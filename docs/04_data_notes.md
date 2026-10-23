# Data Notes (S360)

## Source

- **S360** — the LIMS, source of truth.
- Likely holds everything needed; if anything is missing, client will provide it per our requirements.
- **No data dictionary** — we must reverse-engineer the table structures ourselves.

## Expected data quality issues

- Missing values
- Occasional outliers
- Data-entry errors
- → Noticing and handling these is part of the work.

## Censoring (critical modelling consideration)

Mid-period, many samples are received but not yet completed. Their final TAT and on-time status are unknown. How these in-progress (censored) samples are treated materially affects the forecast.

Censored samples must be handled with a principled approach — e.g., survival analysis, expected-completion estimates, or explicit "at-risk" modelling — rather than dropped or assumed complete.

## Data elements to discover in S360

- Sample ID and received timestamp (CRD).
- Completion timestamps per stage (Laboratory, Interpretation).
- Retest events / loops.
- Deadline band per sample (or the attributes needed to derive it: oil type, equipment, compartment).
- Essay → workgroup → package hierarchy mapping.
- Lab / site identifier.

## Data discovery plan

1. Explore table list and schemas in S360.
2. Trace a sample's lifecycle end-to-end through the tables.
3. Confirm the hierarchy joins (essays → workgroups → packages → lab).
4. Confirm deadline-band derivation.
5. Build an initial quality report (missingness, outliers, timestamp sanity).
