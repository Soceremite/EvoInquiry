# Fixed descriptive comparison

Rows pair baseline and candidate absolute errors on the same sample and horizon.
Each horizon has a fixed weight: near = 2, far = 1. Overall error is the weighted
sum of errors divided by weighted observation counts, not a mean of horizon means.
Lower is better. Report each horizon as well. The rows are a small supplied
descriptive fixture, with no new independent test set or statistical claim.
