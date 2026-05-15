# Design — `generate-prd`: Customer Conversations → PRD

| Field | Value |
|---|---|
| **Status** | 📝 Draft — pending user review |
| **Date** | 2026-05-15 |
| **Author** | mdulog |
| **Sibling of** | [`generate-knowledge-base`](../../generate-knowledge-base/generate-knowledge-base.md) |
| **Spec path** | `docs/specs/2026-05-15-generate-prd-design.md` |

---

## 1. Summary

`generate-prd` is a sibling tool to `generate-knowledge-base`. It ingests cleaned customer conversation transcripts, distills them into evidence-grounded themes, drives an unbounded **discovery loop** that surfaces contradictions and questions assumptions across all artifacts every iteration, and produces a Product Requirements Document that the PM closes out when they choose.

The system runs as a **distill → draft → unbounded discovery loop**:

1. 📞 **Distill phase** — analyzers read the corpus of transcripts and extract problems, jobs-to-be-done, personas, and pains. Read-only; no PM in the loop.
2. 📄 **Initial draft** — the PRD is assembled against a swappable template from distilled evidence; sections lacking sufficient evidence start empty rather than fabricated.
3. 🔄 **Discovery loop (unbounded)** — every iteration a read-only critic re-reads all artifacts (transcripts, draft, full Q&A history) and surfaces typed findings (contradictions, coverage gaps, unsupported assumptions, solution-bias creep, evidence-thin sections). The orchestrator discusses one finding with the PM, refines the affected section(s), and checkpoints state. Loop continues until the PM types `/done` or `/pause`. There are no caps, no convergence signals, no proactive nudges to wrap up.
4. ✅ **Finalize** — completeness audit; state marked `completed`.

Two surfaces are planned, built sequentially:

- **Surface A (v1):** Claude Code skill (deployed like `generate-knowledge-base`), runs `/generate-prd`.
- **Surface B (v2 follow-on):** Standalone Python/TS CLI invoking the Anthropic SDK directly.

The two surfaces share **prompts** and **schema** as durable assets on disk; they each implement orchestration natively. A **golden-corpus regression test** detects behavioral drift between them.

---

## 2. Design Principles

These are load-bearing — they shape the prompts, the schema, and the scope. Violating any of them means changing the doc, not the code.

### 2.1 📐 Pure-conversation discovery — no codebase bias

> The PRD generator is a **discovery tool, not a design tool**. It produces evidence-grounded problem framing; it does not propose solutions, reason about feasibility, or anchor on existing system capabilities. The codebase is intentionally out of scope.

**Why this matters:** if the model is told "we have a .NET API and an Angular front-end," every problem it extracts will subtly tilt toward "thing solvable with that stack." Customer pains that imply different architectures get downweighted or rephrased into familiar shapes. The constraint that should be a *trade-off conversation* gets laundered into a *requirement* before engineering ever sees it.

**Where the principle shows up:**

- Distillation prompts include an explicit anti-solution clause (§ 7.2).
- The Constraints section is **PM-declared in the loop**, not codebase-derived (§ 6).
- The critic runs every loop iteration with `SOLUTION_BIAS` as a first-class finding type (§ 7.7).
- `generate-prd` **never** calls or reads `generate-knowledge-base`. They are deliberate siblings with disjoint inputs.

### 2.2 💾 Continuous state, durable by design

State is written to `.state.json` at every safe checkpoint — after each critic pass, each Q&A turn, and each section refinement — never just at the end. Any unexpected exit (API failure, network drop, context overflow, terminal close) leaves a resumable checkpoint. On startup, an existing in-progress state offers a resume prompt. This makes the unbounded discovery loop (§ 2.5) safe by construction: worst case is losing one in-flight Q&A turn, never a session.

### 2.3 🎯 Shared assets, duplicated orchestration

Two surfaces share the **prompts** (the model instructions) and the **schema** (the artifact format). Each surface implements its own orchestration natively — the Claude Code skill uses the supervisor + subagent pattern; the CLI uses a Python/TS engine with a REPL. A golden-corpus regression test guards against behavioral drift.

### 2.4 🪜 Swappable template, hardcoded section→phase mapping

The PRD template is a markdown file users can replace. In v1, the orchestrator hardcodes the section-to-phase mapping for known section names; unknown sections default to PM-driven in the discovery loop with the critic still running against them. Per-section metadata markers are deferred to v2 if and when 3+ templates with divergent semantics emerge.

### 2.5 🔄 Discovery is iterative, not linear

