# Queueing research context

This is a synthetic offline engineering project. We are interested in reducing
waiting time for heterogeneous requests served in small batches, but have not
chosen a research question or a method. We have one CPU and no authorized GPU,
external service, dataset download, or training budget. We can inspect small
local traces and later write a simulator if a specific question warrants it.

The trace below is an invented illustration, not a measured service benchmark.
Request time, duration and waiting time would be in milliseconds. There is no
evidence yet about how often this pattern occurs in a real workload.

| request | arrival | known processing duration |
| --- | ---: | ---: |
| a | 0 | 12 |
| b | 1 | 2 |
| c | 2 | 2 |
| d | 3 | 8 |

The initial direction is “better queueing for batch inference.” A proposed rule
could improve average waiting time while hurting a tail or a request class.
The actual workload and which tradeoff matters remain open questions.
