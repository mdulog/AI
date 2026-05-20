# Manual playbook — resume from `status: paused`

**Purpose:** verify a `.state.json` with `status: paused` triggers the paused-variant resume prompt per spec § 7.1.

## Setup

```bash
mkdir -p prd transcripts
cp /path/to/generate-prd/tests/durability/state-fixtures/paused-after-iteration-3.json prd/.state.json
cp /path/to/generate-prd/tests/golden-corpus/transcripts/T0[1-3]* transcripts/
# Only T01-T03 — match the fixture's input_transcripts list
```

## Run

```
/generate-prd
```

## Expected behavior

STEP 0 reads `status: "paused"` and renders (per spec § 7.1):

> *"Found an unfinished discovery session for `loopr-onboarding` (3 iterations, last checkpoint at 2026-05-14T10:33:55Z). **Resume**, **archive and start fresh**, or **cancel**?"*

(Note: spec § 7.1 uses the same prompt for `in_progress` and `paused` — they're both "unfinished" sessions. The orchestrator does NOT need to disambiguate them in the prompt wording.)

**Choose `Resume`.** The loop should:
- Skip STEPS 1–4 (already complete per state).
- Enter STEP 5 at iteration 4 (the next critic pass).
- Crucially, `state.status` flips from `paused` back to `in_progress` on the next checkpoint write.

## Pass criteria

- Resume prompt fires (NOT the fresh-run feature-name prompt).
- After Resume, next critic pass is iteration 4.
- After the first checkpoint write following Resume, `prd/.state.json` shows `"status": "in_progress"` (the run is no longer paused).

## On fail

If the orchestrator offers the fresh-run setup prompt or asks for a new `feature_name`, the resume branch isn't matching `paused`. Both `in_progress` and `paused` should route to the same resume prompt per spec § 7.1.

## Capture

Save the chat transcript to `runs/paused-resume.txt` for the regression record.
