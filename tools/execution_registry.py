"""Frozen experiment specifications, source snapshots and distinct execution attempts.

The existing workflow/queue remains the coordinator. These APIs bind its jobs
to evidence, preserve failures and record real local process exit codes.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time

try:
    from .registry_common import (RegistryError, configure_utf8_output, atomic_write, canonical, digest, file_lock,
                                  fixed_ref, identifier, local_path, now, read_record,
                                  validate_schema, verify_ref)
    from .state_paths import resolve_state_root, state_writer
    from .environment_registry import verify_environment
    from .resource_budget import check_launch as check_session_resources
    from .resource_budget import table_path as session_resource_table
    from .resource_budget import ResourceAdmissionError
    from .resource_budget import check_duration as check_training_duration
    from .run_state import coordination_guard
except ImportError:
    from registry_common import (RegistryError, configure_utf8_output, atomic_write, canonical, digest, file_lock,
                                 fixed_ref, identifier, local_path, now, read_record,
                                 validate_schema, verify_ref)
    from state_paths import resolve_state_root, state_writer
    from environment_registry import verify_environment
    from resource_budget import check_launch as check_session_resources
    from resource_budget import table_path as session_resource_table
    from resource_budget import ResourceAdmissionError
    from resource_budget import check_duration as check_training_duration
    from run_state import coordination_guard


class DispatchDeferred(RegistryError):
    """A prepared attempt awaiting workflow coordination, not a failed run."""

    def __init__(self, result):
        self.result = result
        super().__init__(f"Workflow dispatch {result['status']}: {result['reason']}")


def check_execution_dispatch(root, record, *, require_bound=False):
    """Check the original coordinator; preserve a structured queue deferral.

    The final caller must hold coordination_guard through Popen. Earlier queue
    checks are advisory and never replace that serialized dispatch decision.
    """
    directive = _workflow_directive(root, record)
    status, reason = 'AUTO_APPROVED', 'Workflow permits dispatch'
    if directive is None and require_bound:
        status, reason = 'CONTROL_UNAVAILABLE', 'Bound workflow control disappeared'
    elif directive is not None:
        if directive['stopped']:
            status, reason = 'WORKFLOW_STOPPED', 'Bound workflow already stopped: ' + directive['stopped']['reason']
        elif directive['reflection_gate'] or directive['reflection_due']:
            status, reason = 'WAIT_REVIEW', 'Reflection required before launch'
        elif (directive['timing']['dispatch_seconds_remaining'] is not None
              and directive['timing']['dispatch_seconds_remaining'] <= 0):
            status, reason = 'DISPATCH_BUDGET_EXHAUSTED', 'Original workflow dispatch budget exhausted before launch'
    if record.get('workflow_run_id'):
        with state_writer(root):
            atomic_write(local_path(root, f"runs/{record['execution_run_id']}/dispatch-admission.json"), {
                'execution_run_id': record['execution_run_id'], 'snapshot_ref': record['snapshot_ref'],
                'check': {'status': status, 'reason': reason, 'checked_at': now()}})
    if status != 'AUTO_APPROVED':
        raise DispatchDeferred({'status': status, 'reason': reason})
    return directive


def _dispatch_process(root, directory, record, observed, command, log, environment, *, require_bound):
    """Linearize control validation, state transition and creation of one child."""
    guard = coordination_guard(str(root), record['workflow_run_id']) if record.get('workflow_run_id') else nullcontext()
    with guard, state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        current = read_record(directory / 'execution.json')
        if current['status'] != 'prepared':
            raise RegistryError('Another writer already launched this execution')
        directive = check_execution_dispatch(root, record, require_bound=require_bound)
        record.update(status='running', observed_fingerprint=observed, updated_at=now())
        atomic_write(directory / 'execution.json', record)
        process = subprocess.Popen(command, cwd=directory / 'snapshot', stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=os.name == 'posix', env=environment)
        return process, directive


def spec_digest(spec):
    """Hash every spec field except its self-referential digest."""
    return digest({key: value for key, value in spec.items() if key != 'spec_sha256'})


def register_spec(root, spec):
    """Freeze a spec revision; changes to hypothesis, protocol, seeds or policy need a new one."""
    validate_schema('experiment', spec)
    if spec['spec_sha256'] != spec_digest(spec):
        raise RegistryError('Experiment spec digest differs from its expanded contents')
    ids = [variant['variant_id'] for variant in spec['variants']]
    if len(set(ids)) != len(ids):
        raise RegistryError('Variant identities must be unique')
    for key in ('protocol_ref', 'data_ref', 'split_ref', 'evaluator_ref'):
        verify_ref(root, spec[key])
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        path = local_path(root, f"experiments/{spec['experiment_id']}/history/{spec['spec_revision']}/spec.json")
        if path.exists() and read_record(path) != spec:
            raise RegistryError('Spec revisions are immutable; publish a new revision')
        if not path.exists():
            atomic_write(path, spec)
        return fixed_ref(root, path.relative_to(Path(root).resolve()))


def _reject_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in ('api_key', 'password', 'access_token', 'secret', 'credentials', 'auth_token'):
                raise RegistryError('Credentials cannot enter an execution snapshot')
            _reject_secrets(item)
    elif isinstance(value, list):
        for item in value:
            _reject_secrets(item)


def freeze_snapshot(root, execution_run_id, spec_ref, env_revision, source_paths, configuration,
                    entrypoint, variant_id, seed, *, arguments=None, output_argument_indices=()):
    """Copy an explicit source allowlist and expanded configuration, excluding credentials.

    Data/split/evaluator identities stay fixed through spec_ref. Large datasets
    are represented by their manifests, rather than silently copied wholesale.
    """
    root = Path(root).resolve()
    execution_run_id = identifier(execution_run_id)
    spec = read_record(verify_ref(root, spec_ref))
    validate_schema('experiment', spec)
    if spec['spec_sha256'] != spec_digest(spec):
        raise RegistryError('Spec content hash is invalid')
    variant = next((item for item in spec['variants'] if item['variant_id'] == variant_id), None)
    if variant is None or seed not in spec['seeds']:
        raise RegistryError('Execution does not belong to a declared variant/seed slot')
    if configuration.get('variant') != variant['configuration'] or configuration.get('seed') != seed:
        raise RegistryError('Expanded configuration differs from the frozen variant/seed')
    _reject_secrets(configuration)
    verify_ref(root, env_revision)
    sources = sorted(set(Path(path).as_posix() for path in source_paths))
    if entrypoint not in sources:
        raise RegistryError('Entrypoint must be in the explicit source allowlist')
    content = {}
    for relative in sources:
        parts = Path(relative).parts
        if (parts[0] in ('.git', '.ei', '.aris', '.aws', '.codex', '.env')
                or Path(relative).name.startswith('.env')
                or Path(relative).name in ('auth.json', 'credentials', 'credentials.json')):
            raise RegistryError('Private/runtime state cannot enter a source snapshot')
        content[relative] = local_path(root, relative).read_bytes()
    manifest = {'schema_version': 1, 'execution_run_id': execution_run_id, 'spec_ref': spec_ref,
                'env_revision': env_revision, 'variant_id': variant_id, 'seed': seed,
                'entrypoint': entrypoint, 'source_files': {path: digest(data) for path, data in content.items()},
                'configuration_sha256': digest(canonical(configuration) + b'\n')}
    if arguments is not None:
        if not isinstance(arguments, (list, tuple)) or any(not isinstance(arg, str) for arg in arguments):
            raise RegistryError('Frozen launch arguments must be an explicit string array')
        private_flags = {'--api-key','--api_key','--password','--token','--access-token','--secret'}
        if any(arg.split('=', 1)[0].lower() in private_flags for arg in arguments):
            raise RegistryError('Credentials cannot enter frozen launch arguments')
        manifest['arguments'] = list(arguments)
        indices = list(output_argument_indices)
        if (len(set(indices)) != len(indices) or any(type(i) is not int or not 0 <= i < len(arguments) for i in indices)):
            raise RegistryError('Declare unique output argument indices within the frozen argument array')
        for index in indices:
            output = Path(arguments[index])
            if not output.is_absolute():
                output = root / output
            if not output.resolve().is_relative_to(root / 'runs' / execution_run_id):
                raise RegistryError('Output argument must stay within its own execution directory')
        manifest['output_argument_indices'] = indices
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        snapshot = local_path(root, f'runs/{execution_run_id}/snapshot')
        target = snapshot / 'manifest.json'
        if target.exists():
            if read_record(target) != manifest:
                raise RegistryError('Execution snapshot cannot be replaced')
        else:
            if snapshot.exists():
                raise RegistryError('Incomplete snapshot exists; inspect it before reusing an execution ID')
            for relative, data in content.items():
                atomic_write(local_path(snapshot, relative), data)
            atomic_write(snapshot / 'configuration.json', configuration)
            atomic_write(target, manifest)
        reference = fixed_ref(root, target.relative_to(root))
        verify_snapshot(root, reference)
        return reference


def verify_snapshot(root, reference):
    """Verify frozen files, expanded config and all upstream evidence identities."""
    path = verify_ref(root, reference)
    manifest = read_record(path)
    if manifest.get('schema_version') != 1 or not manifest.get('source_files'):
        raise RegistryError('Invalid or empty execution snapshot')
    directory = path.parent
    actual_files = {p.relative_to(directory).as_posix() for p in directory.rglob('*')
                    if p.is_file() or p.is_symlink()}
    if actual_files != set(manifest['source_files']) | {'manifest.json', 'configuration.json'}:
        raise RegistryError('Frozen snapshot contains missing or unapproved source files')
    for relative, expected in manifest['source_files'].items():
        target = local_path(directory, relative)
        if digest(target.read_bytes()) != expected:
            raise RegistryError('Frozen source changed: ' + relative)
    if digest((directory / 'configuration.json').read_bytes()) != manifest['configuration_sha256']:
        raise RegistryError('Frozen expanded configuration changed')
    spec = read_record(verify_ref(root, manifest['spec_ref']))
    if spec_digest(spec) != spec['spec_sha256']:
        raise RegistryError('Frozen spec self-digest differs')
    for key in ('protocol_ref', 'data_ref', 'split_ref', 'evaluator_ref'):
        verify_ref(root, spec[key])
    verify_ref(root, manifest['env_revision'])
    return manifest


def start_execution(root, execution_run_id, snapshot_ref, *, workflow_run_id=None, job_ref=None,
                    retry_of=None, resumed_from=None, checkpoint_ref=None):
    """Allocate one real launch attempt identity; retries and resumes require new IDs."""
    root = Path(root).resolve()
    execution_run_id = identifier(execution_run_id)
    snapshot = verify_snapshot(root, snapshot_ref)
    if snapshot['execution_run_id'] != execution_run_id:
        raise RegistryError('Snapshot belongs to another execution')
    if retry_of and resumed_from:
        raise RegistryError('Use one explicit parent relation per execution')
    if bool(resumed_from) != bool(checkpoint_ref):
        raise RegistryError('Checkpoint recovery requires both resumed_from and a fixed checkpoint reference')
    if checkpoint_ref:
        verify_ref(root, checkpoint_ref)
    for parent_id in filter(None, (retry_of, resumed_from)):
        if parent_id == execution_run_id:
            raise RegistryError('An execution cannot be its own retry/resume parent')
        parent = read_record(local_path(root, f'runs/{identifier(parent_id)}/execution.final.json'))
        if parent['status'] not in ('failed', 'stopped'):
            raise RegistryError('Retry/resume parent must be a recorded failed or stopped attempt')
        if any(parent[key] != snapshot[key] for key in ('spec_ref', 'variant_id', 'seed')):
            raise RegistryError('Retry/resume relation crosses a different experiment slot')
    record = {'schema_version': 1, 'execution_run_id': execution_run_id,
              'workflow_run_id': workflow_run_id, 'spec_ref': snapshot['spec_ref'],
              'variant_id': snapshot['variant_id'], 'seed': snapshot['seed'],
              'snapshot_ref': snapshot_ref, 'env_revision': snapshot['env_revision'],
              'observed_fingerprint': read_record(verify_ref(root, snapshot['env_revision']))['observed_fingerprint'],
              'job_ref': job_ref, 'retry_of': retry_of, 'resumed_from': resumed_from,
              'checkpoint_ref': checkpoint_ref, 'status': 'prepared', 'exit_code': None,
              'created_at': now(), 'transaction_id': 'execution-' + execution_run_id}
    validate_schema('execution', record)
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        path = local_path(root, f'runs/{execution_run_id}/execution.json')
        if path.exists():
            raise RegistryError('Execution ID already exists; every new launch needs a new ID')
        atomic_write(path, record)
    return record


def rebase_execution_output(value, parent_id, execution_run_id):
    """Move one declared output path to a retry, preserving its separator style.

    Accept native or forward Windows separators and glob suffixes. Only an exact
    runs/<parent> component moves; similarly named runs and input arguments stay
    unchanged. Callers must restrict this to declared outputs.
    """
    parent_id, execution_run_id = identifier(parent_id), identifier(execution_run_id)
    pattern = r'(^|[/\\])runs([/\\])' + re.escape(parent_id) + r'(?=[/\\]|$)'
    return re.sub(pattern, lambda match: match[1] + 'runs' + match[2] + execution_run_id,
                  value, count=1)


def clone_attempt(root, parent_id, execution_run_id, *, checkpoint_ref=None):
    """Freeze a retry from the parent's snapshot, never from the current checkout."""
    root = Path(root).resolve()
    parent = read_record(local_path(root, f'runs/{identifier(parent_id)}/execution.final.json'))
    if parent['status'] not in ('failed', 'stopped'):
        raise RegistryError('A retry/resume needs a confirmed terminal parent')
    snapshot = verify_snapshot(root, parent['snapshot_ref'])
    original = verify_ref(root, parent['snapshot_ref']).parent
    execution_run_id = identifier(execution_run_id)
    target = local_path(root, f'runs/{execution_run_id}/snapshot')
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        expected_manifest = dict(snapshot, execution_run_id=execution_run_id)
        if 'arguments' in snapshot:
            retry_arguments = list(snapshot['arguments'])
            for index in snapshot.get('output_argument_indices', []):
                retry_arguments[index] = rebase_execution_output(retry_arguments[index], parent_id, execution_run_id)
            expected_manifest['arguments'] = retry_arguments
        expected_files = {*snapshot['source_files'], 'configuration.json', 'manifest.json'}
        existing_files = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()} if target.exists() else set()
        if existing_files - expected_files:
            raise RegistryError('Retry snapshot contains undeclared content')
        for name in [*snapshot['source_files'], 'configuration.json']:
            source, destination = local_path(original, name), local_path(target, name)
            payload = source.read_bytes()
            if name == 'configuration.json':
                configuration = json.loads(payload)
                for key, field in (('training_clock', 'path'), ('stop_protocol', 'receipt_path')):
                    if configuration.get(key):
                        configuration[key][field] = rebase_execution_output(configuration[key][field], parent_id,
                                                                           execution_run_id)
                payload = canonical(configuration) + b'\n'
                expected_manifest['configuration_sha256'] = digest(payload)
            if destination.exists() and destination.read_bytes() != payload:
                raise RegistryError('Retry snapshot identity has conflicting source content')
            if not destination.exists():
                atomic_write(destination, payload)
        if (target / 'manifest.json').exists() and read_record(target / 'manifest.json') != expected_manifest:
            raise RegistryError('Retry snapshot identity has a different parent/configuration')
        if not (target / 'manifest.json').exists():
            atomic_write(target / 'manifest.json', expected_manifest)
        reference = fixed_ref(root, (target / 'manifest.json').relative_to(root))
    relation = {'resumed_from': parent_id, 'checkpoint_ref': checkpoint_ref} if checkpoint_ref else {'retry_of': parent_id}
    existing = local_path(root, f'runs/{execution_run_id}/execution.json')
    if existing.exists():
        record = validate_schema('execution', read_record(existing))
        if (record['status'] != 'prepared' or record['snapshot_ref'] != reference
                or any(record.get(key) != value for key, value in relation.items())
                or record['job_ref'] != parent['job_ref']):
            raise RegistryError('Retry identity is already launched or belongs to another parent')
        return record
    return start_execution(root, execution_run_id, reference, workflow_run_id=parent['workflow_run_id'],
                           job_ref=parent['job_ref'], **relation)