The discovery phase is a **multi-iteration loop**, not a structured questionnaire. Every iteration the critic re-reads all artifacts and surfaces what's worth questioning. The loop is **pure unbounded**: the only exits are the PM typing `/done` (finalize) or `/pause` (resume later). There are **no iteration caps, no progress warnings, no convergence signals from the system**, because any number chosen as a safety rail mutates into a target — and target-shaped discovery is anti-discovery. Resource protection comes from continuous state (§ 2.2), not from process pacing. The PM owns the decision to finalize, full stop.

---

## 3. Goals / Non-Goals

### Goals

- Convert N customer conversation transcripts (≥1, no fixed upper bound; expect 3–30 typical) into a single PRD.
- Support MS Teams VTT, Zoom transcripts, Granola/Fathom exports, and plain markdown notes as input.
- Run as a Claude Code skill (v1) and a standalone CLI (v2) producing equivalent output.
- Drive PRD refinement via an **unbounded discovery loop** that questions assumptions, surfaces contradictions between PM judgment and transcript evidence, and exposes coverage gaps — terminating only on user command.
- **Survive every common failure mode without session loss** via continuous state checkpoints; resume from interrupted runs automatically.
- Allow users to swap the PRD template and provide a project-specific jargon glossary.
- Preserve traceability from PRD claims back to source transcripts (citation markers).

### Non-Goals

- ❌ Reasoning about the existing codebase (codebase-bias anti-pattern; see § 2.1).
- ❌ Audio transcription (users bring text transcripts; audio handling is a separate v2+ ADR).
- ❌ Live customer conversation orchestration (no agent talking to customers in real time).
- ❌ Multi-PRD comparison or portfolio analysis.
- ❌ Implementation planning, design docs, or technical specs (those are downstream tools).
- ❌ Web app surface (out of scope; v3+ if demand emerges).
- ❌ System-initiated discovery termination — no iteration caps, no token caps, no convergence detection that ends the loop.

---

## 4. Architecture Overview

```
                            ┌───────────────────────────────────┐
                            │  Shared assets (on disk)          │
                            │   ├─ prompts/*.md                 │
                            │   ├─ schema/prd-template.md       │
                            │   ├─ schema/transcript-format.md  │
                            │   ├─ schema/state.schema.json     │
                            │   └─ schema/glossary.md.example   │
                            └─────────────┬─────────────────────┘
                                          │ read by
              ┌───────────────────────────┴───────────────────────────┐
              │                                                       │
   ┌──────────▼──────────────────┐                  ┌─────────────────▼────────────┐
   │  Surface A: Claude Code     │                  │  Surface B: Standalone CLI   │
   │  skill (v1)                 │                  │  (v2)                        │
   │                             │                  │                              │
   │  Orchestrator (markdown)    │                  │  core/engine.py              │
   │   ├─ transcript-normalizer  │                  │   ├─ same phase functions    │
   │   ├─ transcript-distiller   │                  │   ├─ same prompt loader      │
   │   ├─ theme-clusterer        │                  │   ├─ REPL for discovery loop │
   │   ├─ prd-drafter            │                  │   └─ writes same PRD +       │
   │   ├─ prd-critic ◀ loop ─┐   │                  │       state files            │
   │   ├─ (chat is the       │   │                  │                              │
   │   │   discussion UI)    │   │                  │                              │
   │   └─ finalize completed─┘   │                  │                              │
   │                             │                  │                              │
   │  Continuous checkpoints:    │                  │  Continuous checkpoints:     │
   │   docs/prd/<feature>.md     │                  │   ./prd/<feature>.md         │
   │   docs/prd/.state.json ◀── written every iteration ──▶ ./prd/.state.json      │
   └─────────────────────────────┘                  └──────────────────────────────┘

                                       │
                                       ▼
                            ┌───────────────────────────────────┐
                            │  Golden-corpus regression test    │
                            │  • Run A and B on same inputs     │
                            │  • Semantic diff outputs          │
                            │  • Fail CI on divergence          │
                            └───────────────────────────────────┘
```

---

## 5. Repository Layout

