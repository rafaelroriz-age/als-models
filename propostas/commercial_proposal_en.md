# COMMERCIAL PROPOSAL
## TAT & Volume Forecast — ALS Oil & Lubricants

**Prepared for:** ALS Oil & Lubricants
**Prepared by:** Freelance Data-Science Consultant
**Date:** September 2026
**Proposal validity:** 30 days from the date above

---

## 1. Executive summary

Proposal to build an **autonomous forecast model** that, mid-period, predicts how a chosen period will end for a chosen entity — both **TAT / on-time %** and **sample volume** — updated on demand and exposed through a service consumed by ALS's agent. **Integration with the agent is carried out by ALS.**

The work will be carried out on a **part-time basis**: **4 hours per day**, over **40 business days** (with Brazilian holidays compensated), at a rate of **R$ 30.00/hour**, split into **2 monthly payments of R$ 2,400.00**.

| Item | Value |
|------|-------|
| Daily workload | 4 hours |
| Duration | 40 business days (≈ 8 weeks / 2 months) |
| Total hours | 160 hours |
| Hourly rate | R$ 30.00 |
| **Total investment** | **R$ 4,800.00** |
| **Payment schedule** | **2 monthly installments of R$ 2,400.00** |

---

## 2. Project scope (summary)

The client sends oil samples that pass through three stages: **CRD** (registration), **Laboratory** (testing) and **Interpretation** (review). TAT runs continuously (no pause on weekends/holidays) and re-tests do not reset the clock. The service target is **≥ 90% on-time per month**.

The deliverable covers two forecast targets, over flexible entity and period:

1. **TAT / on-time % outcome** — share of samples completed within their deadline band, with at-risk flagging against the 90% target.
2. **Sample volume** — number of samples processed in the period.

**Entities:** whole operation, laboratory/site, package (analysis plan) or workgroup.
**Periods:** day, week, month (key reference) or custom range.

**Delivery format:** autonomous Python model exposed through a service (endpoint) with a documented interface, returning a clear number + uncertainty interval. **Connection to the existing agent is ALS's responsibility**, which receives the service, the interface definition and the integration documentation.

---

## 3. Technical approach (summary)

| Concern | Proposed choice |
|---------|-----------------|
| Data access | Direct to the S360 LIMS (silver layer) |
| Manipulation | Pandas, numpy |
| Censored TAT | Lifelines (Kaplan-Meier / Cox) or survival model |
| Volume forecast | Statsforecast / prophet / gradient boosting |
| Uncertainty | Conformal prediction / prediction intervals (calibrated) |
| Evaluation | Custom backtesting harness (no future leakage) |
| Service | Directly on ALS infrastructure |
| Tests | Pytest / Great Expectations |

Handling **censored samples** (received but not yet completed mid-period) is central and will be done via survival analysis, not by dropping them.

---

## 4. Engagement terms

- **Regime:** part-time — 4 hours/day, on business days.
- **Duration:** 40 business days, with Brazilian holidays added to the calendar (the deadline extends proportionally).
- **Rate:** R$ 30.00/hour. **Total: 160 h × R$ 30.00 = R$ 4,800.00.**
- **Payment:** **2 monthly installments of R$ 2,400.00** (see §6).
- **Integration:** ALS's responsibility — we deliver the service, the interface and the documentation; ALS connects it to the agent.
- **Communication:** short checkpoints at the end of each milestone + async question channel.

### Brazilian holidays considered in the period

Assuming the proposed start date (05/Oct/2026), the following national holidays fall on business days and are **compensated** in the schedule:

