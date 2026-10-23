# Success Criteria & Evaluation

## Primary judge: forecast accuracy

How close the **mid-period forecast** is to the **actual result**.

## Evaluation method: backtesting

For past periods, stand at a mid-point using only data available then, forecast the outcome, and compare to what actually happened.

## Metrics

| Output | Metric |
|--------|--------|
| Volume | MAE / MAPE (average error) |
| On-time % | Error in percentage points, especially whether it correctly flags months at risk of missing 90% |
| Confidence range | Calibration — reported uncertainty should be well-calibrated |

## What "well-calibrated" means in practice

A 90% confidence range should contain the actual result ~90% of the time across backtests. This is a key differentiator and will be explicitly checked.

## Risk-flagging emphasis

Correctly flagging months at risk of falling below the 90% on-time target is worth at least as much as point-accuracy. The evaluation should track precision/recall of "at-risk" flags, not just raw error.

## Backtesting design implications

- Must simulate "only data available then" — no look-ahead leakage.
- Must reproduce censoring faithfully (drop completion info for samples not yet done at the as-of point).
- Should run across many periods and entities to get stable error estimates.
