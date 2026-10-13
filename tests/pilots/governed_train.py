"""Tiny real trainer for governance/recovery acceptance; no research claim.

Shared deterministic data use fixed training/validation IDs. The only method
extension is training noise. A bounded store saves model, optimizer, scheduler,
Python/CPU/device RNG and step; validators load states in a forked RNG context.
"""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import sys

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import torch

from checkpoint_retention import CheckpointStore

torch.set_num_threads(2)
torch.use_deterministic_algorithms(True)
cfg = json.loads(Path('configuration.json').read_text())
execution = json.loads((Path.cwd().parent / 'execution.json').read_text())
device = torch.device(cfg['device'])
seed = cfg['seed']
random.seed(seed)
torch.manual_seed(seed)
if device.type == 'cuda':
    torch.cuda.set_device(device)
    torch.cuda.manual_seed(seed)
    torch.cuda.reset_peak_memory_stats(device)


def make_model():
    return torch.nn.Sequential(torch.nn.Linear(8, 12), torch.nn.ReLU(),
                               torch.nn.Dropout(0.2), torch.nn.Linear(12, 1)).double().to(device)


generator = torch.Generator().manual_seed(2026)
features = torch.randn(128, 8, generator=generator, dtype=torch.float64).to(device)
labels = (features[:, :1] * 0.8 + features[:, 1:2] * -0.2)
train_ids, validation_ids = list(range(96)), list(range(96, 128))
model = make_model()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.9)
start_step, best_loss, best_model = 0, float('inf'), None
recovery = execution['checkpoint_ref']
if recovery:
    checkpoint = Path.cwd().parents[2] / recovery['path']
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == recovery['sha256']
    state = torch.load(checkpoint, map_location=device, weights_only=False)
    model.load_state_dict(state['model'])
    optimizer.load_state_dict(state['optimizer'])
    scheduler.load_state_dict(state['scheduler'])
    random.setstate(state['python_rng'])
    torch.random.set_rng_state(state['cpu_rng'].cpu())
    if device.type == 'cuda':
        torch.cuda.set_rng_state(state['device_rng'].cpu(), device)
    start_step, best_loss, best_model = state['step'], state['best_loss'], state['best_model']

output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
store = CheckpointStore.create(output.parent / 'checkpoints', run_id=execution['execution_run_id'],
                               budget_bytes=512_000, keep_last=2)
peaks = []


def publish(value, step, kind='resume', roles=()):
    buffer = io.BytesIO()
    torch.save(value, buffer)
    content = buffer.getvalue()

    def writer(directory):
        (directory / 'state.pt').write_bytes(content)
        peaks.append(store.status()['bytes_used'])

    def validator(directory):
        loaded = torch.load(directory / 'state.pt', map_location=device, weights_only=False)
        devices = [device.index or 0] if device.type == 'cuda' else []
        with torch.random.fork_rng(devices=devices):
            probe = make_model()
            probe.load_state_dict(loaded['model'])
            probe.eval()
            assert torch.isfinite(probe(features[validation_ids])).all()
            if kind == 'resume':
                probe_optimizer = torch.optim.AdamW(probe.parameters(), lr=0.01)
                probe_optimizer.load_state_dict(loaded['optimizer'])
                probe_scheduler = torch.optim.lr_scheduler.StepLR(probe_optimizer, step_size=3, gamma=0.9)
                probe_scheduler.load_state_dict(loaded['scheduler'])
                assert loaded['step'] == step and probe_scheduler.last_epoch == step
                assert {'python_rng', 'cpu_rng', 'device_rng'} <= loaded.keys()
        return {'loader': 'torch.load + model forward + optimizer/scheduler restore', 'step': step}

    return store.publish(step=step, kind=kind, expected_bytes=len(content), writer=writer,
                         validator=validator, validation_label='Actual PyTorch loader', roles=roles)


for step in range(start_step + 1, cfg['steps'] + 1):
    model.train()
    ids = torch.randperm(96)[:16].to(device)
    batch = features[ids] + cfg['variant']['augmentation'] * random.random()
    optimizer.zero_grad()
    loss = (model(batch) - labels[ids]).square().mean()
    loss.backward()
    optimizer.step()
    scheduler.step()
    if step % 3 == 0:
        model.eval()
        with torch.no_grad():
            validation_loss = float((model(features[validation_ids]) - labels[validation_ids]).square().mean())
        assert math.isfinite(validation_loss)
        if validation_loss < best_loss:
            best_loss = validation_loss
            best_model = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            publish({'model': best_model}, step, 'weights', ('best',))
        state = {'step': step, 'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                 'scheduler': scheduler.state_dict(), 'python_rng': random.getstate(),
                 'cpu_rng': torch.random.get_rng_state(),
                 'device_rng': torch.cuda.get_rng_state(device) if device.type == 'cuda' else None,
                 'best_loss': best_loss, 'best_model': best_model}
        publish(state, step)
        assert len([e for e in store._read()['entries'] if e['kind'] == 'resume']) <= 2
        if cfg.get('stop_step') == step and not recovery:
            print(json.dumps({'intentional_interrupt_step': step, 'checkpoint': str(store.latest())}))
            raise SystemExit(17)

model.eval()
with torch.no_grad():
    final_loss = float((model(features[validation_ids]) - labels[validation_ids]).square().mean())
publish({'model': best_model}, cfg['steps'], 'weights', ('best',))
publish({'model': model.state_dict()}, cfg['steps'], 'weights', ('final',))


def json_state(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): json_state(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_state(v) for v in value]
    return value


result = {'execution_run_id': execution['execution_run_id'], 'device': str(device),
          'start_step': start_step, 'step': cfg['steps'], 'variant': cfg['variant'],
          'seed': seed, 'train_ids': train_ids, 'validation_ids': validation_ids,
          'validation_loss': final_loss, 'best_validation_loss': best_loss,
          'model_state': json_state(model.state_dict()), 'optimizer_state': json_state(optimizer.state_dict()),
          'scheduler_state': json_state(scheduler.state_dict()),
          'python_rng': json_state(random.getstate()),
          'cpu_rng': torch.random.get_rng_state().tolist(),
          'device_rng': torch.cuda.get_rng_state(device).tolist() if device.type == 'cuda' else None,
          'save_peak_bytes': max(peaks), 'save_budget_bytes': 512_000,
          'device_peak_allocated_bytes': torch.cuda.max_memory_allocated(device) if device.type == 'cuda' else 0}
output.write_text(json.dumps(result, sort_keys=True) + '\n')
store.finish(outcome='completed', step=cfg['steps'], reason='All planned optimizer steps completed', apply=True)
assert not any(e['kind'] == 'resume' for e in store._read()['entries'])
print(json.dumps({k: result[k] for k in ('execution_run_id', 'device', 'step', 'validation_loss', 'save_peak_bytes')}))
