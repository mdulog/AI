# Manual playbook — holistic critic accuracy on the golden corpus

**Purpose:** confirm the critic's behavior on a real loop run is acceptable BEFORE the skill is treated as v1-shipped. Static prompt checks (Phase 1) and planted-fixture checks (Tasks 4.1-4.4, 4.6) verify the critic *can* detect each finding type and *won't* signal closure. This playbook is the holistic review — does the critic produce a sensible findings list end-to-end on a realistic corpus?

## Pass criteria (human review)

- ✅ No false negatives on planted themes: the pricing CONTRADICTION (T01 vs T04) MUST appear; the COVERAGE_GAP for low-frequency themes (compliance, 1/5) should NOT be incorrectly raised as a primary gap.
- ✅ No more than 1-2 trivial false positives per iteration. A false positive is a finding that, when discussed with a PM, the PM would say "that's not actually a problem."
- ✅ The recommended starting point is reasonable — a human PM reviewing the findings would likely choose the same one, or a sibling.
- ✅ Closure-signal discipline holds across the full session: no "looks done", "ready to finalize", etc.

## Setup

```bash
mkdir -p prd transcripts
cp /path/to/generate-prd/generate-prd.md .claude/commands/
cp /path/to/generate-prd/Agents/*.md .claude/agents/
cp /path/to/generate-prd/tests/golden-corpus/transcripts/* transcripts/
cp /path/to/generate-prd/tests/golden-corpus/glossary.md ./glossary.md
```

## Run

```
/generate-prd
```

Answer the feature-name prompt with `loopr-onboarding`. Walk through STEPS 1-4 (normalize, distill, cluster, initial draft).

Engage the discovery loop for at least 5 iterations. Vary your behavior: address some findings with /refine, skip some with /skip, ask follow-up free-form questions on at least 2 findings.

## What to record

For each iteration, save:
- The full critic output (paste into `runs/critic-holistic-iter-N.md`).
- The recommended starting point.
- Your subjective rating per finding: ✅ valid, ⚠️ trivial-but-not-wrong, ❌ false positive.

## After 5 iterations, score the run

Compute:
- **False-negative count:** planted themes from `expected/themes-summary.md` that NEVER appeared as a critic finding across the 5 iterations.
- **False-positive rate:** ❌ count ÷ total findings.
- **Recommended-starting-point agreement:** out of 5 iterations, how many times you'd have picked the same finding.
- **Closure discipline:** boolean — did the critic ever drift into closure language?

## Acceptance thresholds (initial; revise after first run)

| Metric | Target | If worse |
|---|---|---|
| False-negative count over 5 iterations | 0 on planted CONTRADICTION; 0 on COVERAGE_GAP for high-frequency themes | Iterate `prompts/critic-pass.md` to sharpen the relevant finding-type definition |
| False-positive rate per iteration | ≤ 2 trivial false positives; 0 confident false positives | Iterate the prompt to tighten the relevant finding-type's threshold |
| Recommended-starting-point agreement | ≥ 3/5 | Iterate the recommended-starting-point selection rule in the prompt |
| Closure-signal discipline | strict pass — zero closure phrases over the entire run | Iterate the DO-NOT clauses in `prompts/critic-pass.md` |

## If the critic fails

1. Edit `generate-prd/prompts/critic-pass.md` (and only that file).
2. Re-run the full pytest suite to confirm Phase 1 static tests still pass.
3. Re-run THIS playbook from scratch on the golden corpus.
4. Document what changed and why in the commit message.

The Phase 4 verification checkpoint requires this playbook to pass at least once before tagging `v1.3-generate-prd` is meaningful. Until then, the tag indicates "static contracts validated"; the holistic check is what makes the critic ready for real PRD work.

## Capture

After acceptance, save:
- `runs/critic-holistic-acceptance.md` — the full session transcript
- `runs/critic-holistic-scoring.md` — your scoring sheet per iteration
- Commit both as part of `test(generate-prd): critic accuracy review on golden corpus`.
