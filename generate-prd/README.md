# generate-prd

> Part of the [Claude Code Skills](../README.md) collection. Sibling skill: [`generate-knowledge-base`](../generate-knowledge-base/README.md) — generates architecture docs and conventions for any codebase.

Turn customer-conversation transcripts into a PRD via an unbounded discovery loop with a critic that questions the draft every iteration.

> **Status:** v1. The skill is deployable and the full discovery loop (normalize → distill → cluster → draft → critic-driven discovery → finalize) is wired end-to-end. Live behavioral validation against real Anthropic API calls has been deferred — see [§ Live validation](#live-validation) below.

---

## What it does

Drop conversation transcripts (any format — Zoom/Teams VTT, Granola export, Word transcript paste, hand-typed notes) into `transcripts/` and run `/generate-prd`. The skill:

1. **Normalizes** every transcript to a canonical speaker-turn format.
2. **Distills** each transcript independently into Problems / Jobs-to-be-done / Pains / Personas / Customer-proposed solutions, with `[T<id>:<timestamp>]` citations.
3. **Clusters** the distillations into cross-transcript themes with frequency counts and contradictions surfaced.
4. **Drafts** a PRD where evidence-anchored sections (Background, Target Users, User Stories, Functional Requirements, Risks) are populated from themes and PM-judgment sections (Goals & Non-Goals, Success Metrics, Constraints, NFR) are deliberately left empty.
5. **Enters a discovery loop** with you. Every iteration: a read-only critic surfaces typed findings; you discuss what to do; the drafter refines the affected section. **No iteration cap. No "are you sure?" prompts. No nudges to finalize.** Closure is yours alone — you type `/done` when you decide.
6. **Finalizes** with a completeness/citations/recommendations report (never silently rewrites).

### Design principle: pure-conversation discovery

The skill **never reads the host project's codebase**. PRDs that consult code drift toward "build what's easy" rather than "build what matters." All discovery is grounded in the transcripts and your judgment. This means `generate-prd` is also project-agnostic — you can run it for product work that has no code yet, or for a feature in a codebase the skill never touches.

The full design rationale is in [`docs/specs/2026-05-15-generate-prd-design.md`](../docs/specs/2026-05-15-generate-prd-design.md) § 2.1.

---

## Install

In the target project root:

```bash
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-prd/generate-prd.md .claude/commands/
cp /path/to/generate-prd/Agents/*.md .claude/agents/
```

For a more detailed walk through with troubleshooting, see [`docs/install.md`](docs/install.md).

---

## Quickstart

1. **Put transcripts in `transcripts/`** at the target project root. Accepted formats: `.vtt`, `.srt`, `.md`, `.txt`. The normalizer handles VTT, docx-paste, Granola summary export, hand-typed notes, and plain markdown.
2. **(Optional) Add `glossary.md`** at the project root for transcription-error fixes. Format: `<original>: <canonical>` per line. Applied as case-insensitive regex preprocessing before any LLM call. Example at [`schema/glossary.md.example`](schema/glossary.md.example).
3. **(Optional) Add `prd-template.md`** at the project root if you want to override the default 9-section template. Otherwise the skill uses [`schema/prd-template.md`](schema/prd-template.md).
4. **Run** in Claude Code: `/generate-prd`.

The skill will ask for a kebab-case `feature_name` (e.g. `loopr-onboarding`), then run STEPS 1-4 sequentially. Once the initial draft is ready it announces:

> *"Initial draft ready at `prd/<feature_name>.md`. Entering discovery loop. Type `/done` when you want to finalize, `/pause` to save and exit, `/status` for a neutral snapshot."*

You're in the loop.

---

## Inside the discovery loop

Each iteration runs three phases: **critic pass → discussion → refine**. You're in the driver's seat for the second one.

### The 7 critic finding types

| Type | What it surfaces |
|---|---|
| `CONTRADICTION` | The draft or your prior answer disagrees with what the transcripts actually said. |
| `COVERAGE_GAP` | A high-frequency theme from the corpus is missing from the PRD. |
| `UNSUPPORTED_ASSUMPTION` | A claim in the draft has no transcript backing and no PM justification. |
| `SOLUTION_BIAS` | A section anchors on an implementation (REST endpoints, React components, specific UI) rather than a capability. |
| `GOAL_METRIC_MISMATCH` | A goal has no matching metric, or a metric has no goal it ties to. |
| `PERSONA_STORY_MISMATCH` | A user story names a persona that wasn't declared in Target Users. |
| `EVIDENCE_THIN` | A section claim cites very few or very weak transcripts relative to the weight it carries. |

### Commands inside the loop

| Type at the prompt | Effect |
|---|---|
| **Empty / Enter** | Discuss the recommended starting point |
| **Number** (e.g. `2`) | Discuss a different finding |
| **Free-form text** | Treat as your answer to the recommended finding (or whatever finding/section your text refers to) |
| `/refine` | Apply the discussion's resolution to the affected PRD section, then continue to the next critic pass |
| `/skip` | Skip the iteration without changing the draft |
| `/status` | Show a neutral snapshot (iterations, Q&A count, sections refined, finding density of last 5 passes, cost estimate) and return to the prompt |
| `/pause` | Save state and exit cleanly |
| `/done` | Exit the loop and proceed to finalize |

### What the skill will NOT do

- It will **never** tell you the PRD looks done. The critic is explicitly forbidden from saying "we're done", "looks complete", "consider finalizing", or any closure phrase.
- It will **never** put a cap on iterations. Iteration count is informational, not a budget.
- It will **never** rank findings as "minor — skip this." All findings are surfaced in source order; the recommended starting point is a *suggestion*, never a verdict.
- It will **never** read your codebase. Discovery is grounded in the transcripts.

### Stuck-loop safety

If the critic returns *byte-identical* findings 5 iterations in a row (the same `output_hash`), the orchestrator writes `status: faulted` with a diagnostic and offers you three choices: **finalize anyway**, **pivot the discussion** (you pick a section/topic), or **report a bug**. This isn't a process budget — it's a sanity check that catches the case where you've stopped engaging the loop without realizing it.

---

## Resuming an interrupted session

Sessions are durable. The orchestrator writes `prd/.state.json` BEFORE every LLM call and AFTER every PM turn — the worst case for any failure is losing one in-flight call.

When you re-run `/generate-prd` and a state file exists, you'll see one of three resume prompts depending on the prior session's status:

- **`in_progress` or `paused`:** *"Found an unfinished discovery session for `<feature>` (`<N>` iterations, last checkpoint at `<time>`). **Resume**, **archive and start fresh**, or **cancel**?"*
- **`faulted`:** the same prompt but with the fault diagnostic surfaced verbatim and "**Resume with diagnostic surfaced**, **retry the failed step**, or **archive and start fresh**" choices.
- **`completed`:** archived silently to `prd/.archive/<run_id>/`; the new run starts fresh.

For a worked example of a paused-and-resumed session, see [`docs/walkthrough.md`](docs/walkthrough.md).

---

## File layout (what the skill produces)

```
./transcripts/                          # Your raw transcripts (any supported format)
./transcripts/.normalized/              # STEP 1 output: canonical normalized markdown + .timestamps.json side-cars
./glossary.md                           # (Optional) Term substitutions you supply
./prd-template.md                       # (Optional) Your override of the default template
./prd/<feature_name>.md                 # The PRD draft — iteratively refined
./prd/.distillations/T<id>.md           # STEP 2 per-transcript distillations
./prd/.themes.md                        # STEP 3 cross-transcript themes
./prd/.qa_history.md                    # Full Q&A log (append-only)
./prd/.state.json                       # Continuous checkpoint (validates against schema/state.schema.json)
./prd/.archive/<run_id>/                # Prior completed/abandoned runs
```

---

## Live validation

The v1 ship validates the skill **statically**: every prompt's contract is documented and tested via Python; every agent's frontmatter parses; every orchestrator dispatch site has a checkpoint-before-call annotation; finding-type definitions are checked for vocabulary distinctness; all state fixtures validate against the schema. Run `pytest generate-prd/tests/` — expect 96 tests in under 200ms, no API calls.

**Behavioral validation against real Anthropic API calls is deferred** to the user's discretion. Two relevant playbooks live under `generate-prd/tests/durability/`:

- `test_critic_holistic.md` — accuracy review on the golden corpus with explicit thresholds (false-negative count, false-positive rate, recommended-starting-point agreement, closure-signal discipline). This is the gate for treating the critic as "ready for real PRD work."
- `test_stuck_loop_detection.md`, `test_context_compaction.md`, `test_resume_*.md` — exercise behavioral paths that require a live run.

Before treating v1 as production-ready for your own use, run the holistic playbook against the golden corpus. The validation harness at `tests/validators/run_prompt.py` is in place if you want to automate parts of it.

---

## Limitations

See the spec for the full list. Quick highlights:

- **No incremental ingestion** — adding transcripts mid-session restarts STEPS 1–3. (Spec § 15.)
- **No audio ingestion** — bring already-transcribed text. (§ 15.)
- **No speaker-role activation in v1** — `speakers:` field is reserved in the normalized format for v2. (§ 8.)
- **Single-user; no concurrent edits** to the same `prd/<feature_name>.md`. (§ 14.)
- The critic's accuracy depends on transcript quality. Garbage in, garbage out — clean transcripts produce sharper findings.

Full out-of-scope list: [spec § 15](../docs/specs/2026-05-15-generate-prd-design.md#15-out-of-scope-for-v1).
Risks: [spec § 14](../docs/specs/2026-05-15-generate-prd-design.md#14-risks).

---

## Relationship to `generate-knowledge-base`

This skill is a **sibling** of `generate-knowledge-base`, not a child. The two share design DNA (markdown-orchestrator + subagent pattern, idempotent runs, MADR-style decision records elsewhere in the same repo), but they're never coupled. `generate-prd` ignores any docs `generate-knowledge-base` might have generated — pure-conversation discovery, no codebase context (spec § 2.1).

Run them in either order, or independently; they don't read each other's outputs.

---

## Further reading

- [`docs/specs/2026-05-15-generate-prd-design.md`](../docs/specs/2026-05-15-generate-prd-design.md) — the design spec (16 sections, the authoritative source for behavior)
- [`docs/install.md`](docs/install.md) — detailed install, verification, troubleshooting
- [`docs/walkthrough.md`](docs/walkthrough.md) — worked example: a paused-and-resumed session
- [`tests/golden-corpus/README.md`](tests/golden-corpus/README.md) — what the test corpus is designed to exercise

---

## License

Same license as the parent repository.
