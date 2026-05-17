# Manual playbook — resume from `status: in_progress`

**Purpose:** verify that a `.state.json` with `status: in_progress` and 5 prior iterations triggers the orchestrator's resume prompt described in spec § 7.1.

**Prerequisites:** the generate-prd skill is deployed (`.claude/commands/generate-prd.md` and `.claude/agents/*.md` in place); a working `transcripts/` folder; `$ANTHROPIC_API_KEY` set if you want to actually walk past STEP 0.

## Setup

```bash
# In a clean test workspace, NOT the generate-prd repo root:
mkdir -p prd transcripts
cp /path/to/generate-prd/tests/durability/state-fixtures/in-progress-mid-loop.json prd/.state.json
cp /path/to/generate-prd/tests/golden-corpus/transcripts/* transcripts/
cp /path/to/generate-prd/tests/golden-corpus/glossary.md ./glossary.md
```

## Run

In Claude Code, in this workspace:

```
/generate-prd
```

## Expected behavior

The orchestrator's STEP 0 reads `prd/.state.json`, sees `status: "in_progress"`, and renders the resume prompt verbatim per spec § 7.1:

> *"Found an unfinished discovery session for `loopr-onboarding` (5 iterations, last checkpoint at 2026-05-15T15:47:11Z). **Resume**, **archive and start fresh**, or **cancel**?"*

**Choose `Resume`.** The loop should:
- Skip STEPS 1–4 entirely (already complete per state).
- Enter STEP 5 at iteration 6 (the next critic pass).
- All prior `qa_history`, `themes`, and `draft_sections` are intact and visible in `/status`.

## Pass criteria

- Resume prompt matches the spec wording (feature name + iteration count + checkpoint time fields all interpolated).
- After choosing Resume, the new critic pass is iteration 6 (not 1).
- Typing `/status` shows `iteration_count: 5` (about to increment) and `qa_turn_count: 9` from the fixture.

## On fail

If the orchestrator restarts from STEP 0 instead of resuming, the resume-detection branch in STEP 0 isn't reading `status` correctly. Inspect `generate-prd.md` STEP 0 step 2.

## Capture

If you run this for real, save the chat transcript as `runs/in-progress-resume.txt` for the regression record.
