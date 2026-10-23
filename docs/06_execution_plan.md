# Execution Plan

> Proposed approach, tools, and effort estimate for the ALS TAT & Volume Forecast engagement.

## Proposed approach (summary)

A **two-output forecasting model** behind a thin service layer:

1. **Volume** — time-series forecast (samples per period) by entity, with calendar features.
2. **TAT / on-time %** — completion-time model with explicit censoring handling (survival-style), aggregated to on-time % per period, plus an at-risk flag vs the 90% target.

Both wrapped with **uncertainty ranges**, validated via **backtesting**, and exposed through a **Python service** the agent can call.

## Proposed tools / libraries

| Concern | Choice | Why |
|---------|--------|-----|
| Data access | SQLAlchemy / direct driver to S360 | pull data on demand |
| Data wrangling | pandas, numpy | standard |
| Censored TAT | `lifelines` (Kaplan-Meier / Cox) or explicit survival model | handles in-progress samples correctly |
| Volume forecast | `statsforecast` / `prophet` / gradient boosting | robust, uncertainty built-in |
| Uncertainty | conformal prediction or prediction intervals | calibrated ranges (a stated success criterion) |
| Evaluation | custom backtest harness | simulates "data available then" |
| Service | FastAPI | agent can call a clean endpoint |
| Testing | pytest | regression safety |

## Work phases & tasks

### Phase 0 — Discovery & data audit (first, before committing)
- Explore S360 schema; reverse-engineer tables.
- Confirm sample lifecycle, timestamps, deadline-band derivation, hierarchy joins.
- Build data-quality report (missingness, outliers, timestamp sanity).
- **Output:** data map + open questions resolved.

### Phase 1 — Feature & dataset engineering
- Build the "period x entity x sample" fact tables.
- Define volume target (received vs completed) with client.
- Engineer features: calendar, entity hierarchy, retest counts, workload indicators.

### Phase 2 — Backtesting harness (build before models)
- Reproduce censoring faithfully at each as-of point.
- No look-ahead leakage.
- Metrics: MAE/MAPE (volume), on-time % error, at-risk precision/recall, calibration.

### Phase 3 — Modelling
- Baseline: naive (last-period volume; running on-time %) to beat.
- Volume model with uncertainty.
- TAT/on-time model with censoring handling.
- Calibrate confidence ranges.

### Phase 4 — Service & integration
- FastAPI endpoint: (entity, as-of date, target period) → forecast + range.
- Simple human-readable output.
- Define agent-to-model interface jointly with client.

### Phase 5 — Validation & handoff
- Backtest report vs success criteria.
- Documentation of assumptions and limitations.
- Handoff to agent integration.

## Effort estimate (assumptions)

| Phase | Estimate |
|-------|----------|
| Phase 0 — Discovery & data audit | 2–3 days |
| Phase 1 — Feature engineering | 2–3 days |
| Phase 2 — Backtesting harness | 2–3 days |
| Phase 3 — Modelling + calibration | 4–6 days |
| Phase 4 — Service & integration | 2–3 days |
| Phase 5 — Validation & handoff | 1–2 days |
| **Total** | **~13–20 working days** |

**Key assumptions:**
- S360 data access is granted early and is reasonably queryable.
- Historical data spans ≥ 12 months (needed for meaningful backtesting).
- Deadline-band attributes are present or derivable.
- Entity hierarchy is joinable to samples without major data wrangling.
- The agent integration point is a simple request/response API.

> Effort scales if data discovery is hard, historical depth is thin, or integration requires more than a plain endpoint.

## Open questions for the client

1. Exact definition of "volume" (received vs completed)?
2. Which timestamps exist in S360 for each stage + retests?
3. How is the deadline band stored/derived?
4. Historical depth available for backtesting?
5. What does the agent-to-model interface look like today (sync HTTP, message queue)?
6. Preferred deployment environment for the service during handoff?
