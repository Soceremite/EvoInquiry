# Declared comparison and retention budget

All 13 held-out IDs in predictions.csv are planned for both frozen methods.
The candidate has no output for s13 after an evaluation failure; the original
failure record is failure.txt. No replacement or new inference is allowed.
The primary accuracy denominator is all planned cases only when complete;
otherwise report available-case accuracy separately from coverage. Do not
invent a prediction or silently count a missing output as correct, incorrect,
or excluded by design. Matched sample-level contrasts use the available pairs.

Storage is tight: reuse CSV references and a small text report. Do not copy
input data, retain new model weights, delete evidence or render large media.
Use sample IDs and actual label predictions to trace cases. The CSV values
and failure record are the only available sample-level evidence.
