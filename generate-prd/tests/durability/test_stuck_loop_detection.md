# Manual playbook — stuck-loop fault detection

**Purpose:** verify the orchestrator detects 5 identical critic outputs in a row and writes `status: faulted` with the stuck-loop diagnostic per spec § 7.7.4.

## Why this is adversarial

In normal use, /refine after a discussion changes the draft, which changes what the next critic sees. To trigger stuck-loop:
- The PM must avoid the /refine path so the draft stays byte-identical.
- The PM must repeatedly /skip the same recommended finding without addressing it.

Five iterations of this should fire the fault.

## Setup

```bash
mkdir -p prd transcripts
# Deploy:
cp /path/to/generate-prd/generate-prd.md .claude/commands/
cp /path/to/generate-prd/Agents/*.md .claude/agents/
# Inputs:
cp /path/to/generate-prd/tests/golden-corpus/transcripts/T0[12]* transcripts/
```

## Run

```
/generate-prd
```

Walk through STEP 0 → STEP 1 → STEP 2 → STEP 3 → STEP 4 normally.

At iteration 1's discussion (STEP 5.b), type `/skip` instead of engaging the finding.
Repeat the same `/skip` at iterations 2, 3, 4, 5. **Do not type `/refine`. Do not type any free-form text** — those would change the draft or the qa_history and break the test condition.

## Expected behavior

At the start of iteration 6 — or at iteration 5's checkpoint, depending on implementation precision — the orchestrator should:
1. Detect that the last 5 critic-pass `output_hash` values are identical.
2. Write `prd/.state.json` with `status: "faulted"`, `fault: { type: "stuck_loop", iteration, diagnostic: "Critic returned identical findings 5 iterations in a row" }`.
3. Surface the diagnostic to the PM, with the three choices from spec § 7.7.4:
   - **Finalize anyway**
   - **Pivot the discussion** (PM picks a section/topic)
   - **Report a bug** (exit with the diagnostic)

## Pass criteria

After the 5th `/skip`:
- `cat prd/.state.json | jq .status` → `"faulted"`
- `cat prd/.state.json | jq .fault.type` → `"stuck_loop"`
- `cat prd/.state.json | jq .fault.diagnostic` → contains the phrase "identical findings 5 iterations"
- The orchestrator's next message presents the 3 choice options verbatim.

## On fail

If the loop continues past iteration 5 without firing the fault, the stuck-loop detection isn't hashing critic outputs or the comparison window is wrong (look at STEP 5.a step 6 in `generate-prd.md`).

If the fault is detected but the diagnostic is empty, the orchestrator wrote `state.fault` without populating its fields — inspect the structure of the write in STEP 5.a step 6.

## Capture

Save the chat transcript to `runs/stuck-loop-detection.txt` AND save the final `prd/.state.json` as `state-fixtures/stuck-loop-from-real-run.json` (compare to the synthetic `faulted-stuck-loop.json` for parity).
