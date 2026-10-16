# Regression evaluation

Eight held-out cases, same inputs and original kWh units across both frozen
models. Primary metric: mean absolute error (lower better). Secondary metric:
mean squared error (kWh squared, lower better). The high-demand slice was
specified as target >=100 kWh before these predictions. One model run per
method; no interval estimates, raw input features or training repeats exist.
The CSV is the complete available pool. A residual is prediction minus target.
