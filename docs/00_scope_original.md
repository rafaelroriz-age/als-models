# ALS OIL & LUBRICANTS
## Project Scope — TAT & Volume Forecast
### Freelance data-science engagement

## 1. Purpose

This document sets out what we would like you to build and the context you need to size the effort. We are not asking you to commit to anything yet — just to come back with a proposed approach, the tools you would use, an estimate of the time involved, and any questions you have.

## 2. Company & process context

ALS Oil & Lubricants is a lubricant-analysis and condition-monitoring laboratory. Clients send us oil samples to monitor equipment health, extend oil-drain intervals, and reduce unplanned downtime. Each sample moves through three stages:

- **CRD** — the sample is received and registered. (Registration only; not counted in TAT.)
- **Laboratory** — the sample goes through its tests. First and most time-consuming part of TAT.
- **Interpretation** — results are reviewed and interpreted. Second part of TAT.

Some samples are sent for a retest, looping back through Laboratory and Interpretation. The TAT clock does not reset — the extra time is added on, so retests push that sample's TAT up directly.

A sample goes through several tests (we call these essays, also referred to as analyses). Essays are grouped into workgroups, and workgroups into packages (also called analysis plans). These groupings, along with the lab / site, are the units by which we manage our workload — so the forecast must be producible for any one of them.

## 3. Glossary

| Term | What it means |
|------|---------------|
| TAT | Turnaround Time — total processing time across the Laboratory and Interpretation stages. Runs continuously; does not pause on weekends or holidays. |
| Deadline band | Maximum allowed TAT for a sample (48 / 72 / 96 / 120 h). Fixed per sample by oil type, equipment, compartment and similar attributes — not chosen freely. |
| Met deadline | The sample was completed within its deadline band, measured from the received timestamp. |
| On-time % | Share of samples that met their deadline. Our service target is at least 90% per month. |
| Essay | An individual test run on a sample. Synonyms: analysis, test. |
| Workgroup | A group of essays. |
| Package | A group of workgroups. Synonym: analysis plan. |
| S360 | Our LIMS (Laboratory Information Management System) — the source of the data. |
| The agent | The existing automated system your model plugs into; it calls the model on demand to return forecasts to users. |

## 4. What we want you to build

Standing partway through a period, forecast how that period will finish for a chosen entity — both the TAT / on-time outcome and the sample volume. The forecast updates as the period progresses.

The period is flexible — a day, a week, a month, or a custom range — depending on what the user needs, for both outputs. (The month is our key reference because the 90% on-time target is monthly.) The forecast must also be producible per entity: the whole operation, or a specific lab, package, or workgroup.

### Deliverable & how it will be used

- A model that runs autonomously (not a notebook or manual report), integrated into our existing agent.
- Refreshed on demand: when a user asks the agent, the model pulls the latest data and returns an up-to-date forecast for the requested entity and period.
- Main users are lab managers and operational lab staff, so the output should be simple to read — a clear number plus a sense of confidence — even if the method behind it is sophisticated.

We would define the agent-to-model interface (inputs: entity, as-of date, target period; output: forecast plus uncertainty range) together with you.

## 5. Data you will receive

You will draw from our LIMS, S360. It likely already holds everything you need; if anything is missing, we will provide it based on your requirements. There is no data dictionary — you will need to work out the table structures yourself.

### Expect imperfect data

The data mirrors real records, so plan for missing values, occasional outliers, and a few data-entry errors. Noticing and handling these is part of the work.

Also note: partway through a period, many samples are received but not yet completed, so their final TAT and on-time status are unknown. How you treat these in-progress (censored) samples matters for the forecast.

## 6. Environment & tools

- Language: Python.
- Runs on your own machine; the model is later integrated into our agent.
- Data access: S360 (our LIMS).

## 7. How we will judge success

By forecast accuracy — how close the mid-period forecast is to the actual result. The natural way to show this is backtesting: for past periods, stand at a mid-point using only the data available then, forecast the outcome, and compare. Useful measures: average error on volume (MAE / MAPE); error in percentage points on on-time %, especially whether it correctly flags months at risk of missing 90%; and whether the confidence range you report is well-calibrated.

## 8. What we would like back from you

- Your proposed approach and the tools/libraries you would use.
- An estimate of the time the work would take, with the assumptions behind it.
- Any questions or information you would want before starting.

---

*Confidential.*
