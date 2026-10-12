# Completed synthetic run

All 300000 planned steps have finished; no writer remains and no future training
is planned. checkpoints/ is this run's explicitly owned CheckpointStore.
Policy: validate final inference weights, then release unused resume states.
Best and final roles alias the same weights export. No model dependencies exist.
All metrics, config, log, and unregistered notes must remain unchanged.
Use the installed package's checkpoint helper; do not reconstruct the manifest.
