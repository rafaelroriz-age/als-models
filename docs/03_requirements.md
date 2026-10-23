# Functional Requirements

## Core requirement

Standing partway through a period, forecast how that period will finish for a chosen entity:

1. **TAT / on-time outcome**
2. **Sample volume**

The forecast updates as the period progresses.

## Interface contract (to be defined jointly)

| Field | Type | Notes |
|-------|------|-------|
| entity | input | whole operation / lab / package / workgroup |
| as-of date | input | the "mid-period" standpoint |
| target period | input | day / week / month / custom range |
| forecast | output | the predicted number(s) |
| uncertainty range | output | confidence / interval |

## Non-functional / deliverable requirements

- **Autonomous** — runs as a service, not a notebook or manual report.
- **Integrated** — plugs into the existing agent.
- **On-demand refresh** — pulls latest data from S360 when asked.
- **Simple output** — a clear number + confidence, readable by lab managers and operational staff.
- **Language** — Python.
- **Runtime** — runs on the freelancer's machine during development; later integrated into the agent.

## Assumptions to validate (open questions)

1. What exactly does "volume" count — received, completed, or both? (per entity/period)
2. Which timestamps exist in S360 (received, lab start/end, interpretation end, retest events)?
3. How is the deadline band stored/derived per sample?
4. Is entity (lab / package / workgroup) directly joinable to samples in S360?
5. Is there historical data volume sufficient for backtesting (how many months/years)?
