# Expected Themes — Golden Corpus

This document captures the themes a correct `generate-prd` run should surface from the five-transcript golden corpus. It is the human-readable ground truth used during prompt tuning (Task 4.5) and as a regression checkpoint for v2.0.

## Theme inventory

### Onboarding friction — PRIMARY pain (4 or 5 / 5 transcripts)
The high-frequency theme. Appears explicitly in:
- **T01** — CSV import header validation; "biggest objection"
- **T02** — discoverability ("where is X" moments) in the first week
- **T03** — verbatim: "The onboarding piece is what's killing us"
- **T04** — onboarding new drivers; "friction is real"
- **T05** — explicitly called out as "the #1 complaint"

The PRD should treat onboarding friction as the dominant problem statement.

### Workflow speed — SECONDARY (~3 / 5)
- **T02** — primary thesis of the call; latency, bulk ops, would churn over it
- **T03** — acknowledged as a baseline expectation but not a blocker
- **T05** — "2 of 5" attendees mentioned; trending but below onboarding

Should appear in the PRD as a clear-but-not-headline requirement.

### Pricing — CONTRADICTION (must be surfaced, not averaged away)
- **T01 (Acme Logistics, Dan Reyes):** "$50/seat is fine" — explicit ceiling that doesn't trigger procurement.
- **T04 (Riverstone Couriers, Kenji Okafor):** "Free is the only acceptable price. If you charge per seat, even five dollars a seat, we won't adopt."

These are **diametrically opposed** statements about per-seat pricing from two different customer segments (mid-market vs. sole-operator). A correct synthesis must:
1. Flag the contradiction explicitly rather than picking one or averaging.
2. Attribute each position to its source transcript.
3. Optionally recommend segmentation (per-seat for mid-market, free tier for solo/small operators).

This is the unambiguous target for the Phase 4 critic.

### Compliance (SOC2 / HIPAA) — LOW-FREQUENCY OUTLIER (1 / 5)
- **T03** — gating requirement for Helios Health Logistics; appears in summary AND two verbatim quotes.

Appears in exactly one transcript. The PRD should mention it but NOT promote it to a top-tier requirement on the strength of one source. It is the "is the system properly weighting frequency vs. salience" test — compliance is high-salience in T03 but low-frequency overall.

### Glossary application
- **T05** uses the misspelling "Looper" throughout. After normalization with `glossary.md` (`Looper: Loopr`), all instances should read "Loopr". The normalized T05 file is the verification artifact.

## What a passing PRD looks like

A correctly synthesized PRD from this corpus should:

1. Lead with onboarding friction as the primary problem (5/5 coverage).
2. Include workflow speed as a secondary problem (3/5 coverage).
3. Flag the pricing contradiction explicitly, with citations to T01 and T04.
4. Mention compliance as a constraint for a specific customer segment (T03), not as a universal requirement.
5. Show no occurrences of "Looper" — the glossary substitution succeeded.

A failing PRD will typically:
- Average the pricing positions into a vague "customers want fair pricing" requirement.
- Inflate compliance into a headline requirement based on one passionate source.
- Miss onboarding because it's distributed across all five transcripts rather than concentrated in one.
- Leave "Looper" in the synthesis output.