```
generate-prd/                              ← Skill source (parallel to generate-knowledge-base/)
├── generate-prd.md                        ← Orchestrator skill (deployed to .claude/commands/)
├── Agents/
│   ├── transcript-normalizer.md           ← Source-detecting adapter: VTT / SRT / docx-paste /
│   │                                         markdown notes → canonical format
│   ├── transcript-distiller.md            ← Extracts problems, JTBD, pains, personas (read-only)
│   ├── theme-clusterer.md                 ← Groups distilled findings into themes (read-only)
│   ├── prd-drafter.md                     ← Assembles initial draft from themes; refines per-section in the loop
│   ├── prd-critic.md                      ← Read-only; runs every iteration of the discovery loop;
│   │                                         emits typed findings (contradictions, gaps, assumptions,
│   │                                         solution-bias, goal/metric mismatches, persona/story
│   │                                         mismatches, evidence-thin sections)
│   └── prd-finalizer.md                   ← Completeness audit at session end (much smaller than
│                                              old auditor — most checks migrated into critic)
├── prompts/                               ← Shared markdown prompts; both surfaces consume these
│   ├── normalize-transcript.md
│   ├── distill-transcript.md
│   ├── cluster-themes.md
│   ├── draft-prd.md                       ← Initial draft + per-section refinement
│   ├── critic-pass.md                     ← The discovery loop's heart — most important prompt
│   ├── discuss-finding.md                 ← Orchestrator's per-iteration discussion turn
│   └── finalize-prd.md                    ← Completeness check at session end
├── schema/                                ← Shared schema and templates
│   ├── prd-template.md                    ← Default PRD template (swappable)
│   ├── transcript-format.md               ← Canonical normalized transcript schema
│   ├── glossary.md.example                ← Example glossary file
│   └── state.schema.json                  ← Versioned for stateful-ready seam
├── cli/                                   ← v2 surface (not built in v1)
│   └── (placeholder)
└── tests/
    └── golden-corpus/                     ← Regression test inputs + expected outputs
```

---

## 6. The PRD Template (v1 default)

Ships at `schema/prd-template.md`. Users may replace it; the orchestrator reads whatever template is present and applies the section→phase mapping (§ 7.5) to known section headings.

```markdown
# {feature_name}

## Background & Problem
*What problem are we solving, and why is now the right time?*

## Target Users
*Who is this for, and what do we know about them from the evidence?*

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

## Functional Requirements
*Numbered list of must-have capabilities.*

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*
```

The italic intent lines are the contract the orchestrator reads to drive each phase. They serve three audiences: human readers, prompt construction, and future automation.

---

## 7. Phase Machine

The orchestrator executes phases sequentially. Within a phase, subagent fan-out is allowed when tasks are independent and write to distinct files (mirrors the safe-parallelism policy from `generate-knowledge-base`).

### 7.1 STEP 0 — Pre-flight

- Verify Claude Code agents are installed.
- **Detect existing `.state.json`** and branch:
  - `status: in_progress` or `status: paused` → prompt PM: *"Found an unfinished discovery session for `<feature>` (N iterations, last checkpoint at `<time>`). **Resume**, **archive and start fresh**, or **cancel**?"*
  - `status: faulted` → prompt PM: *"Previous run hit a fault: `<diagnostic>`. **Resume with diagnostic**, **retry failed step**, or **archive and start fresh**?"*
  - `status: completed` → archive silently; start a clean run.
  - No state file → proceed to fresh-run setup.
- Locate transcript inputs (default: `./transcripts/`; configurable).
- Locate optional `glossary.md` (apply if present, skip if not).
- Locate optional user-supplied `prd-template.md` (use default if not).
- Validate at least one transcript file exists; bail out with a clear error if not.

### 7.2 STEP 1 — Normalize transcripts

Subagent: `transcript-normalizer` (one invocation per source file, fan-out allowed).

For each input file:
1. Detect format (VTT, docx-paste, Granola export, plain markdown).
2. Apply format-specific cleanup (strip VTT cue numbers, collapse multi-line utterances, extract timestamp→speaker→text triples).
3. Apply glossary substitutions if `glossary.md` present (term mappings: `Looper: Loopr`).
4. Emit canonical normalized transcript file: `./transcripts/.normalized/<original>.md` with stable speaker turns and a reserved-but-unused `speakers:` front-matter field (v2 forward-compat).
5. Preserve timestamp index in a side-car file for citation traceability.

### 7.3 STEP 2 — Distill

Subagent: `transcript-distiller` (read-only; one invocation per normalized transcript, fan-out allowed).

**Prompt carries the anti-solution clause:**

> Extract problems, jobs-to-be-done, observed pains, and personas. Capture customer-proposed solutions as `customer's proposed solution` — never as requirements. Do not infer or invent solutions, technical approaches, or implementation strategies. Cite source as `[T<id>:<timestamp>]` (e.g., `[T03:12:45]`).

Output: per-transcript distillation file with structured findings (JSON or markdown front-matter).

### 7.4 STEP 3 — Cluster themes

Subagent: `theme-clusterer` (read-only; single invocation reading all distillations).

Groups raw findings across transcripts into themes. Each theme carries:
- Theme statement
- Supporting evidence (list of `[T<id>:<timestamp>]` citations)
- Frequency (how many transcripts mentioned it)
- Contradictions (if any transcripts disagreed)

Output: `./prd/.themes.md`

### 7.5 Section→phase mapping (reference table)

This is a reference, not a step. The orchestrator uses this table during STEP 4 (initial draft) and STEP 5 (discovery loop) to decide where each section's content comes from and what the critic should emphasize.

