import argparse
import json
from pathlib import Path
import random

p = argparse.ArgumentParser()
p.add_argument('--steps', type=int, default=300000)
p.add_argument('--save-every', type=int, default=5)
p.add_argument('--output', default='checkpoints')
a = p.parse_args()
rng = random.Random(42)
root = Path(a.output)
root.mkdir(parents=True, exist_ok=True)
state = {'step': 0, 'weight': 0.1, 'momentum': 0.0, 'lr': 0.05, 'data_cursor': 0}
for step in range(1, a.steps + 1):
    x = rng.uniform(-1, 1)
    target = 2 * x + rng.gauss(0, 0.01)
    state['momentum'] = 0.8 * state['momentum'] + 2 * (state['weight'] * x - target) * x
    state['weight'] -= state['lr'] * state['momentum']
    state['step'] = step
    state['data_cursor'] = step
    if step % a.save_every == 0:
        state['rng'] = rng.getstate()
        (root / f'step_{step}.json').write_text(json.dumps(state))
print(json.dumps({'step': state['step'], 'weight': state['weight']}))
