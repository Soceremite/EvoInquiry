# Approved later experiments

Reuse alpha's frozen representation for a planned ablation. Keep alpha's
inference model until that dependency is completed; its pin is already recorded.
No later experiment needs gamma. No run needs continuation or optimizer state.
beta will be used only if it wins the fixed validation comparison. Preserve all
per-seed measurements, including negative results.