def inspect_terminal(root, execution_run_id):
    """Validate a terminal attempt and its fixed input/output references.

    Cancellation is independent of exit code: a cooperative trainer can save
    its state and exit zero after an enforced stop without completing its task.
    """
    root = Path(root).resolve()
    path = local_path(root, f'runs/{identifier(execution_run_id)}/execution.final.json')
    record = validate_schema('execution', read_record(path))
    if record['execution_run_id'] != execution_run_id or record['status'] not in ('completed', 'failed', 'stopped'):
        raise RegistryError('Terminal record has a different identity or nonterminal status')
    if ((record['status'] == 'completed' and record['exit_code'] != 0)
            or (record['status'] == 'failed' and record['exit_code'] == 0)):
        raise RegistryError('Terminal status and actual exit code disagree')
    snapshot = verify_snapshot(root, record['snapshot_ref'])
    for key in ('execution_run_id', 'spec_ref', 'env_revision', 'variant_id', 'seed'):
        if record[key] != snapshot[key]:
            raise RegistryError('Terminal execution differs from its fixed snapshot: ' + key)
    for reference in record.get('result_refs', []):
        verify_ref(root, reference)
    return record, fixed_ref(root, path.relative_to(root))


def verify_queue_binding(root, binding):
    """Check prepared snapshot, environment and active consumer lease before scheduling."""
    root = Path(root).resolve()
    record = validate_schema('execution', read_record(local_path(
        root, f"runs/{identifier(binding['execution_run_id'])}/execution.json")))
    for key in ('snapshot_ref', 'env_revision'):
        if record[key] != binding[key]:
            raise RegistryError('Queued binding differs from the prepared execution: ' + key)
    if record['status'] != 'prepared':
        raise RegistryError('Queued execution has already launched; allocate a retry identity')
    snapshot = verify_snapshot(root, record['snapshot_ref'])
    if 'arguments' not in snapshot or snapshot['arguments'] != binding.get('arguments', []):
        raise RegistryError('Governed queue requires arguments fixed in the execution snapshot')
    state = resolve_state_root(root, 'read')
    consumer = validate_schema('consumer', read_record(state / 'consumers' / (identifier(binding['consumer_id']) + '.json')))
    lease = validate_schema('lease', read_record(state / 'leases' / (identifier(binding['lease_id']) + '.json')))
    if (consumer['lease'] != lease['lease_id'] or lease['consumer_id'] != consumer['consumer_id']
            or consumer['env_revision'] != record['env_revision'] or lease['env_revision'] != record['env_revision']
            or lease['job_ref'] != consumer['job_ref'] or record['job_ref'] != lease['job_ref']
            or lease['status'] not in ('queued', 'running') or consumer['lifecycle'] not in ('queued', 'running')):
        raise RegistryError('Queued snapshot/environment lacks its matching active consumer lease')
    return record


