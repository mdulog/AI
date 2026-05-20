# Manual playbook — resume from `status: faulted` (stuck-loop diagnostic preserved)

**Purpose:** verify a `.state.json` with `status: faulted` and a `fault.type: "stuck_loop"` diagnostic triggers the faulted-variant resume prompt per spec § 7.1, and that the diagnostic is surfaced to the PM verbatim — not silently swallowed.

## Setup

```bash
mkdir -p prd transcripts
cp /path/to/generate-prd/tests/durability/state-fixtures/faulted-stuck-loop.json prd/.state.json
cp /path/to/generate-prd/tests/golden-corpus/transcripts/T0[12]* transcripts/
# Only T01-T02 — match the fixture's input_transcripts list
```

## Run

```
/generate-prd
```

## Expected behavior

STEP 0 reads `status: "faulted"` and renders (per spec § 7.1, faulted variant):

> *"Previous run hit a fault: Critic returned identical findings 5 iterations in a row (iter 5..9). PM /skip'd the recommended finding each time without addressing it. Identical output_hash: sha256:f7a2bd... **Resume with diagnostic surfaced**, **retry the failed step**, or **archive and start fresh**?"*

The diagnostic string MUST appear verbatim — interpolated from `state.fault.diagnostic`. The PM should be able to read what happened.

## Pass criteria

- The faulted-variant prompt fires (NOT the `in_progress` / `paused` variant — different wording per spec § 7.1).
- The `state.fault.diagnostic` value is interpolated into the prompt.
- The three choices presented are exactly: **Resume with diagnostic surfaced**, **Retry the failed step**, **Archive and start fresh**.

### Branch behavior

- **Resume with diagnostic surfaced:** loop continues at iteration 10. The fault marker stays in `state.fault` history (under a sibling `state.fault_history` array on the first checkpoint after resume — append-only). `state.status` flips to `in_progress`. The critic still has a chance to surface the same finding again; the difference is that the PM is now informed.
- **Retry the failed step:** the orchestrator re-runs the critic at iteration 9 inputs only (no state increment) to see if a fresh call breaks the stuck pattern.
- **Archive and start fresh:** the faulted state moves to `prd/.archive/<run_id>/state.json` and a clean run begins. The PM is asked for a new `feature_name`.

## On fail

If the prompt uses the `in_progress` wording, the orchestrator isn't branching on `status: faulted`. Inspect STEP 0 step 2.
If `state.fault.diagnostic` isn't interpolated, the orchestrator is rendering the prompt before reading the fault payload.

## Capture

Save the chat transcript to `runs/faulted-resume.txt`.
