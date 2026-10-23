# Project Overview

## One-line summary

Build an autonomous forecasting model that, standing mid-period, predicts how a chosen period will finish for a chosen entity — both **TAT / on-time outcome** and **sample volume** — refreshed on demand via an existing agent.

## The two forecast targets

| Output | Definition | Key reference |
|--------|-----------|---------------|
| TAT / on-time outcome | Share of samples completed within their deadline band | 90% on-time target is monthly |
| Sample volume | Number of samples processed in the period | Day / week / month / custom range |

## Period flexibility

- Day, week, month, or custom range.
- Month is the key reference because the 90% target is monthly.

## Entity flexibility

The forecast must be producible for any of:
- The whole operation
- A specific lab / site
- A specific package (analysis plan)
- A specific workgroup

## Key inputs & outputs

**Inputs:** entity, as-of date, target period.
**Output:** forecast plus uncertainty range.

## The workflow (3 stages per sample)

1. **CRD** — received and registered (not counted in TAT).
2. **Laboratory** — tests run (first, most time-consuming part of TAT).
3. **Interpretation** — results reviewed (second part of TAT).

Retests loop back through Laboratory + Interpretation and **do not reset** the TAT clock — they push TAT up directly.

## Hierarchy of groupings

```
Sample → Essays (tests/analyses) → Workgroups → Packages (analysis plans) → Lab / Site → Operation
```

## Deliverable shape

- Autonomous model (not a notebook / manual report), integrated into the existing agent.
- Refreshed on demand when a user asks the agent.
- Simple, readable output: a clear number + confidence, for lab managers and operational staff.
