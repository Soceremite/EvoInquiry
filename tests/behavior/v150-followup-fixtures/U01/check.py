"""Executable behavior checks for the existing utility; no docstring grading."""
from copy import deepcopy

from src.metrics import masked_mean

values = [[[1, 10], [3, 30], [5, 50]], [[2, 20], [4, 40], [6, 60]]]
valid = [[True, False, True], [False, False, False]]
original = deepcopy((values, valid))
assert masked_mean(values, valid) == [[3.0, 30.0], [0.0, 0.0]]
assert masked_mean(values, valid, fill_value=-2) == [[3.0, 30.0], [-2.0, -2.0]]
assert (values, valid) == original
assert masked_mean([[[7]]], [[True]]) == [[7.0]]
for data, mask in (
    ([], []),
    ([[]], [[]]),
    ([[[]]], [[True]]),
    ([[[1], [2, 3]]], [[True, True]]),
    (values, [[True]]),
    ([[[1]], [[2], [3]]], [[True], [True, False]]),
):
    try:
        masked_mean(data, mask)
    except ValueError:
        pass
    else:
        raise AssertionError('Expected ValueError for an invalid shape')
print('Behavior checks passed')
