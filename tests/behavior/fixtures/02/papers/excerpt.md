# Synthetic paper excerpt: Two-bin recalibration
Authors: A. Example and B. Fixture. This is invented evaluation content.
We partition held-out predictions into two confidence bins, fit a scalar
correction per bin, and evaluate on a separate sensor-shift split. Brier score
falls from 0.20 to 0.18 on one simulated shift; on a second shift it rises to
0.22. Accuracy is unchanged. The authors conjecture that representation quality
improves, but do not measure representations. Limits: one model, two shifts,
small calibration set. Calibration samples never include evaluation labels.
