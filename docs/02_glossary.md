# Glossary

| Term | Meaning |
|------|---------|
| TAT | Turnaround Time — total processing time across Laboratory + Interpretation stages. Runs continuously; does not pause on weekends/holidays. |
| Deadline band | Maximum allowed TAT for a sample (48 / 72 / 96 / 120 h). Fixed per sample by oil type, equipment, compartment, etc. — not chosen freely. |
| Met deadline | Sample completed within its deadline band, measured from received timestamp. |
| On-time % | Share of samples that met their deadline. Service target: ≥ 90% per month. |
| Essay | An individual test run on a sample. Synonyms: analysis, test. |
| Workgroup | A group of essays. |
| Package | A group of workgroups. Synonym: analysis plan. |
| S360 | The LIMS (Laboratory Information Management System) — source of the data. |
| The agent | Existing automated system the model plugs into; calls the model on demand to return forecasts to users. |
| Censored sample | A sample received but not yet completed mid-period, whose final TAT / on-time status is unknown. |

## Implications for modelling

- **Deadline band is a per-sample attribute**, derived from oil type / equipment / compartment — it is an input, not a free choice.
- **On-time %** is a binary outcome per sample (`TAT <= deadline band`) aggregated over a period.
- **TAT** is a continuous duration measured from received timestamp, spanning Laboratory + Interpretation only.
- **Censoring** is central: mid-period forecasts must handle samples with no completion timestamp yet.