| Section | Initial-draft source | Discovery loop emphasis |
|---|---|---|
| Background & Problem | 📞 Themes + frequency | Solution bias; framing fidelity |
| Target Users | 📞 Personas extracted | Persona invention without evidence; coverage gaps |
| Goals & Non-Goals | Empty (PM judgment in loop) | Goals must trace to themes; non-goals must be intentional |
| User Stories | 📞 Story-shaped evidence | Solution bias in "so that" clauses; persona↔story mismatch |
| Functional Requirements | 📞 Capability hints | Solution bias; evidence thinness |
| Non-Functional Requirements | Empty (PM judgment in loop) | Unsubstantiated thresholds |
| Success Metrics | Empty (PM judgment in loop) | Goal↔metric mismatch |
| Risks & Open Questions | 📞 Contradictions + gaps | Completeness against distilled contradictions |
| Constraints | Empty (PM-declared in loop, skippable) | Solution bias |

Unknown sections (user replaced template) default to: distill if any themes match section title heuristically; otherwise PM-driven in the loop. The critic always runs against every section regardless of source.

### 7.6 STEP 4 — Initial Draft

Subagent: `prd-drafter` (single invocation; runs on the full distillation + theme cluster).

Assembles a first-pass draft of the PRD using the section→phase mapping (§ 7.5):
- **Evidence-anchored sections** (Background, Target Users, User Stories, Functional Requirements, Risks): populated from distilled themes with `[T<id>:<timestamp>]` citations.
- **PM-judgment sections** (Goals & Non-Goals, Non-Functional Requirements, Success Metrics, Constraints): left **empty** — the discovery loop fills these.

Critically, the drafter **does not fabricate content** for sections without evidence. An empty section is the correct output when transcripts don't supply the answer; the loop is where the PM provides it.

Output: `./prd/<feature-name>.md` (initial draft) + state checkpoint with `status: in_progress`, `iteration_count: 0`.

### 7.7 STEP 5 — Discovery Loop (unbounded)

The heart of the tool. Replaces what would conventionally be a linear interview. The orchestrator runs an unbounded loop with the PM in the conversation; each iteration runs in three phases and persists state at each phase boundary.

**Loop entry:** initial draft from STEP 4 exists in state.

#### 7.7.1 Iteration phase 5.a — Critic pass

Subagent: `prd-critic` (read-only).

Inputs: normalized transcripts (or their distillations for token efficiency), clustered themes, full Q&A history, current draft PRD.

Output: a list of typed findings — **not ranked, listed in full**:

| Type | Meaning |
|---|---|
| ⚠️ `CONTRADICTION` | PM answer or draft text contradicts transcript evidence |
| 🧱 `COVERAGE_GAP` | High-frequency theme not represented in the PRD |
| 💭 `UNSUPPORTED_ASSUMPTION` | Claim in the draft with no transcript backing or PM justification |
| ⚙️ `SOLUTION_BIAS` | Language anchoring on an implementation rather than an outcome |
| 🎯 `GOAL_METRIC_MISMATCH` | Stated goal without a measurable success metric (or vice versa) |
| 🧑‍💼 `PERSONA_STORY_MISMATCH` | User story doesn't map to any declared persona |
| 🪶 `EVIDENCE_THIN` | Section claim cites few or weak transcripts |

Each finding includes: type, affected section, evidence references, one-sentence description. The critic also flags a **recommended starting point** but does not enforce it. The critic **never signals "I think we're done"** — closure is the PM's alone.

State checkpoint after critic pass: findings recorded.

#### 7.7.2 Iteration phase 5.b — Discussion

Orchestrator-driven (not a subagent), prompt: `discuss-finding.md`.

The orchestrator presents all findings in a structured display with the recommended starting point flagged. PM choice space:

- Reply to the recommended finding (default path)
- Pick a different finding by number
- Skip this iteration entirely (`/skip`)
- Type free-form direction (e.g., "let's revisit Target Users")
- Type `/done`, `/pause`, or `/status`

Discussion is **multi-turn within the iteration**; depth-driven, not breadth-rationed. No cap on follow-ups within a single finding. State checkpoint after each PM turn (Q recorded, A recorded).

#### 7.7.3 Iteration phase 5.c — Refine

Subagent: `prd-drafter` (per-section invocation).

Updates the affected section(s) based on the discussion. State checkpoint records the section diff and increments `iteration_count`.

#### 7.7.4 Termination (exclusively user-driven)

| Exit | Trigger | Effect |
|---|---|---|
| ✅ Finalize | PM types `/done` | Proceed to STEP 6 |
| ⏸️ Pause | PM types `/pause` | State written with `status: paused`; orchestrator exits cleanly; next run offers resume (§ 7.1) |
| 🛑 Fault | Critic returns identical findings 5 iterations in a row | State written with `status: faulted` + diagnostic; surfaced to PM with choices: finalize, pivot the discussion, or report a bug |

