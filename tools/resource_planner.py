"""Plan placements from one session policy and a fresh target-host sample."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

if __package__:
    from . import resource_budget as budget
    from .evaluation_profiles import read_profiles
    from .registry_common import RegistryError, atomic_write, configure_utf8_output, read_record, verify_ref
else:
    import resource_budget as budget
    from evaluation_profiles import read_profiles
    from registry_common import RegistryError, atomic_write, configure_utf8_output, read_record, verify_ref


PREFERENCES = ('balanced', 'fastest', 'lowest_resource')


def _task_request(task, host):
    required = {'gpu_options', 'cpu_cores', 'ram_bytes', 'job_seconds', 'storage', 'new_spend'}
    optional = {'host', 'max_parallel_jobs', 'preference', 'allow_gpu_sharing', 'io_bytes_per_second'}
    if not isinstance(task, dict) or not required <= task.keys() or task.keys() - required - optional:
        raise RegistryError('Task requires gpu_options and explicit CPU, RAM, time, storage and spending peaks')
    options = task['gpu_options']
    if not isinstance(options, list) or not options:
        raise RegistryError('Supply at least one GPU option, with count 0 for an explicit CPU-only option')
    for option in options:
        if not isinstance(option, dict) or not {'count', 'peak_bytes'} <= option.keys() or (
                option.keys() - {'count', 'peak_bytes', 'job_seconds'}):
            raise RegistryError('Each GPU option requires count and per-device peak_bytes')
        count, peak = option['count'], option['peak_bytes']
        if type(count) is not int or count < 0:
            raise RegistryError('GPU option count must be a nonnegative integer')
        budget._number(peak, 'GPU option peak_bytes', positive=count > 0)
        if count == 0 and peak != 0:
            raise RegistryError('A CPU-only option requires zero GPU peak bytes')
        if 'job_seconds' in option:
            budget._number(option['job_seconds'], 'GPU option job_seconds', positive=True)
    if task.get('preference', 'balanced') not in PREFERENCES:
        raise RegistryError('Unknown resource planning preference')
    if type(task.get('allow_gpu_sharing', True)) is not bool:
        raise RegistryError('Task allow_gpu_sharing must be boolean')
    limit = task.get('max_parallel_jobs')
    if limit is not None and (type(limit) is not int or limit < 0):
        raise RegistryError('Task max_parallel_jobs must be a nonnegative integer or null')
    request = {key: task[key] for key in required - {'gpu_options'}}
    if 'io_bytes_per_second' in task:
        request['io_bytes_per_second'] = task['io_bytes_per_second']
    request.update(host=task.get('host', host), gpus=[])
    budget._request(request)
    return request


def queue_context(state, job):
    """Read the queue's limits and other live placements from its durable state.

    Each placement carries the job's concrete peak request and sharing mode.
    An older live job without a placement has unknown remaining peaks.
    """
    active = []
    for row in state['jobs']:
        if row is job or row['status'] != 'running':
            continue
        placement = row.get('resource_assignment')
        active.append(dict(placement, execution_run_id=row['execution']['execution_run_id'],
                           job_id=row['id']) if placement else None)
    context = dict(state['meta']['resource_limits'], active=active, isolate_host=job.get('isolate_host', False),
                   cpu_only=bool(job.get('during')))
    reservation = state['meta'].get('reservation')
    if reservation:
        order = {row['id']: (-row.get('priority', 0), index) for index, row in enumerate(state['jobs'])}
        head = next((row for row in state['jobs'] if row['id'] == reservation['job_id']), None)
        if head and head['status'] == 'pending' and order[head['id']] < order[job['id']]:
            context['reservation'] = reservation
    if context.get('reservation') and job.get('backfill'):
        proof = job['backfill']
        try:
            elapsed = read_record(verify_ref(job['execution']['project_root'], proof['evidence']))['elapsed_seconds']
            budget._number(elapsed, 'backfill observed seconds', positive=True)
        except (OSError, ValueError, KeyError, TypeError):
            pass
        else:
            if elapsed <= proof['seconds']:
                context['backfill_seconds'] = proof['seconds']
    return context


def _devices(observation):
    return {alias: row for row in observation['gpus'] for alias in (row['id'], row['uuid'])}


def _allows(allowlist, device):
    return allowlist in (None, 'all_visible') or device['id'] in allowlist or device['uuid'] in allowlist


def _issue(resource, status, required, available):
    return {'resource': resource, 'status': status, 'required': required, 'available': available}


def _decision(check):
    return {'status': check['status'], 'checks': [check]}


def _combine(request, requests, gpus):
    result = dict(request, gpus=gpus, cpu_cores=sum(item['cpu_cores'] for item in requests),
                  ram_bytes=sum(item['ram_bytes'] for item in requests),
                  storage=[row for item in requests for row in item['storage']])
    io = [item.get('io_bytes_per_second') for item in requests]
    if None not in io:
        result['io_bytes_per_second'] = sum(io)
    else:
        result.pop('io_bytes_per_second', None)
    return result


def _active_reservation(context):
    reservation = context.get('reservation')
    duration = context.get('backfill_seconds')
    if reservation and duration is not None and reservation.get('ready_at') is not None:
        if time.time() + duration <= reservation['ready_at']:
            return None
    return reservation


def _reservation_issue(reservation, table, request, observation, active, limit, stage):
    """Keep the resources needed by the earlier job available at dispatch."""
    if reservation is None:
        return None
    reserved = reservation['request']
    reserved_cards = {row['id'] for row in reserved['gpus']}
    conflicts = reserved_cards.intersection(row['id'] for row in request['gpus'])
    if conflicts or reservation.get('isolate_host'):
        return _issue('queue_priority_reservation', 'WAIT_RESOURCE', reservation['job_id'],
                      sorted(conflicts) or 'host reserved')
    releasing = set(reservation.get('releasing_jobs', []))
    active = [item for item in active if item.get('job_id') not in releasing]
    caps = [cap for cap in (limit, reservation.get('max_parallel_jobs')) if cap is not None]
    if caps and len(active) + 2 > min(caps):
        return _issue('queue_priority_reservation', 'WAIT_RESOURCE', reservation['job_id'], 'parallel slot reserved')
    projected = [item['request'] for item in active] + [request, reserved]
    gpu_peaks = Counter()
    for item in projected:
        for row in item['gpus']:
            gpu_peaks[row['id']] += row['peak_bytes']
    combined = _combine(request, projected, [{'id': uuid, 'peak_bytes': peak} for uuid, peak in gpu_peaks.items()])
    virtual = dict(table, policy=dict(table['policy'], allowed_gpu_ids='all_visible', allow_gpu_sharing=True))
    result = budget.evaluate(virtual, combined, observation, stage=stage)
    for check in result['checks']:
        if check['status'] != 'OK' and not check['resource'].startswith(('gpu:', 'vram:')):
            return _issue('queue_priority_reservation', 'WAIT_RESOURCE', reservation['job_id'], check['resource'])
    return None


def _select_devices(eligible, count, peak, reserved, blocked, exclusive, preference):
    def rank(row):
        slack = row['free_bytes'] - reserved[row['uuid']] - peak
        occupied = row.get('process_ids') != [] or row['utilization_percent'] > 0
        unavailable = row['uuid'] in blocked or (exclusive and occupied) or slack < 0
        # Rank physically viable cards first, even when temporarily busy, so
        # the explanation distinguishes a capacity deficit from a wait.
        return (row['total_bytes'] < peak, unavailable,
                slack if preference == 'lowest_resource' else -slack, row['uuid'])

    return [row['uuid'] for row in sorted(eligible, key=rank)[:count]]


def _evaluate_placement(table, request, observation, *, stage, exclusive, allowed, active):
    """Use existing admission checks on the job and then on overlapping peaks."""
    devices = _devices(observation)
    if any(row['id'] in devices and not _allows(allowed, devices[row['id']]) for row in request['gpus']):
        return _decision(_issue('queue_gpu_allowlist', 'NEEDS_APPROVAL', request['gpus'], allowed))
    if exclusive and table['policy']['allow_gpu_sharing']:
        table = dict(table, policy=dict(table['policy'], allow_gpu_sharing=False))
    result = budget.evaluate(table, request, observation, stage=stage)
    if result['status'] != 'AUTO_APPROVED':
        return result
    gpu_ids = {row['id'] for row in request['gpus']}
    shared = {uuid for uuid in gpu_ids if devices[uuid].get('process_ids')
              or devices[uuid]['utilization_percent'] > 0}
    result.update(shared_gpu_uuids=sorted(shared), concurrent_jobs=len(active) + 1)
    if not active:
        return result
    if None in active:
        return _decision(_issue('active_job_peaks', 'NEEDS_ESTIMATE', 'verified concurrent peaks', None))

    for placement in active:
        overlap = gpu_ids.intersection(row['id'] for row in placement['request']['gpus'])
        if overlap and (exclusive or placement['exclusive']):
            return _decision(_issue('exclusive_reservation', 'WAIT_RESOURCE', sorted(overlap), 'reserved'))
        shared.update(overlap)

    requests = [placement['request'] for placement in active] + [request]
    vram = Counter()
    for item in requests:
        for row in item['gpus']:
            # If a previously assigned card disappeared while work may still
            # be alive, the batch cannot substantiate its current GPU peak.
            if row['id'] not in devices:
                return _decision(_issue('active_gpu_telemetry', 'NEEDS_ESTIMATE', row['id'], None))
            vram[row['id']] += row['peak_bytes']
    combined = _combine(request, requests, [{'id': uuid, 'peak_bytes': peak} for uuid, peak in sorted(vram.items())])
    # The job check already enforced its device policy and time/spend limits.
    # Include other placements' peaks even if a newer allowlist excludes them.
    capacity_table = dict(table, policy=dict(table['policy'], allowed_gpu_ids='all_visible', allow_gpu_sharing=True))
    aggregate = budget.evaluate(capacity_table, combined, observation, stage=stage)
    statuses = {check['status'] for check in aggregate['checks']}
    status = ('NEEDS_ESTIMATE' if 'NEEDS_ESTIMATE' in statuses else
              'WAIT_RESOURCE' if statuses - {'OK'} else 'AUTO_APPROVED')
    result.update(status=status, batch_checks=aggregate['checks'],
                  shared_gpu_uuids=sorted(shared), concurrent_jobs=len(requests),
                  overlapping_attempts=[item['execution_run_id'] for item in active if 'execution_run_id' in item])
    return result


def _options(base, task, profiles, observation, eligible, exclusive, active, preference, placement, reservation):
    devices = _devices(observation)
    if task is None:
        # Pin historical index-based requests to the UUID sampled for this attempt.
        gpus = [dict(row, id=devices[row['id']]['uuid']) if row['id'] in devices else row for row in base['gpus']]
        yield dict(base, gpus=gpus), None, None
        return
    reserved, blocked = Counter(), set()
    for item in active:
        if item is None:
            continue
        for row in item['request']['gpus']:
            reserved[row['id']] += row['peak_bytes']
            if exclusive or item['exclusive']:
                blocked.add(row['id'])
    if reservation:
        blocked.update(row['id'] for row in reservation['request']['gpus'])
    if profiles is None:
        options = [(option, None) for option in task['gpu_options']]
    else:
        options = [({'count': len(profile['gpu_uuids']), 'peak_bytes': profile['peak_bytes_per_gpu']}, profile)
                   for profile in profiles['profiles']]
    for option, profile in options:
        count, peak = option['count'], option['peak_bytes']
        if profile is not None:
            if profiles['host'] != observation['host'] or not set(profile['gpu_uuids']) <= {row['uuid'] for row in eligible}:
                yield None, _issue('evaluation_profile_devices', 'REPLAN_REQUIRED',
                                   profile['gpu_uuids'], [row['uuid'] for row in eligible]), profile
                continue
            yield dict(base, gpus=[{'id': uuid, 'peak_bytes': peak} for uuid in profile['gpu_uuids']]), None, profile
            continue
        if len(eligible) < count and placement is None:
            status = 'NEEDS_ESTIMATE' if observation.get('gpu_probe_error') else 'REPLAN_REQUIRED'
            yield None, _issue('eligible_gpu_count', status, count, len(eligible)), None
            continue
        # When launching, validate the chosen UUIDs using the latest telemetry
        # rather than switching cards after the queue made other assignments.
        selected = ([row['id'] for row in placement['request']['gpus']] if placement is not None else
                    _select_devices(eligible, count, peak, reserved, blocked, exclusive, preference))
        if len(selected) != count:
            continue
        yield dict(base, job_seconds=option.get('job_seconds', base['job_seconds']),
                   gpus=[{'id': uuid, 'peak_bytes': peak} for uuid in selected]), None, None


def _rank(candidate, preference):
    request = candidate['request']
    footprint = (len(request['gpus']), sum(row['peak_bytes'] for row in request['gpus']))
    if profile := candidate.get('evaluation_profile'):
        elapsed, cost = profile['elapsed_seconds'], profile['gpu_seconds']
        if preference == 'fastest':
            return (elapsed, cost, *footprint)
        if preference == 'balanced':
            return (cost, elapsed, *footprint)
        return (*footprint, elapsed)
    if preference == 'fastest':
        return (request['job_seconds'], *footprint)
    return (*footprint, request['job_seconds'])


def plan(root, binding, *, pending_jobs=1, stage='plan', persist=False, queue_context=None, placement=None):
    """Return admitted placements for repeated identical pending requests on this host.

    ``binding`` is the existing session binding with a concrete ``request`` or
    an immutable ``task`` of interchangeable resource options. Peaks are in
    bytes, cores and seconds. Optional queue context supplies stricter device
    and parallel ceilings plus the other live jobs' placements. ``placement``
    pins the queued request at final launch. Only ``persist`` updates the
    original table's last check. The result includes checked alternatives,
    current capacity and the number of additional jobs that fit in this order.
    """
    if stage not in ('plan', 'launch'):
        raise RegistryError('Resource plan stage must be plan or launch')
    if type(pending_jobs) is not int or pending_jobs < 1:
        raise RegistryError('pending_jobs must be a positive integer')
    table_root = budget.binding_table_root(root, binding)
    session = binding['session_id']
    table = budget.read_table(table_root, session)
    if table is None and persist:
        table = budget.initialize(table_root, session)
    task = binding.get('task')
    profiles = None
    if task is not None and 'evaluation_profiles_ref' in task:
        task = dict(task)
        profiles = read_profiles(root, task.pop('evaluation_profiles_ref'))
        if 'gpu_options' in task:
            raise RegistryError('Declare verified evaluation profiles or standalone GPU options')
        task['gpu_options'] = [{'count': len(item['gpu_uuids']), 'peak_bytes': item['peak_bytes_per_gpu']}
                               for item in profiles['profiles']]
    if 'task' in binding:
        base = _task_request(task, 'awaiting-host-probe')
    else:
        base = binding['request']
        budget._request(base)
    context = queue_context or {}
    active = list(context.get('active', []))
    reservation = _active_reservation(context)
    if placement is not None:
        budget._request(placement['request'])
    storage = base['storage'] + [row for item in active if item is not None for row in item['request']['storage']]
    if reservation:
        storage += reservation['request']['storage']
    observation = budget.probe(root, storage)
    if task is not None and 'host' not in task:
        base['host'] = observation['host']
    result = budget.evaluate(table, None, observation, stage='plan')
    candidates, assignments = [], []
    policy = table['policy'] if table else budget.DEFAULT_POLICY
    allowed = context.get('allowed_gpu_ids')
    eligible = [row for row in observation['gpus']
                if _allows(policy['allowed_gpu_ids'], row) and _allows(allowed, row)]
    task_limit = task.get('max_parallel_jobs') if task is not None else None
    session_limit = policy.get('max_parallel_jobs')
    limits = [value for value in (task_limit, session_limit, context.get('max_parallel_jobs'),
              *(item.get('max_parallel_jobs') for item in active if item is not None)) if value is not None]
    limit = min(limits) if limits else None
    exclusive = (not policy['allow_gpu_sharing'] or not (task or {}).get('allow_gpu_sharing', True)
                 or bool(placement and placement['exclusive']))
    preference = (task or {}).get('preference', 'fastest' if profiles else 'balanced')
    isolate_host = bool(context.get('isolate_host') or (placement or {}).get('isolate_host'))
    if result['status'] == 'READY_TO_PLAN':
        for _ in range(pending_jobs):
            if limit is not None and len(active) >= limit:
                result = _decision(_issue('max_parallel_jobs', 'WAIT_RESOURCE', len(active) + 1, limit))
                break
            checked = []
            isolated_overlap = active and (isolate_host or any((item or {}).get('isolate_host') for item in active))
            for request, issue, profile in _options(base, task, profiles, observation, eligible, exclusive, active,
                                                     preference, placement, reservation):
                if placement is not None and (request != placement['request']
                        or profile != placement.get('evaluation_profile')):
                    continue
                if issue is None and isolated_overlap:
                    issue = _issue('host_measurement_isolation', 'WAIT_RESOURCE', 'exclusive batch', 'active jobs')
                check = (_decision(issue) if issue else _evaluate_placement(
                    table, request, observation, stage=stage, exclusive=exclusive, allowed=allowed, active=active))
                if check['status'] == 'AUTO_APPROVED':
                    reserved = _reservation_issue(reservation, table, request, observation, active, limit, stage)
                    if reserved:
                        check = _decision(reserved)
                candidate = dict(check, request=request)
                if profile is not None:
                    candidate['evaluation_profile'] = profile
                checked.append(candidate)
            if not candidates:
                candidates = checked
            approved = [item for item in checked if item['status'] == 'AUTO_APPROVED']
            if not approved:
                # If any candidate can run when occupied capacity frees, keep
                # waiting rather than escalating an unrelated candidate's cap.
                order = ('WAIT_RESOURCE', 'NEEDS_ESTIMATE', 'NEEDS_APPROVAL', 'REPLAN_REQUIRED')
                result = min(checked, key=lambda item: order.index(item['status'])) if checked else _decision(
                    _issue('queued_placement', 'NEEDS_ESTIMATE', 'fresh matching UUIDs and peaks', 'placement changed'))
                break
            choice = min(approved, key=lambda item: _rank(item, preference))
            local_limits = [number for number in (task_limit, session_limit) if number is not None]
            assignment = {'request': choice['request'], 'exclusive': exclusive,
                          'max_parallel_jobs': min(local_limits, default=None), 'concurrent_jobs': len(active) + 1,
                          'shared_gpu_uuids': choice.get('shared_gpu_uuids', []),
                          'overlapping_attempts': choice.get('overlapping_attempts', [])}
            if isolate_host:
                assignment['isolate_host'] = True
            if profiles is not None:
                assignment['evaluation_profile'] = choice['evaluation_profile']
            active.append(assignment)
            assignments.append((choice, assignment))
    first, assignment = assignments[0] if assignments else (result, None)
    report = dict(first, candidates=candidates, slots=len(assignments), pending_jobs=pending_jobs,
                  assignments=[item for _, item in assignments], assignment=assignment,
                  preference=preference, parallel_limit=limit, exclusive=exclusive,
                  concurrent_jobs=first.get('concurrent_jobs', 1 if assignment else 0),
                  remaining_capacity_check=result if len(assignments) < pending_jobs else None)
    report = budget.record_check(table_root, session, table, report, observation, first.get('request'),
                                 stage=stage, persist=False)
    report['effective_capacity'].update(gpus=eligible, max_parallel_jobs=limit)
    if persist:
        # Persist the evaluated request, not a second set of scheduling state.
        budget.save_check(table_root, session, table, {key: value for key, value in report.items()
            if key not in ('candidates', 'assignments', 'assignment', 'remaining_capacity_check')})
    return report


def markdown(table, result):
    """Render a plan and the checks that limited its proposed placements."""
    capacity = result['effective_capacity']
    eligible = ', '.join(f"{row['id']} ({row['uuid']})" for row in capacity['gpus']) or 'none observed'
    preference = result['preference']
    ranking = {'balanced': 'Prefer fewer devices and lower peak demand, then more free headroom.',
               'fastest': 'Prefer the shortest declared duration, then fewer devices and more free headroom.',
               'lowest_resource': 'Prefer fewer devices and lower peak demand, then the tightest fit.'}
    lines = ['# Resource plan', '', budget.markdown(table, result).rstrip(), '',
             f"Eligible devices: {eligible}.",
             f"Effective CPU capacity: {capacity['cpu_cores']} cores. Effective RAM: {capacity['ram_bytes']} B.",
             f"Additional concurrent jobs that fit: {result['slots']} of {result['pending_jobs']}",
             f"Preference: {preference}. {ranking[preference]}",
             'Record GPU sharing and actual concurrency in the comparison log. Use isolated runs for timing comparisons.',
             'Before each launch, verify the current session selection, leases and host capacity again.', '']
    for key, candidate in enumerate(result['candidates'], 1):
        request = candidate['request']
        devices = ', '.join(f"{gpu['id']} +{gpu['peak_bytes']} B" for gpu in request['gpus']) if request else ''
        lines.append(f"- Candidate {key} ({devices or ('CPU only' if request else 'no eligible placement')}): {candidate['status']}")
        for item in candidate['checks'] + candidate.get('batch_checks', []):
            if item['status'] != 'OK':
                lines.append(f"  - {item['resource']}: {item['required']} required, {item['available']} available ({item['status']})")
    for index, assignment in enumerate(result['assignments'], 1):
        gpus = ', '.join(row['id'] for row in assignment['request']['gpus']) or 'CPU only'
        lines.append(f"- Slot {index} uses {gpus} ({'exclusive' if assignment['exclusive'] else 'sharing allowed'}).")
    if result['request'] is not None and result['slots']:
        lines.append(f"- The selected request estimates {result['request']['job_seconds']:g} seconds per job.")
    blocker = result['remaining_capacity_check']
    if blocker:
        for item in blocker['checks'] + blocker.get('batch_checks', []):
            if item['status'] != 'OK':
                lines.append(f"- Next slot: {item['resource']} needs {item['required']} with {item['available']} available ({item['status']}).")
    return '\n'.join(lines) + '\n'


def main():
    configure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.', help='Project root on the execution host')
    parser.add_argument('--session', help='Stable session ID (defaults to the host thread ID)')
    parser.add_argument('--table-root', help='Absolute original table owner if it differs from --root')
    parser.add_argument('--task', type=Path, required=True, help='Path to the JSON task resource template')
    parser.add_argument('--preference', choices=PREFERENCES)
    parser.add_argument('--pending-jobs', type=int, default=1, help='Number of pending jobs with these same peaks')
    parser.add_argument('--output-dir', type=Path, help='Write RESOURCE_PLAN.md and resource-request.json here')
    parser.add_argument('--markdown', action='store_true')
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve()
        task = read_record(args.task)
        if args.preference is not None:
            task['preference'] = args.preference
        binding = {'task': task, 'session_id': budget.session_id(args.session), 'table_root': args.table_root or root}
        result = plan(root, binding, pending_jobs=args.pending_jobs)
        text = markdown(budget.read_table(binding['table_root'], binding['session_id']), result)
        if args.output_dir is not None:
            # Replace stale readiness artifacts when a fresh plan cannot fit.
            atomic_write(args.output_dir / 'resource-request.json', result['request'] if result['slots'] else b'null\n')
            atomic_write(args.output_dir / 'RESOURCE_PLAN.md', text.encode('utf-8'))
        print(text if args.markdown else json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result['status'] == 'AUTO_APPROVED' else 3
    except (RegistryError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