| Holiday | Date | Weekday |
|---------|------|---------|
| Nossa Senhora Aparecida (Our Lady of Aparecida) | 12/Oct/2026 | Monday |
| Finados (All Souls' Day) | 02/Nov/2026 | Monday |
| Dia da Consciência Negra (Black Consciousness Day) | 20/Nov/2026 | Friday |

> Note: Proclamação da República (15/Nov/2026) falls on Sunday and does not affect business days.

### Project window

| Milestone | Date |
|-----------|------|
| Proposed start | 05 October 2026 (Monday) |
| Expected completion | 02 December 2026 (Wednesday) |
| Total calendar span | 59 calendar days (40 business + 3 holidays + weekends) |

---

## 5. Schedule (2 months × 20 business days × 80 hours)

| Month | Focus | Business days | Hours | Window (dates) |
|-------|-------|---------------|-------|----------------|
| **Month 1** | Foundation & data — discovery, features, backtesting | 20 | 80 h | 05/Oct → 03/Nov |
| **Month 2** | Modeling, service & delivery | 20 | 80 h | 04/Nov → 02/Dec |
| **Total** | | **40** | **160 h** | |

### Month 1 — Foundation & data

| Phase | Description | Hours | Business days |
|-------|-------------|-------|---------------|
| Phase 0 — Data discovery & audit | Reverse-engineer S360 schema, sample lifecycle, deadline-band derivation, quality report | 28 h | 7 |
| Phase 1 — Feature & dataset engineering | Period×entity×sample fact tables, volume definition, calendar/hierarchy/workload features | 28 h | 7 |
| Phase 2 — Backtesting harness | Simulate "data available at that point", faithful censoring, metrics (MAE/MAPE, on-time % error, calibration, risk) | 24 h | 6 |

### Month 2 — Modeling, service & delivery

| Phase | Description | Hours | Business days |
|-------|-------------|-------|---------------|
| Phase 3 — Modeling, service & calibration | Baseline, volume model, censored TAT/on-time model, interval calibration, service on ALS infrastructure | 56 h | 14 |
| Phase 4 — Validation & delivery | Backtesting report, calibration validation, documentation, delivery | 24 h | 6 |

---

## 6. Milestones & payment

The project is delivered in **5 milestones**, grouped into **2 billing months** of **R$ 2,400.00** each. Final integration with the agent is carried out by ALS.

### Milestones by month

| # | Milestone | Deliverable | Hours | Business days | Window (dates) | Month |
|---|-----------|-------------|-------|---------------|----------------|-------|
| M1 | Data discovery & audit | S360 data map + quality report + resolved open questions | 28 h | 7 | 05/Oct → 14/Oct | Month 1 |
| M2 | Features & dataset | Fact tables, feature set and approved volume definition | 28 h | 7 | 15/Oct → 23/Oct | Month 1 |
| M3 | Backtesting harness | Working harness + baseline metrics report | 24 h | 6 | 26/Oct → 03/Nov | Month 1 |
| M4 | Modeling, service & calibration | Volume and TAT/on-time models with calibrated intervals (vs. baseline) + service on ALS infrastructure with agent-model interface | 56 h | 14 | 04/Nov → 24/Nov | Month 2 |
| M5 | Validation & delivery | Backtesting report against success criteria + calibration validation + documentation + delivery | 24 h | 6 | 25/Nov → 02/Dec | Month 2 |
| | | | **160 h** | **40** | | |

### Payment plan (2 monthly installments)

| Installment | Period | Milestones covered | Hours | Value |
|-------------|--------|--------------------|-------|-------|
| **Installment 1** | Month 1 (05/Oct → 03/Nov) | M1 + M2 + M3 | 80 h | **R$ 2,400.00** |
| **Installment 2** | Month 2 (04/Nov → 02/Dec) | M4 + M5 | 80 h | **R$ 2,400.00** |
| | | | **160 h** | **R$ 4,800.00** |

**Payment terms:**

- **Installment 1 (R$ 2,400.00):** invoiced at the end of Month 1 (03/Nov), upon delivery and acceptance of milestones M1–M3.
- **Installment 2 (R$ 2,400.00):** invoiced at the end of Month 2 (02/Dec), upon delivery and acceptance of milestones M4–M5.
- Due within 7 calendar days after each invoice is issued.
- Amounts in Brazilian Reais (BRL); consultant's taxes are the consultant's responsibility.

---

## 7. Assumptions & risks

**Key assumptions**

- Access to S360 granted early and reasonably queryable.
- Historical data ≥ 12 months (required for meaningful backtesting).
- Deadline-band attributes present or derivable.
- Entity hierarchy related to samples without excessive cleaning effort.
- ALS performs the agent integration; we deliver a documented, easy-to-consume endpoint/interface.

**Risks & mitigation**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Difficult data discovery (no dictionary) | Schedule | Dedicated Phase 0 + early checkpoint for re-estimation |
| Insufficient historical depth | Backtest quality | Early assessment; methods suited to less data (temporal CV) |
| Ambiguous "volume" definition | Rework | Define with client in M1/M2 |
| Agent-model interface requirements change | Scope | Freeze the interface contract in M4; later changes handled separately |

---

## 8. Out of scope

- **Integration with the existing agent (ALS's responsibility)** — we deliver the service, interface and documentation.
- Team training or ongoing post-delivery support (can be contracted separately).
- Production infrastructure / final service hosting.
- S360 LIMS rework or structural correction of source data.
- Guarantee of hitting the 90% on-time target (the deliverable is the forecast, with accuracy measured via backtesting).

---

## 9. Acceptance

I accept the terms of this proposal:

- Name: ______________________________
- Signature: _________________________
- Date: ____/____/______

---

*Proposal prepared in September 2026. Confidential document — ALS Oil & Lubricants.*