There is **no iteration cap, no convergence signal, no "are you sure?" prompt**. The critic returning "no significant findings this iteration" is not an exit — the PM still chooses.

#### 7.7.5 Visibility — on-demand only

`/status` command returns a neutral snapshot:
- Iteration count
- Sections refined in this run
- Total Q&A turns
- Finding density: last 5 critic passes (e.g., `3, 2, 1, 1, 0 findings`)
- Cost-to-date (informational)

The system **never proactively surfaces these**. The PM pulls them.

#### 7.7.6 Loop guardrails (apply throughout)

- Critic questions probe problem framing, goals, success criteria, non-goals, constraints — never implementation approaches.
- Sections can stay empty; empty sections are omitted from the finalized PRD (preferred over fabrication).
- Solution-bias detection runs every iteration as a first-class finding type, not just at finalize.

### 7.8 STEP 6 — Finalize

Subagent: `prd-finalizer` (read-only).

Runs only when PM types `/done`. Much slimmer than the old end-stage audit — most checks migrated into the in-loop critic. Final responsibilities:

1. **Completeness audit** — every section either has content or is intentionally omitted. No half-filled sections.
2. **Citation resolvability** — every `[T<id>:<timestamp>]` resolves against the side-car index.
3. **Front-matter assembly** — `generated_at`, `template_version`, `state_version`, `input_transcripts`, `iteration_count`, `qa_turn_count`.
4. **State write** — `.state.json` set to `status: completed`, `completed_at: <timestamp>`.

If completeness audit surfaces concerns, present them to the PM with a choice: **accept and ship** (some sections honestly thin) or **return to discovery loop** (re-enter STEP 5). The finalizer never silently rewrites.

### 7.9 Context-window handling (applies throughout STEP 5)

Long unbounded sessions can exhaust the model's context window. Two-tier handling preserves the unbounded principle:

**Tier 1 — Auto-compaction at 70% threshold.**
When the conversation approaches the model's context limit, the orchestrator compacts older Q&A turns into a summary "discovery so far" block, retaining recent turns (last 3–5) verbatim. Transcripts and themes are referenced by ID, not re-included. This can run multiple times in a long session.

**Tier 2 — Clean restart with state carryover.**
If compaction is insufficient (rare; very large transcript corpora plus long sessions), the orchestrator:
1. Writes a complete state checkpoint.
2. Surfaces to the PM: *"Context budget exhausted. State saved. Start a new run to continue — discovery will resume from the current draft and Q&A summary."*
3. Exits cleanly with `status: paused, reason: context_carryover`.
4. The next run loads only the essentials (themes, current draft, Q&A summary) into a fresh context.

Both tiers are transparent to the unbounded principle — neither stops discovery, both reduce context pressure so discovery can continue. Neither is a process-budget signal.

---

## 8. Input Pipeline Detail

Real transcripts are messier than the canonical schema regardless of source. The normalizer absorbs this so every downstream prompt sees the same shape.

**Supported input formats (v1):**

| Format | Example sources | Notes |
|---|---|---|
| WebVTT (`.vtt`) | MS Teams export, Zoom export, Otter, Riverside | Cue numbers + timestamps + speaker turns on separate lines; needs parsing |
| Speaker-labeled markdown / text | Granola, Fathom, manually cleaned notes, copy-paste from any meeting tool | Already close to canonical; light pass |
| Word-document paste (`.docx` extracted to text) | Teams "meeting recap" download, Word transcript exports | Speaker + utterance per line; trivial to parse |
| Plain prose notes | Hand-typed by the PM during/after a call | Treated as single-speaker degenerate case |
| SRT (`.srt`) subtitles | Generic transcription tools, podcast platforms | Same approach as VTT |

Source-detection happens in the normalizer; the format adapter is the only source-aware part of the pipeline. Adding a new format means adding a new adapter — distill, cluster, draft, and critic phases never see source-specific structure.

### 8.1 Transcript quirks the normalizer absorbs

These quirks show up across multiple transcription sources — they are not specific to any one tool. The normalizer + downstream prompts handle them uniformly:

