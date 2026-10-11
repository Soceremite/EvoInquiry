# Fixed proposal: calibration under drift
Question: does a two-bin confidence recalibration improve prediction calibration
under an unseen sensor shift? The mechanism claim is that it corrects confidence,
not that it improves representations. Main metric: Brier score (lower is better).
For the initial comparison only, accuracy is reported in results/metrics.csv.
Use held-out calibration data; retain an independent evaluation split. Training
budget, data, and architecture must match before any mechanism attribution.
Scope: one synthetic dataset. No general real-world claim is supported yet.
