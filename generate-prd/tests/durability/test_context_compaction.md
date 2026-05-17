# Manual playbook — context-window auto-compaction (Tier 1)

**Purpose:** verify spec § 7.9 Tier 1 (auto-compaction at ~70% of context window) actually triggers in a long unbounded session and that the loop continues seamlessly afterward.

## Why this is hard to automate

Tier 1 compaction depends on cumulative in-context tokens, which depends on the model's actual context budget at runtime, which depends on the harness. There's no reliable way to simulate "70% context full" without a live, long-running session.

This playbook is therefore *manual*. The static-structure test in `test_durability_static.py` covers the documentation contract (the orchestrator's § 7.9 must describe both tiers); this playbook covers the behavioral contract.

## Setup

```bash
mkdir -p prd transcripts
cp /path/to/generate-prd/generate-prd.md .claude/commands/
cp /path/to/generate-prd/Agents/*.md .claude/agents/
cp /path/to/generate-prd/tests/golden-corpus/transcripts/* transcripts/
cp /path/to/generate-prd/tests/golden-corpus/glossary.md ./glossary.md
```

## Run — accumulate context volume

```
/generate-prd
```

Answer the feature-name prompt with `compaction-test`. Walk normally through STEPS 1-4.

In STEP 5, force the loop to accumulate Q&A volume without ending:
- At every iteration, /refine after the discussion (drives the draft to evolve, which keeps the critic finding fresh things).
- Engage every finding with 3-5 free-form turns of follow-up discussion before the /refine.
- Repeat for ~25-30 iterations. The threshold trigger depends on the model's context limit; this is the rough volume needed for Opus 4.7.

## Expected behavior

At some iteration N where cumulative qa_history + transcripts + themes + draft approaches 70% of the model's context limit:
1. The orchestrator detects the threshold (per § 7.9 Tier 1).
2. Generates a compacted "Discovery so far" summary block (~500 tokens) for the oldest `qa_history` turns, keeping the last 3-5 verbatim.
3. Drops the verbatim old turns from the working context.
4. **Critically:** `prd/.state.json` and `prd/.qa_history.md` on DISK remain untouched. Compaction is in-memory only.
5. The loop continues at iteration N+1 with the compacted context.

## Pass criteria

- The compaction is announced or visible (some orchestrator message indicates a compaction happened — or, at minimum, the iteration continues without errors when context volume would otherwise have exceeded the model limit).
- On disk: `prd/.state.json` still has the full `qa_history` (no truncation).
- The next critic pass after compaction still references prior themes by ID and prior decisions by content — i.e., the compacted summary preserved enough signal to continue useful discovery.

## Pass criteria for Tier 2 (rare)

If compaction is insufficient (Tier 1 ran ~3 times and the loop is still hitting the threshold), the orchestrator should:
1. Write `state.status = "paused"`, `state.fault = { type: "context_carryover", diagnostic: "Tier-1 compaction insufficient" }`.
2. Surface the Tier-2 message verbatim per spec § 7.9.
3. Exit cleanly. Next run resumes with the compacted summary + last 3-5 turns loaded fresh.

## On fail

- If the loop dies with a hard "context length exceeded" error: Tier 1 compaction isn't firing. Inspect § 7.9 in `generate-prd.md`.
- If `prd/.state.json` is truncated after compaction: compaction is mutating on-disk state, which violates the invariant. Compaction must be in-memory only.
- If after compaction the critic produces obviously wrong findings (e.g. flags themes that were resolved 10 iterations ago): the summary is dropping too much signal. Adjust the compaction prompt to retain section-by-section conclusions.

## Capture

Save the chat transcript to `runs/context-compaction.txt`.
Snapshot `prd/.state.json` before and after compaction; diff them — only `last_checkpoint_at` should change.