| Quirk | Where it shows up | Handling |
|---|---|---|
| Cue numbers + timestamps + speaker on separate lines | VTT, SRT, some Word exports | Format adapter collapses to `<speaker>\t<text>` with timestamp side-car |
| Speaker mis-attribution (crosstalk, shared rooms, weak audio) | Any auto-transcribed source | Distillation prompt treats speaker labels as **hints**; never attributes quotes to specific people unless corroborated |
| Disfluencies preserved verbatim ("um", "uh", false starts) | Most auto-transcribed sources; absent in human-summarized notes | Distillation prompt **paraphrases meaning**; does not quote verbatim |
| Domain term mangling (`Loopr` → `Looper`) | Any speech-to-text source unfamiliar with the user's jargon | Glossary substitution at normalize time (§ 8.2) |
| No semantic markup (no topics, action items) | VTT, SRT, raw exports; partially present in Granola/Fathom | All structuring happens in distill + cluster phases regardless |
| External vs. internal speakers mixed | Any multi-party meeting recording | v1: treat all speakers equally. v2: read `speakers:` front-matter to disambiguate |
| Timestamps as noise for distillation, signal for citation | Any timestamped format (VTT, SRT, Teams docx, Zoom) | Strip from distillation input; preserve in side-car for `[T<id>:<timestamp>]` citations |
| No timestamps at all | Hand-typed notes, summary-style exports (Granola/Fathom) | Citations fall back to `[T<id>]` without timestamp; PRD reader can still navigate to the source transcript |

### 8.2 Glossary file

Optional `glossary.md` at project root:

```markdown
# Glossary

# original: canonical
Looper: Loopr
Sales Force: Salesforce
John Roe: John Doe
A C M E: ACME
```

Mechanism:
- Pre-normalization pass: case-insensitive term replacement on transcript text.
- LLM-assisted fallback for context-sensitive cases (e.g., "Looper" is correct in a film reference but not as a product name) — only if a deterministic regex pass leaves ambiguous matches.

STEP 0 surfaces a hint when no glossary is found: *"Tip: if your transcripts have unusual product names or acronyms, create `glossary.md` with `original: canonical` pairs — accuracy improves significantly."*

---

## 9. Solution-Bias Guardrails (How the Principle Is Enforced)

The principle in § 2.1 isn't aspirational — it's enforced at four points in the pipeline:

| Layer | Guardrail |
|---|---|
| **Distillation prompt** | Explicit anti-solution clause; customer-proposed solutions captured as such, never as requirements |
| **Discussion prompt** | The orchestrator's per-iteration discussion turn never asks about implementation approaches; PM injects constraints consciously via the Constraints section |
| **Critic — every iteration** | `SOLUTION_BIAS` is a first-class finding type that runs every loop iteration. Catches drift the moment it appears, not at finalize |
| **Architectural** | `generate-prd` does not call `generate-knowledge-base`; no codebase context enters the pipeline |

---

## 10. Output Format

### 10.1 PRD file

- Path: `./prd/<feature-name>.md` (default; configurable)
- Format: markdown following the template structure
- Front-matter includes: `generated_at`, `template_version`, `state_version`, `input_transcripts: [...]`
- Citations inline: `[T03:12:45]` referring to transcript ID 3 at timestamp 12:45

### 10.2 State file (continuous, v1 core)

- Path: `./prd/.state.json`
- Schema versioned (`schema_version: 1`) — bump for breaking changes; written-out version must equal reader-expected version or migration runs
- Written at every safe checkpoint: post-critic-pass, post-Q&A-turn, post-section-refinement
- Purpose: failure-resilient unbounded discovery, resume on next run, audit traceability

**Schema (informal):**

```json
{
  "schema_version": 1,
  "run_id": "2026-05-15-loopr-onboarding",
  "feature_name": "loopr-onboarding",
  "started_at": "2026-05-15T14:22:03Z",
  "last_checkpoint_at": "2026-05-15T16:48:11Z",
  "status": "in_progress",
  "fault": null,

  "input_transcripts": [
    {
      "id": "T01",
      "hash": "sha256:...",
      "path": "transcripts/discovery-call-1.vtt",
      "normalized_path": "transcripts/.normalized/discovery-call-1.md"
    }
  ],
  "glossary_hash": "sha256:...",
  "template_hash": "sha256:...",

  "themes": [
    { "id": "TH01", "statement": "...", "evidence": ["[T01:12:45]", "[T03:08:21]"],
      "frequency": 4, "contradictions": [] }
  ],

  "draft_sections": {
    "Background & Problem": "...",
    "Target Users": "...",
    "Goals & Non-Goals": "",
    "User Stories": "...",
    "Functional Requirements": "...",
    "Non-Functional Requirements": "",
    "Success Metrics": "",
    "Risks & Open Questions": "...",
    "Constraints": ""
  },

  "qa_history": [
    {
      "iteration": 1,
      "critic_findings": [
        { "type": "CONTRADICTION", "section": "Goals & Non-Goals",
          "evidence": ["[T01:14:22]", "[T04:09:15]"], "description": "..." }
      ],
      "selected_finding": 1,
      "turns": [
        { "role": "orchestrator", "content": "..." },
        { "role": "pm", "content": "..." }
      ],
      "sections_refined": ["Goals & Non-Goals"]
    }
  ],

  "iteration_count": 23,
  "qa_turn_count": 58,
  "cost_estimate_usd": 4.27
}
```

