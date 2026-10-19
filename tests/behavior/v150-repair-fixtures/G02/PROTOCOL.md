# Metric definitions

Only rows with actual_mask=true are eligible for masked_exact. For each eligible row the masked positions must all match; unmasked rows are excluded, not counted as success. Report successes, eligible count and ratio. token_accuracy uses all supplied token positions across all rows. The selection is fixed; no resampling or invented examples. Empty eligible populations must be reported as undefined with count zero.
