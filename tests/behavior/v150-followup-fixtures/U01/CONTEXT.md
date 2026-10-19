# Existing scientific utility

Implement `masked_mean(values, valid, fill_value=0.0)` in `src/metrics.py` using
the standard library. This is one small modification, not a new prototype campaign.

`values` is a nonempty rectangular nested numeric sequence with axes batch,
time and feature (`B, T, D`). `valid` is a rectangular boolean sequence (`B, T`);
True includes that time step for every feature. Return floating-point feature
means over valid time steps for each batch item, shaped (`B, D`). An all-invalid
item returns `fill_value` in each feature. Do not mutate either input. Empty or
ragged axes and a mismatched mask must raise ValueError.

Run `python check.py`. Keep that existing check unchanged; write a concise
REPORT.md with the actual check and any remaining limits. Only the utility and
report are writable. No dependency or runtime-state setup is needed.