**Status values:**

| Status | Meaning |
|---|---|
| `in_progress` | Run is active or was interrupted mid-iteration |
| `paused` | PM typed `/pause`; resumable cleanly |
| `faulted` | Stuck-loop or other detected fault; diagnostic in `fault` field |
| `completed` | PM typed `/done`, finalize step ran successfully; archive on next run |

---

## 11. Forward-Compat Seams (v2+)

These are explicitly designed into v1 to keep v2 cheap:

| v2 feature | v1 seam |
|---|---|
| **Incremental transcript ingestion** (new transcripts arrive after a PRD is "complete"; re-open discovery on just the deltas) | `.state.json` already contains transcript hashes + theme cluster + Q&A history; the v2 work is delta detection + targeted re-critic, not state design |
| **Speaker roles** | `speakers:` front-matter field reserved in normalized transcript schema (unused in v1 logic) |
| **CLI surface** | Prompts and schema externalized as durable files; no Claude-Code-specific syntax in prompt text |
| **Audio ingestion** | Normalizer step is a clean boundary; new format adapters plug in without touching distill/cluster/draft phases |
| **Codebase context** | **Explicitly NOT a seam.** This is excluded by design principle § 2.1, not deferral. Crossing this line requires changing the design doc. |
| **System-initiated termination** (auto-stop on convergence) | **Explicitly NOT a seam.** Excluded by design principle § 2.5; only the PM ends discovery. |

Note: what was once "stateful re-runs as a v2 feature" is now subsumed into v1 by continuous-state-checkpoints (§ 2.2). Resume after any interruption is a v1 capability. The remaining v2 work is *delta-driven discovery on new transcripts after a completed PRD*, which is a smaller and better-defined feature.

---

## 12. Testing

### 12.1 Golden corpus

A small set of curated transcript fixtures lives in `tests/golden-corpus/`:
- 3–5 transcripts covering typical shapes (Teams VTT, Zoom export, Granola, plain notes)
- One transcript with intentional speaker mis-attribution
- One transcript with disfluency-heavy text
- One transcript that contradicts another (to test contradiction surfacing)
- A glossary file with known mappings
- An expected reference PRD (regenerated occasionally with human review)

### 12.2 Regression test

Once Surface B (CLI) exists:
- Run A and B on the same golden corpus.
- Semantic-diff the produced PRDs (not byte-equal; structured comparison of sections, claims, citations).
- Fail on any **structural** divergence (different sections, different citation counts, different number of distilled themes). Tolerate **prose-level** divergence (different phrasings of the same claim) — quantified semantically via either a model-judged equivalence check or a documented similarity metric, whichever proves stable when the CLI lands.

### 12.3 Prompt regression

Each prompt has a fixture-based test: same input → output meets structural assertions (e.g., "distillation output must contain at least one item per transcript or explicitly state insufficient evidence").

---

## 13. Build Order

1. **v1.0 — Critical-path prompts and schema**
   - Write `critic-pass.md` first — this is the most important and hardest prompt; quality determines whether the discovery loop is valuable or noise
   - Write remaining prompt files (`normalize-transcript`, `distill-transcript`, `cluster-themes`, `draft-prd`, `discuss-finding`, `finalize-prd`)
   - Write schema files (template, transcript format, glossary example, state schema with the v1 state structure from § 10.2)
   - Smoke-test prompts manually with sample transcripts
2. **v1.1 — Skill orchestrator and subagents**
   - Write `generate-prd.md` orchestrator (STEP 0 → STEP 6 + § 7.9 context handling)
   - Write the 6 subagent files (`transcript-normalizer`, `transcript-distiller`, `theme-clusterer`, `prd-drafter`, `prd-critic`, `prd-finalizer`)
   - Wire into Claude Code; test end-to-end on golden corpus including a deliberately long discovery session for context-window behavior
3. **v1.2 — State durability hardening**
   - Validate checkpoint write happens before every potentially-failing API call
   - Test resume after artificially-induced interruptions (kill mid-iteration, simulate 429s/529s, exhaust context)
   - Verify schema migration path exists (even if v1 → v1 is a no-op, the mechanism is in place for v1 → v2)
4. **v1.3 — Critic prompt tuning**
   - Tune `critic-pass.md` against intentional fixtures: planted contradictions, solution-bias creep, coverage gaps, persona/story mismatches
   - Verify the critic never signals closure (it lists findings only)