def finish_execution(root, execution_run_id, exit_code, result_refs=(), *, stopped=False):
    """Record terminal process status and freeze final metadata without deleting attempts."""
    root = Path(root).resolve()
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        path = local_path(root, f'runs/{identifier(execution_run_id)}/execution.json')
        record = validate_schema('execution', read_record(path))
        if record['status'] != 'running':
            raise RegistryError('Only a running execution can record a terminal process result')
        if not isinstance(exit_code, int):
            raise RegistryError('A terminal process requires its actual integer exit code')
        for reference in result_refs:
            verify_ref(root, reference)
        record.update(status='stopped' if stopped else ('completed' if exit_code == 0 else 'failed'),
                      exit_code=exit_code, result_refs=list(result_refs), updated_at=now())
        final = path.with_name('execution.final.json')
        if final.exists():
            raise RegistryError('Final execution record already exists; inspect interrupted terminal commit')
        atomic_write(final, record)
        atomic_write(path, record)
        return fixed_ref(root, final.relative_to(root))


def reconcile_execution(root, execution_run_id, *, final_ref=None, termination_ref=None):
    """Recover a terminal projection or record independently observed termination.

    A missing heartbeat/screen is never enough. An interrupted final write can
    be replayed from its fixed final_ref. Otherwise a fixed process-observer
    receipt must identify this job/execution, its actual exit and confirmed
    termination; calling this does not launch a replacement process.
    An observer can explicitly set stopped=true for cooperative cancellation,
    independently of exit code. Legacy zero-exit observations retain their
    completed interpretation when no cancellation is recorded.
    """
    root = Path(root).resolve()
    execution_run_id = identifier(execution_run_id)
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        path = local_path(root, f'runs/{execution_run_id}/execution.json')
        current = validate_schema('execution', read_record(path))
        if final_ref:
            final, reference = inspect_terminal(root, execution_run_id)
            if reference != final_ref:
                raise RegistryError('Recovery final reference differs from the terminal record')
            for key in ('execution_run_id', 'spec_ref', 'snapshot_ref', 'env_revision', 'variant_id', 'seed',
                        'job_ref', 'retry_of', 'resumed_from', 'checkpoint_ref'):
                if current[key] != final[key]:
                    raise RegistryError('Interrupted terminal projection has different input identities')
            if current['status'] != 'running' and current != final:
                raise RegistryError('Terminal projection conflicts with the existing execution state')
            atomic_write(path, final)
            return reference
        if not termination_ref or current['status'] != 'running':
            raise RegistryError('Running execution recovery needs a fixed verified termination receipt')
        receipt = read_record(verify_ref(root, termination_ref))
        if (receipt.get('execution_run_id') != execution_run_id or receipt.get('job_ref') != current['job_ref']
                or receipt.get('process_alive') is not False or receipt.get('queued') is not False
                or not receipt.get('confirmed_at') or not receipt.get('source')
                or type(receipt.get('exit_code')) is not int
                or ('stopped' in receipt and type(receipt['stopped']) is not bool)):
            raise RegistryError('Termination receipt does not establish this actual process exit')
        final = dict(current, status='stopped', exit_code=receipt['exit_code'],
                     updated_at=now(), result_refs=[termination_ref])
        if final['exit_code'] == 0 and receipt.get('stopped') is not True:
            final['status'] = 'completed'
        atomic_write(path.with_name('execution.final.json'), final)
        atomic_write(path, final)
        return fixed_ref(root, path.with_name('execution.final.json').relative_to(root))


