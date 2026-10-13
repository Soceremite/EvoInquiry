"""Frozen environment revisions, explicit consumer bindings and conservative leases.

This is a metadata registry, not a package solver or scheduler. Candidate
installation uses existing conda/uv tools in a separate, authorized environment.
No API in this module deletes an environment or expires a lease by time alone.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

try:
    from .registry_common import (RegistryError, atomic_write, digest, file_lock, fixed_ref,
                                  identifier, now, read_record, validate_schema, verify_ref)
    from .state_paths import resolve_state_root, state_writer
except ImportError:
    from registry_common import (RegistryError, atomic_write, digest, file_lock, fixed_ref,
                                 identifier, now, read_record, validate_schema, verify_ref)
    from state_paths import resolve_state_root, state_writer


def _matches(observed, required):
    return all(key in observed and (_matches(observed[key], value) if isinstance(value, dict)
                                   and isinstance(observed[key], dict) else observed[key] == value)
               for key, value in required.items())


def environment_diff(before, after, prefix=''):
    """Report additions, removals and all nested changes, including package sources."""
    result = []
    for key in sorted(set(before) | set(after)):
        path = prefix + key
        old, new = before.get(key), after.get(key)
        if key not in before:
            result.append({'path': path, 'kind': 'added', 'before': None, 'after': new})
        elif key not in after:
            result.append({'path': path, 'kind': 'removed', 'before': old, 'after': None})
        elif isinstance(old, dict) and isinstance(new, dict):
            result.extend(environment_diff(old, new, path + '.'))
        elif old != new:
            result.append({'path': path, 'kind': 'changed', 'before': old, 'after': new})
    return result


def absolute_interpreter(interpreter, *, root=None):
    """Keep the executable's logical entry, including a venv's final symlink."""
    entry = os.fspath(interpreter)
    if not entry:
        raise RegistryError('An interpreter entry is required')
    if not os.path.isabs(entry) and not os.path.dirname(entry):
        entry = shutil.which(entry)
        if entry is None:
            raise RegistryError(f'Interpreter is not on PATH: {interpreter}')
    elif not os.path.isabs(entry):
        entry = os.path.join(root or os.getcwd(), entry)
    return os.path.abspath(entry)


def bound_interpreter(record, root):
    """Pin new entries and recover legacy relative entries from their fixed probe.

    Resolve directory aliases, never the executable's final symlink. A wrapper
    whose entry differs from sys.executable needs an explicit new validation.
    """
    observed = record['observed_fingerprint'].get('interpreter')
    if not isinstance(observed, str) or not os.path.isabs(observed):
        raise RegistryError('Fingerprint must contain an absolute interpreter entry')
    declared = os.fspath(record['interpreter'])
    if not os.path.isabs(declared) and not os.path.dirname(declared):
        names = {os.path.normcase(Path(observed).name)}
        if os.name == 'nt' and Path(observed).suffix.lower() == '.exe':
            names.add(os.path.normcase(Path(observed).stem))
        if os.path.normcase(declared) not in names:
            raise RegistryError('Interpreter entry differs from the validated executable; create a new revision')
        entry = observed  # Do not consult a possibly changed PATH for an old record.
    else:
        entry = absolute_interpreter(declared, root=root)
    def logical(value):
        return os.path.normcase(str(Path(value).parent.resolve() / Path(value).name))
    if logical(entry) != logical(observed):
        raise RegistryError('Interpreter entry differs from the validated executable; create a new revision')
    return os.path.abspath(observed)


def _fingerprint_version(record):
    version = record['observed_fingerprint'].get('fingerprint_version', 1)
    if type(version) is not int or version not in (1, 2):
        raise RegistryError('Unsupported environment fingerprint version')
    return version


def probe_environment(interpreter, imports=(), *, timeout=60, device_probe=False,
                      fingerprint_version=2, diagnostics=None):
    """Run the actual interpreter and requested imports in isolated mode.

    Imported modules may execute their initialization. Request only the imports
    needed by the approved validation. Optional diagnostics receives stdout,
    stderr and the actual exit code, without writing project state. Version 1
    reproduces historical fixed-record fingerprints.
    """
    if type(fingerprint_version) is not int or fingerprint_version not in (1, 2):
        raise RegistryError('Unsupported environment fingerprint version')
    interpreter = absolute_interpreter(interpreter)
    marker = 'EVOINQUIRY_FINGERPRINT_' + secrets.token_hex(16) + ':'
    program = r'''
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
import csv, importlib, importlib.machinery, importlib.metadata, io, json, platform, subprocess
version = int(sys.argv[3])
packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
imports = {}
for name in json.loads(sys.argv[1]):
    module = importlib.import_module(name)
    imports[name] = {'path': getattr(module, '__file__', None), 'version': str(getattr(module, '__version__', 'unknown'))}
    if version == 2:
        spec = getattr(module, '__spec__', None)
        origin = getattr(spec, 'origin', None)
        locations = getattr(spec, 'submodule_search_locations', None)
        kind = ('builtin' if origin == 'built-in' else 'frozen' if origin == 'frozen'
                else 'namespace' if origin is None and locations is not None
                else 'extension' if isinstance(getattr(spec, 'loader', None), importlib.machinery.ExtensionFileLoader)
                else 'file' if origin is not None else 'unknown')
        imports[name].update(kind=kind, origin=origin,
                             search_locations=list(locations) if locations is not None else None)
fingerprint = {'interpreter': sys.executable, 'python': platform.python_version(),
               'platform': platform.platform(), 'host': platform.node(),
               'packages': packages, 'imports': imports}
if version == 2:
    fingerprint.update(fingerprint_version=2, prefix=sys.prefix, base_prefix=sys.base_prefix)
if json.loads(sys.argv[2]):
    torch = importlib.import_module('torch')
    accelerator = {'kind': 'torch', 'cuda_runtime': torch.version.cuda,
                   'cudnn': torch.backends.cudnn.version(), 'cuda_available': torch.cuda.is_available()}
    try:
        query = subprocess.run(['nvidia-smi', '--query-gpu=name,uuid,driver_version,memory.total',
                                '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=15)
        accelerator['driver_probe_exit_code'] = query.returncode
        accelerator['physical_devices'] = list(csv.reader(io.StringIO(query.stdout))) if query.returncode == 0 else []
        accelerator['driver_probe_error'] = query.stderr.strip() if query.returncode else None
    except (OSError, subprocess.TimeoutExpired) as error:
        accelerator.update(driver_probe_exit_code=127, physical_devices=[], driver_probe_error=str(error))
    fingerprint['accelerator'] = accelerator
print('\n' + sys.argv[4] + json.dumps(fingerprint, sort_keys=True, ensure_ascii=True), flush=True)
'''
    command = [interpreter, '-I', '-B', '-c', program, json.dumps(list(imports)),
               json.dumps(device_probe), str(fingerprint_version), marker]
    try:
        completed = subprocess.run(command, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        if diagnostics is not None:
            diagnostics.update(stdout=(getattr(error, 'stdout', None) or b'').decode('utf-8', errors='replace'),
                               stderr=(getattr(error, 'stderr', None) or b'').decode('utf-8', errors='replace'),
                               exit_code=None, error=str(error))
        raise RegistryError('Environment probe could not complete: ' + str(error)) from error
    stdout = completed.stdout.decode('utf-8', errors='replace')
    stderr = completed.stderr.decode('utf-8', errors='replace')
    frames = [line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
    if diagnostics is not None:
        diagnostics.update(stdout='\n'.join(line for line in stdout.splitlines() if not line.startswith(marker)),
                           stderr=stderr, exit_code=completed.returncode)
    if completed.returncode:
        raise RegistryError(f'Environment import probe failed (exit {completed.returncode}): ' + (stderr or stdout)[-3000:])
    if len(frames) != 1:
        raise RegistryError('Environment probe output was not one framed fingerprint')
    try:
        fingerprint = json.loads(frames[0])
    except json.JSONDecodeError:
        raise RegistryError('Environment probe output was not a fingerprint') from None
    if (not isinstance(fingerprint, dict)
            or any(not isinstance(fingerprint.get(key), str) or not fingerprint[key]
                   for key in ('interpreter', 'python', 'platform', 'host'))
            or not os.path.isabs(fingerprint['interpreter'])
            or any(not isinstance(fingerprint.get(key), dict) for key in ('packages', 'imports'))
            or (fingerprint_version == 2 and (fingerprint.get('fingerprint_version') != 2
                or any(not isinstance(fingerprint.get(key), str) or not fingerprint[key]
                       for key in ('prefix', 'base_prefix'))))):
        raise RegistryError('Environment probe returned an invalid fingerprint')
    return fingerprint


def verify_environment(root, reference):
    """Detect actual environment drift before a formal launch; never repair in place."""
    record = validate_schema('environment', read_record(verify_ref(root, reference)))
    if record['lifecycle'] != 'frozen':
        raise RegistryError('Formal execution requires a validated frozen environment revision')
    for key in ('recipe_ref', 'lock_ref', 'build_ref'):
        verify_ref(root, record[key])
    observed = probe_environment(bound_interpreter(record, root), record['observed_fingerprint'].get('imports', {}),
                                 device_probe='accelerator' in record['observed_fingerprint'],
                                 fingerprint_version=_fingerprint_version(record))
    if observed != record['observed_fingerprint']:
        raise RegistryError('Actual environment fingerprint changed; create an independent candidate')
    return observed


def run_environment_check(root, interpreter, check_id, stage, arguments, observed_fingerprint, consumer_ids=()):
    """Run one authorized interpreter check and preserve command, actual exit and output."""
    if stage not in ('metadata', 'imports', 'numerical', 'consumers'):
        raise RegistryError('Unknown environment validation layer')
    try:
        completed = subprocess.run([str(interpreter), *map(str, arguments)],
                                   capture_output=True, timeout=60)
    except subprocess.TimeoutExpired as error:
        completed = subprocess.CompletedProcess(error.cmd, -9, error.stdout or b'',
                                                (error.stderr or b'') + b'\nValidation timed out\n')
    directory = Path(root).resolve() / 'env' / 'receipts'
    output = directory / (identifier(check_id) + '.log')
    receipt_path = directory / (check_id + '.json')
    receipt = {'stage': stage, 'command': [str(interpreter), *map(str, arguments)],
               'exit_code': completed.returncode,
               'observed_fingerprint_sha256': digest(observed_fingerprint),
               'consumer_ids': list(consumer_ids), 'recorded_at': now()}
    with state_writer(root) as state, file_lock(state / 'locks/environments.lock'):
        if receipt_path.exists() or output.exists():
            raise RegistryError('Validation check ID already exists; use a fresh attempt ID')
        atomic_write(output, completed.stdout + completed.stderr)
        receipt['output_ref'] = fixed_ref(root, output.relative_to(Path(root).resolve()))
        receipt['output_sha256'] = receipt['output_ref']['sha256']
        atomic_write(receipt_path, receipt)
    return fixed_ref(root, receipt_path.relative_to(Path(root).resolve()))


class EnvironmentRegistry:
    """Project-local bindings; cross-project physical sharing needs an owner registry."""
    def __init__(self, root):
        self.root = Path(root).resolve()

    @property
    def state(self):
        return resolve_state_root(self.root, 'read')

    def find_compatible(self, requirements):
        """Find frozen records matching exact requested constraints; unknowns do not match."""
        matches = []
        for path in sorted(self.state.glob('environments/*/*/record.json')):
            record = validate_schema('environment', read_record(path))
            if record['lifecycle'] == 'frozen' and _matches(record['observed_fingerprint'], requirements):
                matches.append(fixed_ref(self.root, path.relative_to(self.root)))
        return matches

    def _receipts_pass(self, record, receipts, required_consumers=()):
        stages, tested_consumers = set(), set()
        for reference in receipts:
            receipt = read_record(verify_ref(self.root, reference))
            if (receipt.get('exit_code') != 0 or not receipt.get('command')
                    or not receipt.get('output_sha256') or not receipt.get('observed_fingerprint_sha256')
                    or receipt['observed_fingerprint_sha256'] != digest(record['observed_fingerprint'])):
                return False
            if not receipt.get('output_ref') or receipt['output_ref'].get('sha256') != receipt['output_sha256']:
                return False
            verify_ref(self.root, receipt['output_ref'])
            stages.add(receipt.get('stage'))
            if receipt.get('stage') == 'consumers':
                consumers = receipt.get('consumer_ids', [])
                if not isinstance(consumers, list) or any(not isinstance(item, str) or not item for item in consumers):
                    return False
                tested_consumers.update(consumers)
        return {'metadata', 'imports', 'numerical', 'consumers'} <= stages and set(required_consumers) <= tested_consumers

    def record_candidate(self, record, diff, receipts, required_consumers=()):
        """Persist an independent candidate and failed receipts without touching a frozen instance."""
        record = dict(record, diff=list(diff), test_receipts=list(receipts), lifecycle='candidate')
        validate_schema('environment', record)
        _fingerprint_version(record)
        identifier(record['env_id'])
        identifier(record['revision'])
        record['interpreter'] = bound_interpreter(record, self.root)
        for key in ('recipe_ref', 'lock_ref', 'build_ref'):
            verify_ref(self.root, record[key])
        if (not _matches(record['observed_fingerprint'], record['expected_fingerprint'])
                or not self._receipts_pass(record, receipts, required_consumers)):
            record['lifecycle'] = 'rejected'
        with state_writer(self.root) as state, file_lock(state / 'locks/environments.lock'):
            path = state / 'environment-candidates' / record['env_id'] / record['revision'] / 'record.json'
            if path.exists() and read_record(path) != record:
                raise RegistryError('Candidate revision already exists with different content')
            if not path.exists():
                atomic_write(path, record)
            return fixed_ref(self.root, path.relative_to(self.root))

    def promote_candidate(self, reference, approval, required_consumers=()):
        """Publish a new frozen revision after candidate-bound approval and all receipt layers."""
        record = validate_schema('environment', read_record(verify_ref(self.root, reference)))
        if record['lifecycle'] != 'candidate' or not self._receipts_pass(record, record['test_receipts'], required_consumers):
            raise RegistryError('Candidate validation failed or does not cover required consumers')
        if not (approval.get('approved') is True and approval.get('candidate_ref') == reference
                and approval.get('confirmed_by') and approval.get('confirmed_at')):
            raise RegistryError('Promotion requires approval bound to the candidate revision')
        observed = probe_environment(bound_interpreter(record, self.root), record['observed_fingerprint'].get('imports', {}),
                                     device_probe='accelerator' in record['observed_fingerprint'],
                                     fingerprint_version=_fingerprint_version(record))
        if observed != record['observed_fingerprint']:
            raise RegistryError('Candidate interpreter changed after validation; validate a new revision')
        frozen = dict(record, lifecycle='frozen')
        with state_writer(self.root) as state, file_lock(state / 'locks/environments.lock'):
            path = state / 'environments' / frozen['env_id'] / frozen['revision'] / 'record.json'
            for key in ('recipe_ref', 'lock_ref', 'build_ref'):
                original = verify_ref(self.root, frozen[key])
                payload = original.read_bytes()
                if digest(payload) != frozen[key]['sha256']:
                    raise RegistryError('Environment input changed while freezing the candidate')
                copied = path.parent / 'inputs' / (key + original.suffix)
                if copied.exists() and copied.read_bytes() != payload:
                    raise RegistryError('Frozen environment input cannot be overwritten')
                if not copied.exists():
                    atomic_write(copied, payload)
                frozen[key] = fixed_ref(self.root, copied.relative_to(self.root))
            if path.exists() and read_record(path) != frozen:
                raise RegistryError('Frozen environment revisions cannot be overwritten')
            if not path.exists():
                atomic_write(path, frozen)
            return fixed_ref(self.root, path.relative_to(self.root))

    def _pending_pin_releases(self, state, consumer_id, permitted=None):
        for path in (state / 'pin-releases').glob('*.json'):
            receipt = read_record(path)
            if (receipt['plan']['consumer_id'] == consumer_id and receipt.get('status') == 'prepared'
                    and receipt['plan']['plan_sha256'] != permitted):
                raise RegistryError('Unfinished pin release must be reconciled before changing this consumer')

    def _save_consumer(self, state, record, *, release_plan=None):
        """Publish immutable consumer revisions and update the mutable lookup separately.

        Caller holds the environment lock. Returned references always address
        history, so lease attachment and later lifecycle changes cannot invalidate
        a previously issued binding receipt.
        """
        self._pending_pin_releases(state, record['consumer_id'], release_plan)
        path = state / 'consumers' / (record['consumer_id'] + '.json')
        if path.exists():
            previous = read_record(path)
            if previous['consumer_id'] != record['consumer_id']:
                raise RegistryError('Consumer ID collides with an existing filesystem entry')
            atomic_write(state / 'consumer-history' / record['consumer_id'] / (digest(previous) + '.json'), previous)
        historical = state / 'consumer-history' / record['consumer_id'] / (digest(record) + '.json')
        if historical.exists() and read_record(historical) != record:
            raise RegistryError('Consumer history identity has conflicting content')
        if not historical.exists():
            atomic_write(historical, record)
        atomic_write(path, record)
        return fixed_ref(self.root, historical.relative_to(self.root))

    def bind_consumer(self, record):
        """Bind a selected task, preserving busy bindings, pins and all prior consumer records."""
        validate_schema('consumer', record)
        identifier(record['consumer_id'])
        environment = validate_schema('environment', read_record(verify_ref(self.root, record['env_revision'])))
        if environment['lifecycle'] != 'frozen':
            raise RegistryError('Consumer binding requires a validated frozen environment')
        if record['lifecycle'] != 'unknown' and not all(record.get(key) for key in ('source', 'confirmed_by', 'confirmed_at')):
            raise RegistryError('Known consumer lifecycle requires explicit provenance')
        for pin in record['pin']:
            verify_ref(self.root, pin['ref'])
        with state_writer(self.root) as state, file_lock(state / 'locks/environments.lock'):
            path = state / 'consumers' / (record['consumer_id'] + '.json')
            if path.exists():
                old = read_record(path)
                if old['lifecycle'] in ('queued', 'running') and old['env_revision'] != record['env_revision']:
                    raise RegistryError('Queued/running consumer cannot be rebound to another environment')
                if old['env_revision'] != record['env_revision']:
                    if old['pin']:
                        raise RegistryError('A pinned historical consumer cannot change environment; create a separate future consumer')
                    if old['lease'] and read_record(state / 'leases' / (old['lease'] + '.json'))['status'] != 'released':
                        raise RegistryError('An active lease protects the original environment binding')
                if any(pin not in record['pin'] for pin in old['pin']):
                    raise RegistryError('Existing reproducibility pins require a separate approved release')
                if old['lease'] and old['lease'] != record['lease']:
                    lease = read_record(state / 'leases' / (old['lease'] + '.json'))
                    if lease['status'] != 'released':
                        raise RegistryError('Active lease cannot be detached from its consumer')
            return self._save_consumer(state, record)

    def plan_pin_release(self, consumer_id, pins, reason):
        """Describe selected historical pin removal, without changing any binding.

        Completion or abandonment never constitutes authorization. The caller
        supplies selected pin objects and a reason; an explicit plan-bound
        approval is required by release_pins.
        """
        consumer_id = identifier(consumer_id)
        current = self.state / 'consumers' / (consumer_id + '.json')
        record = validate_schema('consumer', read_record(current))
        if not reason or not pins or any(pin not in record['pin'] for pin in pins):
            raise RegistryError('Select existing pins and state why reproducibility protection may be released')
        plan = {'operation': 'release-selected-pins', 'consumer_id': consumer_id,
                'binding_sha256': digest(record), 'pins': list(pins), 'reason': reason}
        plan['plan_sha256'] = digest(plan)
        return plan

    def release_pins(self, plan, approval):
        """Release only approved pins, preserving prior bindings and an immutable receipt."""
        if not (approval.get('approved') is True and approval.get('plan_sha256') == plan.get('plan_sha256')
                and approval.get('confirmed_by') and approval.get('confirmed_at')):
            raise RegistryError('Pin release requires plan-bound authorization')
        with state_writer(self.root) as state, file_lock(state / 'locks/environments.lock'):
            receipt_path = state / 'pin-releases' / (plan['plan_sha256'] + '.json')
            if receipt_path.exists():
                receipt = read_record(receipt_path)
                if receipt['plan'] != plan:
                    raise RegistryError('Pin release transaction has conflicting content')
                if receipt.get('status') == 'complete':
                    verify_ref(self.root, receipt['binding_ref'])
                    return receipt
            else:
                if self.plan_pin_release(plan['consumer_id'], plan['pins'], plan['reason']) != plan:
                    raise RegistryError('Binding or pin-release plan changed')
                before = read_record(state / 'consumers' / (plan['consumer_id'] + '.json'))
                after = dict(before, pin=[pin for pin in before['pin'] if pin not in plan['pins']])
                receipt = {'plan': plan, 'approval': approval, 'before': before, 'after': after,
                           'status': 'prepared', 'created_at': now(), 'deletion_authorized': False}
                # The approved intent must be durable before changing protection.
                atomic_write(receipt_path, receipt)
            path = state / 'consumers' / (plan['consumer_id'] + '.json')
            record = read_record(path)
            if record not in (receipt['before'], receipt['after']):
                raise RegistryError('Interrupted pin release has a competing consumer change; reconcile explicitly')
            reference = self._save_consumer(state, receipt['after'], release_plan=plan['plan_sha256'])
            receipt.update(status='complete', binding_ref=reference, released_at=now())
            atomic_write(receipt_path, receipt)
            return receipt

    def acquire_lease(self, consumer_id, lease_id, job_ref, *, status='queued', expires_at):
        """Protect a queued/running binding; expiration is a reconciliation signal only."""
        with state_writer(self.root) as state, file_lock(state / 'locks/environments.lock'):
            consumer_path = state / 'consumers' / (identifier(consumer_id) + '.json')
            consumer = validate_schema('consumer', read_record(consumer_path))
            self._pending_pin_releases(state, consumer_id)
            if consumer['job_ref'] != job_ref or consumer['lifecycle'] not in ('queued', 'running'):
                raise RegistryError('Lease must address its actual queued/running consumer job')
            record = {'schema_version': 1, 'lease_id': identifier(lease_id), 'consumer_id': consumer_id,
                      'env_revision': consumer['env_revision'], 'job_ref': job_ref,
                      'status': status, 'heartbeat_at': now(), 'expires_at': expires_at,
                      'termination_receipt': None}
            validate_schema('lease', record)
            if datetime.fromisoformat(expires_at).tzinfo is None:
                raise RegistryError('Lease expiration must include a timezone')
            path = state / 'leases' / (lease_id + '.json')
            if path.exists():
                old = read_record(path)
                if any(old[key] != record[key] for key in ('consumer_id', 'env_revision', 'job_ref', 'status', 'expires_at')):
                    raise RegistryError('Lease ID already belongs to another binding')
                if consumer['lease'] != lease_id:
                    consumer['lease'] = lease_id
                    self._save_consumer(state, consumer)
                return old
            if consumer['lease'] and consumer['lease'] != lease_id:
                raise RegistryError('Consumer already has another lease')
            for other_path in state.glob('leases/*.json'):
                other = read_record(other_path)
                if other['job_ref'] == job_ref and other['status'] != 'released' and other['consumer_id'] != consumer_id:
                    raise RegistryError('Active job reference already belongs to another consumer')
            atomic_write(path, record)
            consumer['lease'] = lease_id
            self._save_consumer(state, consumer)
            return record

    def reconcile_leases(self, observations):
        """Release only jobs independently confirmed terminal by fixed queue/process receipts."""
        results = []
        with state_writer(self.root) as state, file_lock(state / 'locks/environments.lock'):
            for path in sorted(state.glob('leases/*.json')):
                lease = validate_schema('lease', read_record(path))
                if lease['status'] == 'released':
                    continue
                receipt_ref = observations.get(lease['job_ref'])
                if receipt_ref:
                    receipt = read_record(verify_ref(self.root, receipt_ref))
                    consumer = read_record(state / 'consumers' / (lease['consumer_id'] + '.json'))
                    if (receipt.get('job_ref') == lease['job_ref'] and receipt.get('confirmed_at')
                            and receipt.get('source') and receipt.get('status') in ('completed', 'failed', 'cancelled')
                            and receipt.get('process_alive') is False and receipt.get('queued') is False
                            and (not consumer.get('execution_run_id') or receipt.get('execution_run_id') == consumer['execution_run_id'])
                            and receipt.get('lease_id', lease['lease_id']) == lease['lease_id']
                            and receipt.get('consumer_id', lease['consumer_id']) == lease['consumer_id']):
                        lease['status'] = 'released'
                        lease['termination_receipt'] = receipt_ref
                        atomic_write(path, lease)
                        results.append({'lease_id': lease['lease_id'], 'status': 'released'})
                        continue
                results.append({'lease_id': lease['lease_id'], 'status': 'protected-needs-reconciliation',
                                'expired': datetime.fromisoformat(lease['expires_at']) < datetime.now(timezone.utc)})
        return results

    def plan_retirement(self, reference, *, inventory_ref=None):
        """Return blockers and a deletion-free plan; unknown consumers and pins stay protected."""
        environment = validate_schema('environment', read_record(verify_ref(self.root, reference)))
        blockers = []
        for path in (self.state / 'pin-releases').glob('*.json'):
            receipt = read_record(path)
            if receipt.get('status') == 'prepared' and receipt['before']['env_revision'] == reference:
                blockers.append('unfinished-pin-release:' + receipt['plan']['consumer_id'])
        for path in self.state.glob('consumers/*.json'):
            consumer = validate_schema('consumer', read_record(path))
            if consumer['env_revision'] != reference:
                continue
            if consumer['lifecycle'] not in ('completed', 'abandoned'):
                blockers.append('consumer:' + consumer['consumer_id'] + ':' + consumer['lifecycle'])
            if consumer['importance'] == 'unknown' or not all(consumer.get(key) for key in ('source', 'confirmed_by', 'confirmed_at')):
                blockers.append('unknown-consumer-provenance:' + consumer['consumer_id'])
            if consumer['pin']:
                blockers.append('reproducibility-pin:' + consumer['consumer_id'])
        for path in self.state.glob('leases/*.json'):
            lease = validate_schema('lease', read_record(path))
            if lease['env_revision'] == reference and lease['status'] != 'released':
                blockers.append('lease:' + lease['lease_id'])
        if not inventory_ref:
            blockers.append('consumer-inventory-not-confirmed')
        else:
            receipt = read_record(verify_ref(self.root, inventory_ref))
            if (receipt.get('env_revision') != reference or receipt.get('complete') is not True
                    or not receipt.get('confirmed_by') or not receipt.get('confirmed_at') or not receipt.get('source')):
                blockers.append('consumer-inventory-not-confirmed')
        return {'env_id': environment['env_id'], 'revision': environment['revision'],
                'env_revision': reference, 'status': 'BLOCKED' if blockers else 'READY-FOR-AUTHORIZATION',
                'blockers': blockers, 'deletion_authorized': False,
                'retained': ['recipe', 'lock', 'build', 'test receipts', 'historical bindings', 'retirement receipt']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    sub = parser.add_subparsers(dest='command', required=True)
    probe = sub.add_parser('inspect')
    probe.add_argument('--interpreter', default=sys.executable)
    probe.add_argument('--imports', nargs='*', default=[])
    probe.add_argument('--device-probe', action='store_true', help='Authorized PyTorch/CUDA/driver inspection')
    probe.add_argument('--diagnostics', action='store_true', help='Include captured import stdout/stderr and exit code')
    find = sub.add_parser('find')
    find.add_argument('--requirements', required=True)
    candidate = sub.add_parser('record-candidate')
    candidate.add_argument('--record', required=True)
    candidate.add_argument('--required-consumers', nargs='*', default=[])
    promote = sub.add_parser('promote')
    promote.add_argument('--ref', required=True)
    promote.add_argument('--approval', required=True)
    promote.add_argument('--required-consumers', nargs='*', default=[])
    bind = sub.add_parser('bind')
    bind.add_argument('--record', required=True)
    acquire = sub.add_parser('acquire-lease')
    acquire.add_argument('--consumer-id', required=True)
    acquire.add_argument('--lease-id', required=True)
    acquire.add_argument('--job-ref', required=True)
    acquire.add_argument('--expires-at', required=True)
    acquire.add_argument('--status', choices=['queued', 'running'], default='queued')
    reconcile = sub.add_parser('reconcile-leases')
    reconcile.add_argument('--observations', required=True)
    release_plan = sub.add_parser('plan-pin-release')
    release_plan.add_argument('--request', required=True)
    release = sub.add_parser('release-pins')
    release.add_argument('--plan', required=True)
    release.add_argument('--approval', required=True)
    retire = sub.add_parser('retire-plan')
    retire.add_argument('--ref', required=True)
    retire.add_argument('--inventory-ref')
    args = parser.parse_args()
    registry = EnvironmentRegistry(args.root)
    try:
        if args.command == 'inspect':
            diagnostics = {} if args.diagnostics else None
            result = probe_environment(args.interpreter, args.imports, device_probe=args.device_probe,
                                       diagnostics=diagnostics)
            if args.diagnostics:
                result = {'fingerprint': result, 'probe_diagnostics': diagnostics}
        elif args.command == 'find':
            result = registry.find_compatible(read_record(args.requirements))
        elif args.command == 'record-candidate':
            record = read_record(args.record)
            result = registry.record_candidate(record, record.get('diff', []), record['test_receipts'],
                                               args.required_consumers)
        elif args.command == 'promote':
            result = registry.promote_candidate(read_record(args.ref), read_record(args.approval),
                                                args.required_consumers)
        elif args.command == 'bind':
            result = registry.bind_consumer(read_record(args.record))
        elif args.command == 'acquire-lease':
            result = registry.acquire_lease(args.consumer_id, args.lease_id, args.job_ref,
                                            status=args.status, expires_at=args.expires_at)
        elif args.command == 'reconcile-leases':
            result = registry.reconcile_leases(read_record(args.observations))
        elif args.command == 'plan-pin-release':
            request = read_record(args.request)
            result = registry.plan_pin_release(request['consumer_id'], request['pins'], request['reason'])
        elif args.command == 'release-pins':
            result = registry.release_pins(read_record(args.plan), read_record(args.approval))
        else:
            result = registry.plan_retirement(read_record(args.ref), inventory_ref=(
                read_record(args.inventory_ref) if args.inventory_ref else None))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (RegistryError, OSError, subprocess.SubprocessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