5. **v1.4 — Documentation + deployment guide**
   - README, install instructions, example walkthrough including a paused-then-resumed session
   - Note relationship to `generate-knowledge-base` (sibling, never coupled)
6. **v2.0 — CLI surface**
   - Extract Python engine consuming the same prompts/schema
   - REPL for discovery loop (renders findings list, recommended starting point, `/status`, `/done`, `/pause`)
   - Golden-corpus regression test in CI: same inputs through A and B, semantic-diff outputs
7. **v2.x — As demand surfaces**
   - Speaker role logic (activate `speakers:` field)
   - Incremental transcript ingestion (delta-driven discovery on new transcripts after `status: completed`)
   - Additional input formats (audio via Whisper adapter; Slack threads; CRM exports)

---

## 14. Risks and Open Questions

| Risk / Question | Mitigation / Notes |
|---|---|
| Distillation prompt over-extracts (every aside becomes a "pain") | Iterate against golden corpus; add explicit signal-vs-noise heuristic to prompt |
| **Critic becomes lazy** (returns "no findings" too readily because PM has tired of pushback) | Critic prompt explicitly tasks it with depth over closure; it has no signal that the session is "supposed" to end; finding density is shown via `/status` so the PM can judge |
| **Critic becomes pedantic** (returns dozens of trivial findings every iteration) | Finding types are explicit and bounded; `EVIDENCE_THIN` is the only "soft" type and must include strength score; tune against golden corpus to set signal threshold |
| Glossary application creates false substitutions | Regex pass is exact-match (case-insensitive); LLM fallback only on ambiguous matches |
| Citation drift (citations point to wrong timestamps) | Side-car timestamp index from normalize step; finalizer verifies citation resolvability |
| Template-swap users get wrong section→phase mapping | Unknown sections default to PM-driven; critic still runs against them; document the table for users writing custom templates |
| Two surfaces drift behaviorally | Golden-corpus regression test; CI gate on Surface B |
| User runs v1 without normalizer's glossary feature, complains about garbled jargon | STEP 0 hint surfaces the feature; document in README; v1.4+ could auto-suggest glossary terms from frequency analysis |
| PM provides too little content; PRD ends up hollow | Empty sections are honest, not failed; finalizer flags them; user can return to discovery or accept and ship |
| **API failures interrupt session** (rate limits, overload, network drops, context overflow) | Continuous state checkpoints (§ 2.2) bound loss to one in-flight Q&A turn; resume on next run via § 7.1 |
| **Context window exceeded** in a long session | Two-tier handling in § 7.9: auto-compaction at 70%, clean restart with state carryover if compaction insufficient |
| **Unbounded loop runs up cost** (PM walks away with chat open) | The loop blocks on PM input, so it cannot iterate without engagement. `/status` includes cost-to-date for PM visibility. No opt-in cost ceiling in v1 (per principle § 2.5); resource risk is the PM's to manage |
| **Stuck loop** (critic emits identical findings 5+ iterations in a row) | Detected as a fault; surfaces honestly with diagnostic; PM chooses finalize, pivot, or bug-report |
| **Schema migration when v2 lands** | `schema_version` field in state from day 1; v1 → v2 needs a migration script; tested in v1.2 build phase |

---

## 15. Out of Scope (Explicit)

- Codebase scanning / integration (design principle § 2.1)
- Audio / video transcription
- Live customer conversation orchestration
- Web app surface
- Multi-PRD comparison / portfolio management
- Implementation planning, technical design, architecture decisions
- System-initiated discovery termination (design principle § 2.5)
- Incremental transcript ingestion after a PRD is `completed` (v2 feature; v1 supports interrupted-run resume but not delta-on-new-transcripts)
- Speaker role disambiguation logic (v1 — schema field reserved)
- Opt-in cost ceilings or token budgets (pure unbounded by design)

---

## 16. Open Decisions Pending User Review

None at draft time. All major architectural and content decisions are captured above. If anything below is unclear or wrong, flag during spec review.

---

## Appendix A — Sharing Boundary Summary

| Asset | Owned by | Shared between A and B? |
|---|---|---|
| Prompts (`prompts/*.md`) | Source repo | ✅ Yes — same files |
| Schema (`schema/*`) | Source repo | ✅ Yes — same files |
| Glossary mechanism | Source repo | ✅ Yes — same logic |
| Template default | Source repo | ✅ Yes — same file |
| Orchestration (phase machine) | Each surface | ❌ Duplicated; native to each runtime |
| Subagent isolation | Surface A (Claude Code) | ❌ Surface B uses asyncio + process-level isolation |
| Discovery loop UI | Each surface | ❌ Surface A = native chat; Surface B = REPL |
| Output schema (PRD + state.json) | Source repo | ✅ Yes — byte-identical structure expected |
