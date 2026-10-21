"""Frozen experiment specifications, source snapshots and distinct execution attempts.

The existing workflow/queue remains the coordinator. These APIs bind its jobs
to evidence, preserve failures and record real local process exit codes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
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
except ImportError:
    from registry_common import (RegistryError, configure_utf8_output, atomic_write, canonical, digest, file_lock,
                                 fixed_ref, identifier, local_path, now, read_record,
                                 validate_schema, verify_ref)
    from state_paths import resolve_state_root, state_writer
    from environment_registry import verify_environment


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
                retry_arguments[index] = retry_arguments[index].replace('runs/' + parent_id + '/', 'runs/' + execution_run_id + '/')
            expected_manifest['arguments'] = retry_arguments
        expected_files = {*snapshot['source_files'], 'configuration.json', 'manifest.json'}
        existing_files = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()} if target.exists() else set()
        if existing_files - expected_files:
            raise RegistryError('Retry snapshot contains undeclared content')
        for name in [*snapshot['source_files'], 'configuration.json']:
            source, destination = local_path(original, name), local_path(target, name)
            payload = source.read_bytes()
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


def _stop_owned_process(process):
    """Stop the process group created by this launcher and reap its parent."""
    try:
        if os.name == 'posix':
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    # The parent can exit before a child that ignores SIGTERM. Kill the owned
    # group even when wait() has already returned; never target unrelated jobs.
    try:
        if os.name == 'posix':
            os.killpg(process.pid, signal.SIGKILL)
        elif process.poll() is None:
            process.kill()
    except ProcessLookupError:
        pass
    process.wait()


def request_stop_execution(root, execution_run_id, reason):
    """Request cancellation of one running local execution, without sending signals.

    Bind the request to its immutable snapshot and observed local process file.
    The existing launcher observes it, stops its own process group and freezes
    actual termination evidence. Return a fixed request reference; this is not
    a termination receipt and cannot settle a live reservation. Same-reason
    retries reuse the request; changed reasons/identities are rejected.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise RegistryError('Execution stop needs a reason')
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
                    or existing.get('reason') != reason):
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
                             'reason': reason, 'requested_at': now()})
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


def _wait_controlled(root, directory, record, process, timeout, bound_workflow):
    """Wait for actual exit while observing only this execution's control inputs."""
    started = time.monotonic()
    cause = None
    while process.poll() is None:
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
                cause = {'cause': 'execution_stop', 'reason': request['reason'],
                         'requested_at': request['requested_at'],
                         'request_ref': fixed_ref(root, request_path.relative_to(root))}
            if cause is None and bound_workflow:
                directive = _workflow_directive(root, record)
                if directive is None:
                    raise RegistryError('Bound workflow control disappeared')
                if directive['stopped']:
                    cause = {'cause': 'workflow_stop', 'reason': directive['stopped']['reason'],
                             'requested_at': directive['stopped']['at']}
                elif directive['timing']['dispatch_seconds_remaining'] <= 0:
                    cause = {'cause': 'workflow_deadline', 'reason': 'Original dispatch budget exhausted'}
            if cause is None and timeout is not None and time.monotonic() - started >= timeout:
                cause = {'cause': 'timeout', 'reason': 'Fixed execution time limit reached'}
        except (RegistryError, OSError, ValueError, TypeError, KeyError) as error:
            cause = {'cause': 'control_error', 'reason': str(error)}
        if cause is not None:
            _stop_owned_process(process)
            receipt = dict(cause, schema_version=1, execution_run_id=record['execution_run_id'],
                           workflow_run_id=record.get('workflow_run_id'), snapshot_ref=record['snapshot_ref'],
                           process_ref=fixed_ref(root, (directory / 'process.json').relative_to(root)),
                           pid=process.pid, exit_code=process.returncode, parent_exited=True,
                           termination_scope='posix-process-group' if os.name == 'posix' else 'windows-parent-only',
                           observed_at=now())
            atomic_write(directory / 'termination.json', receipt)
            return process.returncode, True
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            pass
    return process.returncode, False


def launch_execution(root, execution_run_id, arguments=(), *, timeout=None):
    """Launch an authorized local CPU/GPU entry from its verified snapshot and interpreter.

    Resource authorization/budgets belong to the calling execution skill. Imports
    of mutable project code are rejected and actual import paths are retained.
    The local wait observes bound workflow stops and identity-bound per-execution
    requests. Effective timeout is the minimum of an explicit bound, the spec's
    max_seconds_per_attempt and the configured workflow's original remaining
    dispatch time. Ordinary reflection does not interrupt a healthy process.
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
    directive = _workflow_directive(root, record)
    if directive is not None and directive['stopped']:
        raise RegistryError('Bound workflow already stopped; execution was not launched')
    try:
        from .project_registry import discover_project
    except ImportError:
        from project_registry import discover_project
    if discover_project(root)['layout_profile'] == 'governed-v1' and 'arguments' not in snapshot:
        raise RegistryError('Governed formal launch requires explicit frozen arguments, including an empty array')
    observed = verify_environment(root, record['env_revision'])
    if directive is not None:
        directive = _workflow_directive(root, record)
        if directive is None or directive['stopped']:
            raise RegistryError('Bound workflow stopped or disappeared before launch')
        remaining = directive['timing']['dispatch_seconds_remaining']
        if remaining <= 0:
            raise RegistryError('Original workflow dispatch budget exhausted before launch')
        bounds.append(remaining)
    effective_timeout = min(bounds) if bounds else None
    snapshot_dir = verify_ref(root, record['snapshot_ref']).parent
    with state_writer(root) as state, file_lock(state / 'locks/executions.lock'):
        current = read_record(path)
        if current['status'] != 'prepared':
            raise RegistryError('Another writer already launched this execution')
        record.update(status='running', observed_fingerprint=observed, updated_at=now())
        atomic_write(path, record)
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
    with state_writer(root):
        with (directory / 'process.log').open('wb') as log:
            try:
                process = subprocess.Popen(command, cwd=snapshot_dir, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=os.name == 'posix')
            except OSError as error:
                log.write(str(error).encode())
                exit_code, stopped = 127, False
            else:
                try:
                    atomic_write(directory / 'process.json', {'execution_run_id': execution_run_id,
                                 'pid': process.pid, 'host': platform.node(), 'command': command,
                                 'cwd': str(snapshot_dir), 'started_at': now(),
                                 'effective_timeout_seconds': effective_timeout})
                except BaseException:
                    _stop_owned_process(process)
                    # Keep the attempt unresolved for explicit reconciliation:
                    # there is no durable process identity to certify its exit.
                    raise
                try:
                    exit_code, stopped = _wait_controlled(root, directory, record, process,
                                                         effective_timeout, directive is not None)
                except BaseException:
                    _stop_owned_process(process)
                    raise
        references = [fixed_ref(root, (directory / 'process.log').relative_to(root))]
        if (directory / 'process.json').exists():
            references.append(fixed_ref(root, (directory / 'process.json').relative_to(root)))
        if (directory / 'import-paths.json').exists():
            references.append(fixed_ref(root, (directory / 'import-paths.json').relative_to(root)))
        if (directory / 'termination.json').exists():
            references.append(fixed_ref(root, (directory / 'termination.json').relative_to(root)))
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
            result = request_stop_execution(args.root, args.execution_id, args.reason)
        else:
            result = launch_execution(args.root, args.execution_id, args.arguments, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result.get('exit_code', 0) if isinstance(result, dict) else 0
    except (RegistryError, OSError, subprocess.SubprocessError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