def _owned_group_alive(process):
    """Observe our process group, excluding Linux zombies awaiting reaping."""
    if os.name != 'posix':
        return process.poll() is None
    if sys.platform.startswith('linux'):
        for path in Path('/proc').glob('[0-9]*/stat'):
            try:
                fields = path.read_text().rsplit(')', 1)[1].split()
                if int(fields[2]) == process.pid and fields[0] != 'Z':
                    return True
            except (OSError, ValueError, IndexError):
                continue
        return False
    try:
        os.killpg(process.pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _stop_owned_process(process, *, force_after_seconds=None):
    """Request termination once; force only under a distinct explicit grant.

    Cooperative saves may take minutes. Keep the original observer and resource
    ownership until actual exit; a five-second wait never authorizes SIGKILL.
    """
    if force_after_seconds is not None:
        force_after_seconds = _positive_timeout(force_after_seconds)
    started, forced = time.monotonic(), False
    try:
        if os.name == 'posix':
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        pass
    while process.poll() is None or _owned_group_alive(process):
        if force_after_seconds is not None and not forced and time.monotonic() - started >= force_after_seconds:
            try:
                if os.name == 'posix':
                    os.killpg(process.pid, signal.SIGKILL)
                elif process.poll() is None:
                    process.kill()
            except ProcessLookupError:
                pass
            forced = True
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            continue
        if _owned_group_alive(process):
            time.sleep(0.2)
    process.wait()
    return {'force_used': forced, 'force_after_seconds': force_after_seconds,
            'process_tree_exited': os.name == 'posix'}


def request_stop_execution(root, execution_run_id, reason, *, confirmed_by=None, force_after_seconds=None):
    """Request cancellation of one running local execution, without sending signals.

    Bind the request to its immutable snapshot and observed local process file.
    confirmed_by must reference an actual user choice for this experiment; a
    review verdict, elapsed reminder or unanswered popup is not confirmation.
    The existing launcher observes it, stops its own process group and freezes
    actual termination evidence. Return a fixed request reference; this is not
    a termination receipt and cannot settle a live reservation. Same-reason
    retries reuse the request; changed reasons/identities are rejected.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise RegistryError('Execution stop needs a reason')
    if not isinstance(confirmed_by, str) or not confirmed_by.strip():
        raise RegistryError('Interrupting an execution requires explicit user confirmation')
    if force_after_seconds is not None:
        force_after_seconds = _positive_timeout(force_after_seconds)
    execution_run_id = identifier(execution_run_id)
    root = Path(root).resolve()
    directory = local_path(root, f'runs/{execution_run_id}')
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        record = validate_schema('execution', read_record(directory / 'execution.json'))
        target = directory / 'stop-request.json'
        if target.exists():
            existing = read_record(target)
            if (existing.get('execution_run_id') != execution_run_id
                    or existing.get('snapshot_ref') != record['snapshot_ref']
                    or existing.get('reason') != reason
                    or existing.get('confirmed_by') != confirmed_by
                    or existing.get('force_after_seconds') != force_after_seconds):
                raise RegistryError('Existing execution stop request is immutable')
            verify_ref(root, existing['process_ref'])
            return fixed_ref(root, target.relative_to(root))
        if record['status'] != 'running':
            raise RegistryError('Only a running execution can receive a stop request')
        process_ref = fixed_ref(root, (directory / 'process.json').relative_to(root))
        process = read_record(verify_ref(root, process_ref))
        if (process.get('execution_run_id') != execution_run_id
                or process.get('host') != platform.node()):
            raise RegistryError('No matching observed local process for this execution')
        atomic_write(target, {'schema_version': 1, 'execution_run_id': execution_run_id,
                             'snapshot_ref': record['snapshot_ref'], 'process_ref': process_ref,
                             'reason': reason, 'requested_at': now(), 'confirmed_by': confirmed_by,
                             'force_after_seconds': force_after_seconds})
        return fixed_ref(root, target.relative_to(root))


def _workflow_directive(root, record):
    if not record.get('workflow_run_id'):
        return None
    try:
        from .research_control import execution_directive
    except ImportError:
        from research_control import execution_directive
    return execution_directive(root, record['workflow_run_id'])


def _positive_timeout(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise RegistryError('Execution timeout must be finite and positive')
    return float(value)


def _stop_authorization(configuration):
    """Read only explicitly authorized automatic stop conditions from frozen inputs."""
    authorization = configuration.get('stop_authorization')
    if authorization is None:
        return {'confirmed_by': None, 'conditions': []}
    if (not isinstance(authorization, dict) or set(authorization) - {
            'confirmed_by', 'conditions', 'force_after_seconds', 'force_on_confirmed_stop'}
            or not {'confirmed_by', 'conditions'} <= set(authorization)
            or not isinstance(authorization['confirmed_by'], str) or not authorization['confirmed_by'].strip()
            or not isinstance(authorization['conditions'], list) or not authorization['conditions']
            or any(condition not in ('timeout', 'workflow_deadline', 'control_error', 'launcher_error')
                   for condition in authorization['conditions'])
            or len(set(authorization['conditions'])) != len(authorization['conditions'])):
        raise RegistryError('Automatic stopping requires a user confirmation reference and explicit conditions')
    if authorization.get('force_after_seconds') is not None:
        _positive_timeout(authorization['force_after_seconds'])
    if 'force_on_confirmed_stop' in authorization and (
            type(authorization['force_on_confirmed_stop']) is not bool
            or authorization.get('force_after_seconds') is None):
        raise RegistryError('Forced confirmed-stop cleanup requires its explicit force interval')
    return authorization


def _stop_notice(directory, record, process, cause, notices):
    """Retain one notice per cause without signaling or repeatedly asking the user."""
    key = (cause['cause'], cause['reason'])
    if key in notices:
        return
    notices.add(key)
    path = directory / 'process-control-notices.json'
    rows = read_record(path)['notices'] if path.exists() else []
    rows.append(dict(cause, execution_run_id=record['execution_run_id'], pid=process.pid,
                     snapshot_ref=record['snapshot_ref'], observed_at=now(),
                     action='await_user_stop_confirmation', process_interrupted=False))
    atomic_write(path, {'schema_version': 1, 'notices': rows})


def _validate_monitor_bindings(root, record, configuration):
    """Bind optional trainer-owned timing/save receipts before any process starts."""
    for key, fields in (('training_clock', {'path', 'experiment_id'}),
                        ('stop_protocol', {'mode', 'receipt_path'})):
        binding = configuration.get(key)
        if binding is None:
            continue
        if not isinstance(binding, dict) or set(binding) != fields:
            raise RegistryError(f'Invalid frozen {key} binding')
        name = binding['path' if key == 'training_clock' else 'receipt_path']
        if not isinstance(name, str) or not name or Path(name).is_absolute() or '\\' in name:
            raise RegistryError(f'{key} receipt must be project-relative')
        target = local_path(root, name)
        if not target.is_relative_to(Path(root) / 'runs' / record['execution_run_id']):
            raise RegistryError(f'{key} receipt must belong to this execution')
        if key == 'training_clock':
            identifier(binding['experiment_id'])
            if not configuration.get('resource_budget'):
                raise RegistryError('Training clock monitoring requires the original session resource binding')
        elif binding['mode'] != 'checkpoint_then_stop' or os.name != 'posix':
            raise RegistryError('checkpoint_then_stop requires a cooperating POSIX SIGTERM handler')


def _observe_training_budget(root, directory, record, configuration):
    """Consume the trainer's first-step clock in the existing execution observer.

    Persist deduplicated notices for the session UI/monitor. Missing receipts
    mean setup has not reported a first step; never substitute process uptime.
    A reminder, invalid clock or exceeded ceiling never sends a signal.
    """
    binding = configuration.get('training_clock')
    if binding is None:
        return
    path = local_path(root, binding['path'])
    if not path.exists():
        return
    try:
        clock = read_record(path)
        if clock.get('segments') and clock['segments'][-1].get('attempt_id') != record['execution_run_id']:
            raise RegistryError('Training clock current attempt differs from this execution')
        resource = configuration['resource_budget']
        result = check_training_duration(resource.get('table_root', root), resource['session_id'],
                                        training_clock=clock, experiment_id=binding['experiment_id'])
    except (RegistryError, OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        result = {'status': 'INVALID_TRAINING_CLOCK', 'reason': str(error),
                  'action': 'repair_clock_continue_observing', 'notice_required': True}
    receipt = directory / 'training-budget-observations.json'
    data = read_record(receipt) if receipt.exists() else {
        'schema_version': 1, 'execution_run_id': record['execution_run_id'],
        'snapshot_ref': record['snapshot_ref'], 'notices': []}
    previous = data.get('latest', {})
    status = result['status']
    key = (status, result.get('policy_revision'))
    if (result.get('notice_required') or status in ('NEEDS_APPROVAL', 'SELECTION_REQUIRED')) and not any(
            (item['status'], item.get('policy_revision')) == key for item in data['notices']):
        data['notices'].append(dict(result, observed_at=now(), process_interrupted=False,
                                   delivery='pending_execution_owner'))
    if (status != previous.get('status') or len(data['notices']) != data.get('notice_count', 0)
            or result.get('training_state') != previous.get('training_state')
            or abs(result.get('seconds', 0) - previous.get('seconds', 0)) >= 1):
        data.update(latest=result, notice_count=len(data['notices']), observed_at=now())
        atomic_write(receipt, data)


def _checkpoint_stop_evidence(root, record, configuration):
    protocol = configuration.get('stop_protocol')
    if protocol is None:
        return {'status': 'not_requested', 'checkpoint_saved': False}
    try:
        reference = fixed_ref(root, protocol['receipt_path'])
        receipt = read_record(verify_ref(root, reference))
        if (receipt.get('execution_run_id') != record['execution_run_id']
                or receipt.get('snapshot_ref') != record['snapshot_ref']
                or receipt.get('validation', {}).get('passed') is not True
                or not receipt['validation'].get('label')):
            raise RegistryError('Checkpoint stop receipt lacks matching identity/loader validation')
        verify_ref(root, receipt['checkpoint_ref'])
        return {'status': 'verified', 'checkpoint_saved': True, 'receipt_ref': reference}
    except (RegistryError, OSError, ValueError, TypeError, KeyError) as error:
        return {'status': 'unverified', 'checkpoint_saved': False, 'reason': str(error)}


def _wait_controlled(root, directory, record, process, timeout, bound_workflow, stop_authorization,
                     configuration=None):
    """Wait for actual exit while observing only this execution's control inputs."""
    started = time.monotonic()
    configuration = configuration or {}
    notices = set()
    while process.poll() is None:
        _observe_training_budget(root, directory, record, configuration)
        causes = []
        try:
            request_path = directory / 'stop-request.json'
            if request_path.exists():
                request = read_record(request_path)
                if (request.get('schema_version') != 1
                        or request.get('execution_run_id') != record['execution_run_id']
                        or request.get('snapshot_ref') != record['snapshot_ref']
                        or request.get('process_ref') != fixed_ref(root, (directory / 'process.json').relative_to(root))
                        or not isinstance(request.get('reason'), str) or not request['reason'].strip()):
                    raise RegistryError('Execution stop request has mismatched identities')
                causes.append({'cause': 'execution_stop', 'reason': request['reason'],
                               'requested_at': request['requested_at'],
                               'confirmed_by': request.get('confirmed_by'),
                               'force_after_seconds': request.get('force_after_seconds'),
                               'request_ref': fixed_ref(root, request_path.relative_to(root))})
        except (RegistryError, OSError, ValueError, TypeError, KeyError) as error:
            causes.append({'cause': 'control_error', 'reason': str(error)})
        if bound_workflow:
            try:
                directive = _workflow_directive(root, record)
                if directive is None:
                    raise RegistryError('Bound workflow control disappeared')
                if directive['stopped']:
                    causes.append({'cause': 'workflow_stop', 'reason': directive['stopped']['reason'],
                                   'requested_at': directive['stopped']['at'],
                                   'confirmed_by': directive['stopped'].get('confirmed_by')})
                if (directive['timing']['dispatch_seconds_remaining'] is not None
                      and directive['timing']['dispatch_seconds_remaining'] <= 0):
                    causes.append({'cause': 'workflow_deadline', 'reason': 'Original dispatch budget exhausted'})
            except (RegistryError, OSError, ValueError, TypeError, KeyError) as error:
                causes.append({'cause': 'control_error', 'reason': str(error)})
        if timeout is not None and time.monotonic() - started >= timeout:
            causes.append({'cause': 'timeout', 'reason': 'Fixed execution time limit reached'})
        for cause in causes:
            confirmed_by = cause.get('confirmed_by')
            if not confirmed_by and cause['cause'] in stop_authorization['conditions']:
                confirmed_by = stop_authorization['confirmed_by']
            if isinstance(confirmed_by, str) and confirmed_by.strip():
                force_after = cause.get('force_after_seconds')
                if force_after is None and (cause['cause'] in stop_authorization['conditions'] or
                        (cause.get('confirmed_by') and stop_authorization.get('force_on_confirmed_stop') is True)):
                    force_after = stop_authorization.get('force_after_seconds')
                atomic_write(directory / 'stop-progress.json', dict(cause, confirmed_by=confirmed_by,
                             action='stop_requested_observing_exit', force_after_seconds=force_after, observed_at=now()))
                stopped = _stop_owned_process(process, force_after_seconds=force_after)
                receipt = dict(cause, schema_version=1, execution_run_id=record['execution_run_id'],
                               workflow_run_id=record.get('workflow_run_id'), snapshot_ref=record['snapshot_ref'],
                               process_ref=fixed_ref(root, (directory / 'process.json').relative_to(root)),
                               pid=process.pid, exit_code=process.returncode, parent_exited=True,
                               confirmed_by=confirmed_by,
                               **stopped,
                               checkpoint_stop=_checkpoint_stop_evidence(root, record, configuration),
                               termination_scope='posix-process-group' if os.name == 'posix' else 'windows-parent-only',
                               observed_at=now())
                atomic_write(directory / 'termination.json', receipt)
                _observe_training_budget(root, directory, record, configuration)
                return process.returncode, True
            _stop_notice(directory, record, process, cause, notices)
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            pass
    _observe_training_budget(root, directory, record, configuration)
    return process.returncode, False


def check_execution_resources(root, record):
    """Reuse one session table at queue admission and after environment validation.

    The per-execution receipt is evidence of this check, not another policy
    table. Deferred checks leave the execution prepared and spend no retry.
    """
    root = Path(root).resolve()
    directory = local_path(root, f"runs/{identifier(record['execution_run_id'])}")
    snapshot_dir = verify_ref(root, record['snapshot_ref']).parent
    binding = read_record(snapshot_dir / 'configuration.json').get('resource_budget')
    if (binding is None and (os.environ.get('CODEX_THREAD_ID') or os.environ.get('CODEX_SESSION_ID'))
            and session_resource_table(root).exists()):
        raise RegistryError('Bind the current session resource table before launching this execution')
    if binding is None:
        return None
    try:
        result = check_session_resources(root, binding)
    except ResourceAdmissionError as error:
        result = error.result
        with state_writer(root):
            atomic_write(directory / 'resource-admission.json', {
                'execution_run_id': record['execution_run_id'], 'snapshot_ref': record['snapshot_ref'],
                'check': result})
        raise
    with state_writer(root):
        atomic_write(directory / 'resource-admission.json', {
            'execution_run_id': record['execution_run_id'], 'snapshot_ref': record['snapshot_ref'],
            'check': result})
    return result


def launch_execution(root, execution_run_id, arguments=(), *, timeout=None):
    """Launch an authorized local CPU/GPU entry from its verified snapshot and interpreter.

    Resource authorization/budgets belong to the calling execution skill. Imports
    of mutable project code are rejected and actual import paths are retained.
    The local wait interrupts only on a user-confirmed stop or a specifically
    preauthorized automatic condition. Unconfirmed review stops, limits and
    control errors produce notices while observation continues. The wall-clock
    timeout is distinct from a training budget beginning at the first step.
    Effective timeout is the minimum of an explicit bound, the spec's
    max_seconds_per_attempt and the configured workflow's original remaining
    dispatch time. Pending/due reflection blocks prepared dispatch, and is
    rechecked after environment verification. It does not interrupt a healthy
    process that was already launched.
    A termination.json receipt records actual exit and its enforcement scope;
    Windows parent termination does not certify a descendant process tree.
    """
    root = Path(root).resolve()
    directory = local_path(root, f'runs/{identifier(execution_run_id)}')
    path = directory / 'execution.json'
    record = validate_schema('execution', read_record(path))
    if record['status'] != 'prepared':
        raise RegistryError('An execution identity can launch only once')
    snapshot = verify_snapshot(root, record['snapshot_ref'])
    if 'arguments' in snapshot and list(arguments) != snapshot['arguments']:
        raise RegistryError('Launch arguments differ from the frozen snapshot')
    bounds = []
    if timeout is not None:
        bounds.append(_positive_timeout(timeout))
    spec_budget = read_record(verify_ref(root, record['spec_ref']))['budget']
    if 'max_seconds_per_attempt' in spec_budget:
        bounds.append(_positive_timeout(spec_budget['max_seconds_per_attempt']))
    directive = check_execution_dispatch(root, record)
    try:
        from .project_registry import discover_project
    except ImportError:
        from project_registry import discover_project
    if discover_project(root)['layout_profile'] == 'governed-v1' and 'arguments' not in snapshot:
        raise RegistryError('Governed formal launch requires explicit frozen arguments, including an empty array')
    observed = verify_environment(root, record['env_revision'])
    if directive is not None:
        directive = check_execution_dispatch(root, record, require_bound=True)
        remaining = directive['timing']['dispatch_seconds_remaining']
        if remaining is not None:
            if remaining <= 0:
                raise RegistryError('Original workflow dispatch budget exhausted before launch')
            bounds.append(remaining)
    effective_timeout = min(bounds) if bounds else None
    snapshot_dir = verify_ref(root, record['snapshot_ref']).parent
    configuration = read_record(snapshot_dir / 'configuration.json')
    resource_binding = configuration.get('resource_budget')
    stop_authorization = _stop_authorization(configuration)
    _validate_monitor_bindings(root, record, configuration)
    resource_admission = check_execution_resources(root, record)
    bootstrap = r'''
import importlib.abc, importlib.machinery, json, pathlib, runpy, sys, sysconfig
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.dont_write_bytecode = True
root, snapshot, entry, trace, *arguments = sys.argv[1:]
root, snapshot = pathlib.Path(root).resolve(), pathlib.Path(snapshot).resolve()
# A validated interpreter may live in the project's .venv. Its installed
# dependencies are environment inputs, rather than mutable project sources.
environment_roots = tuple(pathlib.Path(value).resolve() for key, value in sysconfig.get_paths().items()
                          if key in ('purelib', 'platlib', 'stdlib', 'platstdlib'))
sys.path[:0] = [str(snapshot / 'src'), str(snapshot)]
class FrozenProjectImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec and spec.origin and spec.origin not in ('built-in', 'frozen'):
            origin = pathlib.Path(spec.origin).resolve()
            if (origin.is_relative_to(root) and not origin.is_relative_to(snapshot)
                    and not any(origin.is_relative_to(prefix) for prefix in environment_roots)):
                raise ImportError('Mutable project import rejected: ' + str(origin))
        return None
sys.meta_path.insert(0, FrozenProjectImports())
sys.argv = [str(snapshot / entry)] + arguments
try:
    runpy.run_path(str(snapshot / entry), run_name='__main__')
finally:
    paths = {name: str(getattr(module, '__file__', '')) for name, module in sys.modules.items()
             if getattr(module, '__file__', None)}
    pathlib.Path(trace).write_text(json.dumps(paths, sort_keys=True))
'''
    command = [observed['interpreter'], '-I', '-c', bootstrap, str(root), str(snapshot_dir),
               snapshot['entrypoint'], str(directory / 'import-paths.json'), *map(str, arguments)]
    launch_environment = None
    if resource_admission is not None:
        # Restrict the actual child to the admitted physical devices; host indices
        # can differ from CUDA's process-local numbering. Empty means CPU-only.
        admitted = resource_binding['request']['gpus']
        devices = resource_admission['observed']['gpus']
        uuids = [next(row['uuid'] for row in devices if item['id'] in (row['id'], row['uuid']))
                 for item in admitted]
        launch_environment = dict(os.environ, CUDA_VISIBLE_DEVICES=','.join(uuids))
    with state_writer(root):
        with (directory / 'process.log').open('wb') as log:
            try:
                process, directive = _dispatch_process(root, directory, record, observed, command, log,
                                                        launch_environment, require_bound=directive is not None)
            except OSError as error:
                log.write(str(error).encode())
                exit_code, stopped = 127, False
            else:
                if directive is not None and directive['timing']['dispatch_seconds_remaining'] is not None:
                    remaining = directive['timing']['dispatch_seconds_remaining']
                    effective_timeout = min(bounds + [remaining])
                try:
                    atomic_write(directory / 'process.json', {'execution_run_id': execution_run_id,
                                 'pid': process.pid, 'host': platform.node(), 'command': command,
                                 'cwd': str(snapshot_dir), 'started_at': now(),
                                 'effective_timeout_seconds': effective_timeout,
                                 'timeout_basis': 'process_wall_seconds',
                                 'stop_authorization': stop_authorization})
                except BaseException as error:
                    interrupted = False
                    if 'launcher_error' in stop_authorization['conditions']:
                        _stop_owned_process(process, force_after_seconds=stop_authorization.get('force_after_seconds'))
                        interrupted = True
                    # Keep the attempt unresolved for explicit reconciliation:
                    # there is no durable process identity to certify its exit.
                    raise RegistryError(f'Process identity recording failed for execution {execution_run_id}, '
                                        f'PID {process.pid}; process_interrupted={interrupted}: {error}') from error
                try:
                    exit_code, stopped = _wait_controlled(root, directory, record, process,
                                                         effective_timeout, directive is not None, stop_authorization,
                                                         configuration)
                except BaseException as error:
                    interrupted = False
                    if 'launcher_error' in stop_authorization['conditions']:
                        _stop_owned_process(process, force_after_seconds=stop_authorization.get('force_after_seconds'))
                        interrupted = True
                    raise RegistryError(f'Observation interrupted for execution {execution_run_id}, PID {process.pid}; '
                                        f'process_interrupted={interrupted}: {error}') from error
        references = [fixed_ref(root, (directory / 'process.log').relative_to(root))]
        if (directory / 'process.json').exists():
            references.append(fixed_ref(root, (directory / 'process.json').relative_to(root)))
        if (directory / 'import-paths.json').exists():
            references.append(fixed_ref(root, (directory / 'import-paths.json').relative_to(root)))
        if (directory / 'termination.json').exists():
            references.append(fixed_ref(root, (directory / 'termination.json').relative_to(root)))
        if (directory / 'process-control-notices.json').exists():
            references.append(fixed_ref(root, (directory / 'process-control-notices.json').relative_to(root)))
        if (directory / 'resource-admission.json').exists():
            references.append(fixed_ref(root, (directory / 'resource-admission.json').relative_to(root)))
        if (directory / 'dispatch-admission.json').exists():
            references.append(fixed_ref(root, (directory / 'dispatch-admission.json').relative_to(root)))
        for name in ('stop-progress.json', 'training-budget-observations.json'):
            if (directory / name).exists():
                references.append(fixed_ref(root, (directory / name).relative_to(root)))
        reference = finish_execution(root, execution_run_id, exit_code, references, stopped=stopped)
        return {'exit_code': exit_code, 'execution_ref': reference}


def select_attempts(root, spec_ref, execution_refs):
    """Apply the predeclared slot aggregation, retaining every failed/excluded attempt."""
    spec = read_record(verify_ref(root, spec_ref))
    validate_schema('experiment', spec)
    if spec_digest(spec) != spec['spec_sha256']:
        raise RegistryError('Experiment spec digest is inconsistent')
    records, groups = [], {}
    for reference in execution_refs:
        record = validate_schema('execution', read_record(verify_ref(root, reference)))
        if record['spec_ref'] != spec_ref:
            raise RegistryError('Aggregation mixes different fixed experiment specs')
        if record['status'] not in ('completed', 'failed', 'stopped'):
            raise RegistryError('Aggregation needs terminal records, not floating running state')
        if record['variant_id'] not in {v['variant_id'] for v in spec['variants']} or record['seed'] not in spec['seeds']:
            raise RegistryError('Execution is not a declared experiment slot')
        if any(row['record']['execution_run_id'] == record['execution_run_id'] for row in records):
            raise RegistryError('Duplicate execution reference in aggregation')
        terminal, actual_ref = inspect_terminal(root, record['execution_run_id'])
        if terminal != record or actual_ref != reference:
            raise RegistryError('Aggregation reference is not the immutable terminal record')
        row = {'reference': reference, 'record': record, 'included': False, 'reason': record['status']}
        records.append(row)
        groups.setdefault((record['variant_id'], record['seed']), []).append(row)
    ids = {row['record']['execution_run_id']: row['record'] for row in records}
    for record in ids.values():
        parent_id = record['retry_of'] or record['resumed_from']
        if parent_id:
            parent = ids.get(parent_id)
            if parent is None:
                raise RegistryError('Aggregation must retain the failed/stopped parent attempt: ' + parent_id)
            if (parent['status'] not in ('failed', 'stopped')
                    or any(parent[key] != record[key] for key in ('spec_ref', 'variant_id', 'seed'))):
                raise RegistryError('Aggregation has an invalid retry/resume relation')
    for variant in spec['variants']:
        for seed in spec['seeds']:
            slot = (variant['variant_id'], seed)
            candidates = groups.get(slot, [])
            success = sorted((row for row in candidates if row['record']['status'] == 'completed'),
                             key=lambda row: (row['record']['created_at'], row['record']['execution_run_id']))
            rule = spec['failure_policy']['aggregation']
            selected = success if rule == 'all-attempts' else (
                success[:1] if rule == 'first-success' else success[-1:])
            for row in selected:
                row.update(included=True, reason=rule)
    missing = [(v['variant_id'], seed) for v in spec['variants'] for seed in spec['seeds']
               if not any(row['included'] for row in groups.get((v['variant_id'], seed), []))]
    return {'spec_ref': spec_ref, 'aggregation': spec['failure_policy']['aggregation'],
            'attempts': records, 'missing_slots': missing, 'scientific_verdict': 'not-assessed'}


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    sub = parser.add_subparsers(dest='command', required=True)
    spec = sub.add_parser('register-spec')
    spec.add_argument('--record', required=True)
    verify = sub.add_parser('verify-snapshot')
    verify.add_argument('--ref', required=True,
                        help='Path to a JSON reference object with path and sha256 fields; not the snapshot manifest or inline JSON')
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--request', required=True)
    launch = sub.add_parser('launch')
    launch.add_argument('--execution-id', required=True)
    launch.add_argument('--timeout', type=float)
    launch.add_argument('arguments', nargs=argparse.REMAINDER)
    recover = sub.add_parser('reconcile')
    recover.add_argument('--execution-id', required=True)
    recover.add_argument('--final-ref')
    recover.add_argument('--termination-ref')
    stop = sub.add_parser('stop', help='Request an identity-bound local execution stop; await actual terminal evidence')
    stop.add_argument('--execution-id', required=True)
    stop.add_argument('--reason', required=True)
    stop.add_argument('--confirmed-by', required=True, help='Actual user stop choice reference for this execution')
    stop.add_argument('--force-after-seconds', type=float, help='Only when that user choice explicitly authorizes forced termination')
    args = parser.parse_args()
    try:
        if args.command == 'register-spec':
            result = register_spec(args.root, read_record(args.record))
        elif args.command == 'verify-snapshot':
            result = verify_snapshot(args.root, read_record(args.ref))
        elif args.command == 'prepare':
            request = read_record(args.request)
            parent = {key: request.pop(key) for key in ('workflow_run_id', 'job_ref', 'retry_of', 'resumed_from', 'checkpoint_ref')
                      if key in request}
            reference = freeze_snapshot(args.root, **request)
            result = start_execution(args.root, request['execution_run_id'], reference, **parent)
        elif args.command == 'reconcile':
            result = reconcile_execution(args.root, args.execution_id,
                final_ref=read_record(args.final_ref) if args.final_ref else None,
                termination_ref=read_record(args.termination_ref) if args.termination_ref else None)
        elif args.command == 'stop':
            result = request_stop_execution(args.root, args.execution_id, args.reason, confirmed_by=args.confirmed_by,
                                            force_after_seconds=args.force_after_seconds)
        else:
            result = launch_execution(args.root, args.execution_id, args.arguments, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result.get('exit_code', 0) if isinstance(result, dict) else 0
    except (RegistryError, OSError, subprocess.SubprocessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
