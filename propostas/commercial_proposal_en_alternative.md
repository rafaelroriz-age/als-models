# COMMERCIAL PROPOSAL (ALTERNATIVE)
## TAT & Volume Forecast — ALS Oil & Lubricants

**Prepared for:** ALS Oil & Lubricants
**Prepared by:** Freelance Data-Science Consultant
**Date:** September 2026
**Proposal validity:** 30 days from the date above
**Alternative proposed start:** 19 October 2026

---

## 1. Executive summary

Proposal to build an **autonomous forecast model** that, mid-period, predicts how a chosen period will end for a chosen entity — both **TAT / on-time %** and **sample volume** — updated on demand and exposed through a service consumed by ALS's agent. **Integration with the agent is carried out by ALS.**

The work will be carried out on a **part-time basis**: **4 hours per day**, over **40 business days** (with Brazilian holidays compensated), at a rate of **R$ 30.00/hour**, split into **2 payments of R$ 2,400.00**.

| Item | Value |
|------|-------|
| Daily workload | 4 hours |
| Duration | 40 business days (≈ 8 weeks) |
| Total hours | 160 hours |
| Hourly rate | R$ 30.00 |
| **Total investment** | **R$ 4,800.00** |
| **Payment schedule** | **2 installments of R$ 2,400.00** |

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
- **Payment:** **2 installments of R$ 2,400.00** (see §6).
- **Integration:** ALS's responsibility — we deliver the service, the interface and the documentation; ALS connects it to the agent.
- **Communication:** short checkpoints at the end of each milestone + async question channel.

### Brazilian holidays considered in the period

Assuming the proposed start date (19/Oct/2026), the following national holidays fall on business days and are **compensated** in the schedule:

| Holiday | Date | Weekday |
|---------|------|---------|
| Finados (All Souls' Day) | 02/Nov/2026 | Monday |
| Dia da Consciência Negra (Black Consciousness Day) | 20/Nov/2026 | Friday |

> Note: Proclamação da República (15/Nov/2026) falls on Sunday and does not affect business days.

### Project window

| Milestone | Date |
|-----------|------|
| Proposed start | 19 October 2026 (Monday) |
| Expected completion | 15 December 2026 (Tuesday) |
| Total calendar span | 58 calendar days (40 business + 2 holidays + weekends) |

---

## 5. Schedule (2 stages × 20 business days × 80 hours)

| Stage | Focus | Business days | Hours | Window (dates) |
|-------|-------|---------------|-------|----------------|
| **Stage 1** | Foundation & data — discovery, features, backtesting | 20 | 80 h | 19/Oct → 16/Nov |
| **Stage 2** | Modeling, service & delivery | 20 | 80 h | 17/Nov → 15/Dec |
| **Total** | | **40** | **160 h** | |

### Stage 1 — Foundation & data

| Phase | Description | Hours | Business days |
|-------|-------------|-------|---------------|
| Phase 0 — Data discovery & audit | Reverse-engineer S360 schema, sample lifecycle, deadline-band derivation, quality report | 28 h | 7 |
| Phase 1 — Feature & dataset engineering | Period×entity×sample fact tables, volume definition, calendar/hierarchy/workload features | 28 h | 7 |
| Phase 2 — Backtesting harness | Simulate "data available at that point", faithful censoring, metrics (MAE/MAPE, on-time % error, calibration, risk) | 24 h | 6 |

### Stage 2 — Modeling, service & delivery

| Phase | Description | Hours | Business days |
|-------|-------------|-------|---------------|
| Phase 3 — Modeling, service & calibration | Baseline, volume model, censored TAT/on-time model, interval calibration, service on ALS infrastructure | 56 h | 14 |
| Phase 4 — Validation & delivery | Backtesting report, calibration validation, documentation, delivery | 24 h | 6 |

---

## 6. Milestones & payment

The project is delivered in **5 milestones**, grouped into **2 billing stages** of **R$ 2,400.00** each. Final integration with the agent is carried out by ALS.

### Milestones by stage

| # | Milestone | Deliverable | Hours | Business days | Window (dates) | Stage |
|---|-----------|-------------|-------|---------------|----------------|-------|
| M1 | Data discovery & audit | S360 data map + quality report + resolved open questions | 28 h | 7 | 19/Oct → 27/Oct | Stage 1 |
| M2 | Features & dataset | Fact tables, feature set and approved volume definition | 28 h | 7 | 28/Oct → 06/Nov | Stage 1 |
| M3 | Backtesting harness | Working harness + baseline metrics report | 24 h | 6 | 09/Nov → 16/Nov | Stage 1 |
| M4 | Modeling, service & calibration | Volume and TAT/on-time models with calibrated intervals (vs. baseline) + service on ALS infrastructure with agent-model interface | 56 h | 14 | 17/Nov → 07/Dec | Stage 2 |
| M5 | Validation & delivery | Backtesting report against success criteria + calibration validation + documentation + delivery | 24 h | 6 | 08/Dec → 15/Dec | Stage 2 |
| | | | **160 h** | **40** | | |

### Payment plan (2 installments)

| Installment | Period | Milestones covered | Hours | Value |
|-------------|--------|--------------------|-------|-------|
| **Installment 1** | Stage 1 (19/Oct → 16/Nov) | M1 + M2 + M3 | 80 h | **R$ 2,400.00** |
| **Installment 2** | Stage 2 (17/Nov → 15/Dec) | M4 + M5 | 80 h | **R$ 2,400.00** |
| | | | **160 h** | **R$ 4,800.00** |

**Payment terms:**

- **Installment 1 (R$ 2,400.00):** invoiced at the end of Stage 1 (16/Nov), upon delivery and acceptance of milestones M1–M3.
- **Installment 2 (R$ 2,400.00):** invoiced at the end of Stage 2 (15/Dec), upon delivery and acceptance of milestones M4–M5.
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
