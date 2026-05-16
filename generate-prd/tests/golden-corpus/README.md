# Golden Corpus — `generate-prd`

A small, hand-crafted set of customer-discovery transcripts with **known, planted attributes**. Used to validate that the `generate-prd` pipeline correctly ingests heterogeneous raw inputs, normalizes them, extracts themes, and surfaces contradictions.

The corpus is deliberately tiny (5 transcripts) so a human reviewer can hold the whole thing in their head and judge model output against a ground truth they trust.

## Hypothetical product

All transcripts are about **Loopr**, a fictional logistics/dispatch SaaS product. The user persona consuming `generate-prd` is a PM at a mid-market SaaS company; the five conversations are with hypothetical customers and prospects.

## What this corpus tests

The fixtures are designed to exercise four capabilities of the pipeline:

1. **Input-format diversity** — five different raw formats (VTT, Word paste, Granola export, hand-typed notes) hit the normalizer with realistic noise.
2. **Theme-frequency discrimination** — high-frequency (onboarding), mid-frequency (speed), and low-frequency (compliance) themes coexist; the extractor must weight them correctly.
3. **Contradiction detection** — pricing positions in T01 and T04 are diametrically opposed; the critic in Phase 4 must catch this rather than averaging it away.
4. **Glossary substitution** — T05 uses the misspelling "Looper"; after normalization it must read "Loopr".

## File map

| File | Format | Planted attribute(s) |
|---|---|---|
| `transcripts/T01-onboarding-friction.vtt` | VTT (with timestamps) | Onboarding friction (primary theme); **speaker mis-attribution** on one cue (interviewer's question wrapped in customer's `<v>` tag); explicit pricing: **"$50/seat is fine"** |
| `transcripts/T02-workflow-speed.docx-paste.md` | Word-doc paste, no speaker prefixes | **Workflow speed** as primary; heavy disfluency (`um`, `uh`, `I— I mean`); two speakers identifiable only by context; mentions onboarding secondarily |
| `transcripts/T03-compliance-question.granola.md` | Granola-style export (summary + verbatim quotes) | **Compliance (SOC2/HIPAA)** mentioned (low-frequency outlier); onboarding also strongly present; no timestamps |
| `transcripts/T04-contradictory-pricing.vtt` | VTT (with timestamps) | **Direct contradiction of T01 on pricing**: "free is the only acceptable price; if you charge per seat we won't adopt"; also covers onboarding friction |
| `transcripts/T05-handtyped-notes.md` | Hand-typed PM notes (bullets, fragments) | Uses **"Looper"** misspelling (glossary target); no speaker attribution; onboarding as #1 complaint |
| `glossary.md` | Term-substitution table | Single entry: `Looper: Loopr` |
| `expected/themes-summary.md` | Markdown | Human-readable ground truth — themes, frequencies, and the pricing contradiction the pipeline must surface |

## Theme distribution (ground truth)

- **Onboarding friction**: 5 / 5 transcripts (primary pain — high-frequency)
- **Workflow speed**: 3 / 5 (T02 primary, T03 + T05 secondary mentions)
- **Pricing**: 2 / 5 (T01 and T04) — **direct contradiction**
- **Compliance (SOC2/HIPAA)**: 1 / 5 (T03 only) — low-frequency outlier

See `expected/themes-summary.md` for the full ground-truth description.

## Where this corpus is consumed

- **Task 2.8 — Normalizer smoke test.** Runs the normalizer over all five raw inputs and verifies the canonical format (`schema/transcript-format.md`) is produced correctly: VTT cues stripped to side-cars, glossary substitution applied to T05, speaker turns formatted per spec.
- **Task 4.5 — Critic accuracy / prompt tuning.** End-to-end run of the pipeline against this corpus. Human reviewer compares the generated PRD against `expected/themes-summary.md` and tunes prompts until the pricing contradiction is flagged, onboarding leads, and compliance is mentioned but not over-weighted.
- **v2.0 regression.** This corpus becomes the locked-in regression suite for future versions of `generate-prd`. Any change that degrades performance on this corpus is a regression.

## When to add to the corpus

Resist growing this corpus casually. The whole point is that a human can hold it in their head. Add a new fixture only when:

- A real failure mode emerges in production that the existing fixtures don't represent, AND
- The failure can be reduced to a small, hand-crafted transcript with a single planted attribute.

Document the planted attribute in the file map above and update `expected/themes-summary.md`.
