"""Forecast diagnostics over samples and horizons; masked positions are omitted.

The module supports weighted overall and unweighted per-horizon absolute errors.
"""


def _width(rows):
    return len(rows[0]) if rows else 0


def diagnose(targets, predictions, observed, *, horizon_weights=None):
    raise NotImplementedError
