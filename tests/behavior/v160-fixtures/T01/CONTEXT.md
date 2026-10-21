# Synthetic trajectory review fixture

A baseline and further closed-form fits were evaluated on held-out synthetic
regression data: five seed groups, two evaluation groups and four variants.
RMSE is lower-is-better. `more_training` recomputes the same closed-form optimum;
it is not an optimizer-duration experiment. `center_intervention` removes the
inference offset; `feature_intervention` adds quadratic capacity where used.
There are 150 evaluation rows per seed/group/variant. This summary lacks sample,
weight and split identities, so do not certify a causal or independent result.

This is an advice/report task using existing results. No run, Goal, experiment,
reviewer call or external service should be initialized for this request.
