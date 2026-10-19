"""Read-only numerical consumer checks; no documentation keyword matching."""
from copy import deepcopy
import importlib.util
import math
from pathlib import Path

module_path = Path(__file__).parent / 'src/diagnostics.py'
spec = importlib.util.spec_from_file_location('diagnostics', module_path)
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)
run = diagnostics.diagnose


def equal(actual, expected):
    assert actual.keys() == expected.keys(), (actual, expected)
    for key, value in expected.items():
        if isinstance(value, float):
            assert math.isclose(actual[key], value, rel_tol=1e-12), (actual, expected)
        else:
            assert actual[key] == value, (actual, expected)


t = [[1., None], [4., 10.], [None, 8.]]
p = [[3., None], [3., 14.], [None, 10.]]
m = [[True, False], [True, True], [False, True]]
saved = deepcopy((t, p, m))
equal(run(t, p, m), {'overall_mae': 2.25, 'horizon_mae': [1.5, 3.0], 'counts': [2, 2]})
equal(run(t, p, m, horizon_weights=[2., 1.]),
      {'overall_mae': 2.0, 'horizon_mae': [1.5, 3.0], 'counts': [2, 2]})
equal(run([[0., 0.], [0., None]], [[2., 8.], [4., None]],
          [[True, True], [True, False]], horizon_weights=[1., 2.]),
      {'overall_mae': 5.5, 'horizon_mae': [3.0, 8.0], 'counts': [2, 1]})
equal(run(t, p, m, horizon_weights=[0., 0.]),
      {'overall_mae': None, 'horizon_mae': [1.5, 3.0], 'counts': [2, 2]})
equal(run([[None]], [[None]], [[False]]),
      {'overall_mae': None, 'horizon_mae': [None], 'counts': [0]})
equal(run([], [], []), {'overall_mae': None, 'horizon_mae': [], 'counts': []})
equal(run([[], []], [[], []], [[], []]),
      {'overall_mae': None, 'horizon_mae': [], 'counts': []})
assert (t, p, m) == saved
assert diagnostics._width([[1, 2]]) == 2

bad = [
    ([[1]], [[1], [2]], [[True]], {}),
    ([[1], [2, 3]], [[1], [2]], [[True], [True]], {}),
    ([[1]], [[1]], [[1]], {}),
    ([[None]], [[1]], [[True]], {}),
    ([[float('nan')]], [[1]], [[True]], {}),
    ([[1]], [[float('inf')]], [[True]], {}),
    ([[True]], [[1]], [[True]], {}),
    ([[1]], [[1]], [[True]], {'horizon_weights': [-1]}),
    ([[1]], [[1]], [[True]], {'horizon_weights': [True]}),
    ([[1]], [[1]], [[True]], {'horizon_weights': [float('nan')]}),
    ([[1]], [[1]], [[True]], {'horizon_weights': [1, 2]}),
    ([], [], [], {'horizon_weights': [1]}),
]
for args in bad:
    try:
        run(*args[:3], **args[3])
    except ValueError:
        continue
    raise AssertionError(('Expected ValueError', args))
print('PASS: numerical consumer, masking, weights, empty inputs and invalid contracts')
