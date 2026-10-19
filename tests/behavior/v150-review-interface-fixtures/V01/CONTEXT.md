# Forecast diagnostics

Complete `diagnose(targets, predictions, observed, *, horizon_weights=None)` in
`src/diagnostics.py`. The consumer is `check.py`; use the standard library only.
The code should be usable by a researcher who did not participate in this session.

Inputs are rectangular N-by-H nested sequences: sample then forecast horizon.
`observed` contains booleans. Targets and predictions at unobserved positions may
be `None`; ignore them entirely. At observed positions require finite real
numbers (not booleans). Do not mutate inputs. Weights default to one per horizon;
an explicit sequence has H finite nonnegative real numbers, excluding booleans.

Return a dictionary with `overall_mae`, `horizon_mae` and `counts`. Counts are the
number of observed pairs per horizon. A horizon with zero observations has MAE
`None`. Overall MAE is the sum of weight[h] times absolute errors, divided by the
sum of weight[h] times counts[h]; when that denominator is zero return `None`.
Zero weights do not remove observations from counts or horizon MAE. Units match
the targets. An empty outer input returns None and two empty lists; explicit
weights must then also be empty. Zero-width rows are allowed. Invalid alignment,
mask values, active values or weights raise `ValueError`.

Keep the existing `_width` helper unchanged. It has a separate consumer.
Run the existing checks and write a short factual handoff. No dataset, training,
dependency change or research claim is needed.
