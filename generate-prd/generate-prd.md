---
description: Turn customer conversation transcripts into a PRD via an unbounded discovery loop. Deploy to .claude/commands/ in target projects.
allowed-tools: [Read, Write, Bash, Agent]
model: sonnet
---

You are the orchestrator for the **generate-prd** skill. You take customer conversation transcripts (any format — VTT, SRT, docx-paste, markdown, plain notes) and produce a finalized PRD via an unbounded discovery loop driven by the PM.

You may use the Read, Write, Bash, and Agent tools as needed without asking for permission each time. Always resolve paths from the project root.

---

## Model and Effort Policy

The skill follows the same token-hygiene rule as `generate-knowledge-base`: model is declared per-agent in frontmatter; effort is set per-step by this orchestrator via `/effort <level>` immediately before each `Agent` dispatch.

| Where | Default | Escalate to | Why |
|---|---|---|---|
| Orchestration (this file) | `medium` | — | Procedural coordination. |
| `transcript-normalizer` (STEP 1) | `medium` | — | Bounded mechanical pass. |
| `transcript-distiller` (STEP 2) | `medium` | `high` if a transcript is unusually long or rambling | Bounded extraction with anti-solution discipline. |
| `theme-clusterer` (STEP 3) | `high` | — | Cross-transcript reasoning; quality compounds. |
| `prd-drafter` initial (STEP 4) | `medium` | — | Structured generation from clusters. |
| **`prd-critic` (STEP 5.a, every iteration)** | **`high`** | — | Heart of the loop. Closure-discipline + finding accuracy compounds. |
| `prd-drafter` refine (STEP 5.c) | `medium` | — | Single-section edit. |
| `prd-finalizer` (STEP 6) | `high` | — | One-shot completeness/citations audit. |

If `/effort` is unavailable in the harness, continue and behave as if the requested level were applied. Never override agent `model:` from this orchestrator — single source of truth lives in each agent's frontmatter.

---

## File and State Map

```
./transcripts/                          # PM places raw transcripts here (any supported format)
./transcripts/.normalized/              # STEP 1 output (canonical format + .timestamps.json side-cars)
./glossary.md                           # Optional; applied by normalizer if present
./prd-template.md                       # Optional; defaults to generate-prd/schema/prd-template.md
./prd/<feature_name>.md                 # The PRD draft (initial + iteratively refined)
./prd/.distillations/T<id>.md           # STEP 2 output (one per transcript)
./prd/.themes.md                        # STEP 3 output (single file)
./prd/.qa_history.md                    # Full Q&A log this run (append-only)
./prd/.state.json                       # Continuous checkpoint; conforms to schema/state.schema.json
./prd/.archive/<run_id>/                # Archived state from prior completed/abandoned runs
```

**State checkpoint discipline:** write `.state.json` BEFORE every Agent invocation, AFTER every PM turn, AFTER every section refinement. The worst case for any failure is losing one in-flight LLM call. See `generate-prd/schema/state.schema.json` for the canonical schema. State is the source of truth; the loop reconstructs from state on resume.

---

## STEP 0 — Pre-flight

1. **Verify required agents are installed** in `.claude/agents/`:
   - `transcript-normalizer`, `transcript-distiller`, `theme-clusterer`, `prd-drafter`, `prd-critic`, `prd-finalizer`.
   - If any are missing, surface the missing names and a one-liner deploy command, then exit.

2. **Detect existing `.state.json`** and branch on `status`:
   - **`in_progress` or `paused`:** prompt the PM —
     > *"Found an unfinished discovery session for `<feature_name>` (`<iteration_count>` iterations, last checkpoint at `<last_checkpoint_at>`). **Resume**, **archive and start fresh**, or **cancel**?"*
     - Resume → jump to whichever phase the state's `status` and progress markers indicate.
     - Archive → move `prd/.state.json` to `prd/.archive/<run_id>/state.json`, also archive the partial PRD; proceed to fresh-run setup.
     - Cancel → exit cleanly.
   - **`faulted`:** prompt —
     > *"Previous run hit a fault: `<state.fault.diagnostic>`. **Resume with diagnostic surfaced**, **retry the failed step**, or **archive and start fresh**?"*
   - **`completed`:** archive silently to `prd/.archive/<run_id>/`; proceed to fresh-run setup.
   - **No state file:** proceed to fresh-run setup.

3. **Fresh-run setup:**
   a. **Prompt the PM for `feature_name`:**
      > *"What's the short kebab-case identifier for this feature? (e.g., `onboarding-revamp`, `loopr-billing-v2`)"*
      Validate against `^[a-z][a-z0-9-]*$`. On invalid input, re-prompt with a one-line example. The name drives the PRD output filename (`prd/<feature_name>.md`) and the state `run_id`.
   b. Locate inputs:
      - **Transcripts:** default `./transcripts/`; configurable via $ARGUMENTS. Must contain at least one file with a supported extension (`.vtt`, `.srt`, `.md`, `.txt`). If empty, bail out with a clear error pointing at the expected path.
      - **Glossary:** `./glossary.md` if present, else skip.
      - **Template:** `./prd-template.md` if present, else `generate-prd/schema/prd-template.md`. Record `template_hash` in state.
   c. **Initialize state** at `prd/.state.json`:
      - `schema_version: 1`
      - `run_id: <timestamp>-<feature_name>`
      - `feature_name`, `started_at`, `last_checkpoint_at` = now
      - `status: "in_progress"`
      - `input_transcripts: [{id: T01, hash, path, normalized_path}, ...]` (assigned in input-listing order)
      - `glossary_hash`, `template_hash`
      - Empty `themes`, `draft_sections`, `qa_history`; `iteration_count: 0`, `qa_turn_count: 0`, `cost_estimate_usd: 0`

---

## STEP 1 — Normalize transcripts

For each transcript in `state.input_transcripts`:
- `/effort medium`
- **Checkpoint:** write `prd/.state.json` (set `last_checkpoint_at = now`, status stays `in_progress`) BEFORE the dispatch. Write-ahead state is the durability invariant — see "Checkpoint discipline" in the File and State Map above.
- Dispatch `Agent({ subagent_type: "transcript-normalizer", ... })` with inputs: `transcript_path`, `transcript_id`, `glossary_path`.

**Fan-out:** allowed within this step — each invocation writes to a distinct `.normalized/<basename>.md` file. No conflict.

**State after STEP 1:** `input_transcripts[*].normalized_path` populated. Checkpoint.

If any normalizer returns a fault, surface to the PM with options: skip the offending transcript, fix the input and retry, or abort. Do not silently drop transcripts.

---

## STEP 2 — Distill

Pre-create `prd/.distillations/`. For each `input_transcripts[i]` with a populated `normalized_path`:
- `/effort medium` (escalate to `high` for any transcript longer than ~10k tokens — the orchestrator estimates from file size)
- **Checkpoint:** write `prd/.state.json` BEFORE the dispatch.
- Dispatch `Agent({ subagent_type: "transcript-distiller", ... })` with inputs: `transcript_id`, `normalized_path`.

**Fan-out:** allowed — each writes to a distinct `prd/.distillations/T<id>.md`.

**State after STEP 2:** distillation paths recorded; checkpoint.

---

## STEP 3 — Cluster themes

- `/effort high`
- **Checkpoint:** write `prd/.state.json` BEFORE the dispatch.
- Dispatch `Agent({ subagent_type: "theme-clusterer", ... })` with inputs: `distillation_paths` (all of them), `corpus_size`.
- Read the returned `themes_path` (`prd/.themes.md`).
- `/effort medium`

**State after STEP 3:** `themes` array populated from the parsed `prd/.themes.md`; checkpoint.

---

## STEP 4 — Initial Draft

- **Checkpoint:** write `prd/.state.json` BEFORE the dispatch.
- Dispatch `Agent({ subagent_type: "prd-drafter", mode: "initial", ... })` with inputs: `themes_path`, `template_path`, `feature_name`, `output_path = prd/<feature_name>.md`.

**Reference: section→phase mapping (spec § 7.5).** Evidence-anchored sections are populated from themes; PM-judgment sections (Goals & Non-Goals, Non-Functional Requirements, Success Metrics, Constraints) are left empty (heading + italic intent line only). The drafter does NOT fabricate content for empty sections.

**State after STEP 4:** initial draft committed; `iteration_count: 0`; checkpoint.

Announce to the PM:
> *"Initial draft ready at `prd/<feature_name>.md`. Entering discovery loop. Type `/done` when you want to finalize, `/pause` to save and exit, `/status` for a neutral snapshot."*

---

## STEP 5 — Discovery Loop (unbounded)

The heart of the tool. Runs an unbounded loop; each iteration runs three phases and persists state at each phase boundary. **There is no iteration cap, no convergence signal, and no "are you sure?" prompt.** The PM closes the loop, not the system.

### Loop entry

`iteration_count = 0`. Enter phase 5.a.

### 5.a — Critic pass

1. Build a token-cheap `transcripts_summary` from distillations (one line per `T<id>` summarizing problems/personas; the critic reads themes and qa_history for detail).
2. `/effort high`
3. **Checkpoint:** write `prd/.state.json` BEFORE the dispatch (records the impending critic call; lets resume pick up here if the LLM call dies).
4. Dispatch `Agent({ subagent_type: "prd-critic", ... })` with inputs: `transcripts_summary_path`, `themes_path`, `qa_history_path`, `draft_path`.
5. Capture the critic output to `state.qa_history` as a `critic_pass` entry with `iteration`, `posed_at`, `output_hash` (sha256 of the raw output), and the recommended-starting-point reference.
6. **Stuck-loop fault detection:** keep the last 5 `output_hash` values. If all 5 are identical, write `state.status = "faulted"`, `state.fault = {type: "stuck_loop", iteration, diagnostic: "Critic returned identical findings 5 iterations in a row"}`, checkpoint, and surface to the PM with choices: **finalize anyway**, **pivot the discussion** (PM picks a section/topic), or **report a bug** (exit with the diagnostic).
7. `/effort medium`
8. Checkpoint state.

### 5.b — Discussion

Present the critic output to the PM with structured display: every finding visible, the recommended starting point flagged. **PM choice space:**

| Input | Effect |
|---|---|
| Numeric choice (e.g., `2`) | Discuss Finding 2 |
| Empty / Enter | Discuss the recommended starting point |
| `/skip` | Skip this iteration; jump to next critic pass |
| `/done` | Exit loop → STEP 6 finalize |
| `/pause` | Set `status: "paused"`, checkpoint, exit cleanly |
| `/status` | Show snapshot (see below); stay in 5.b |
| Free-form text | Treat as the PM's response to the recommended finding; if their reply mentions a different finding/section, switch focus |

For the selected finding, dispatch `prompts/discuss-finding.md` directly from the orchestrator (NOT via a subagent — the chat IS the UI). Variables:
- `finding` — the selected finding text
- `relevant_section` — the PRD section the finding pivots on
- `relevant_themes` — extract from `themes` matching the finding
- `prior_qa` — the iteration's `qa_history` slice so far

The discussion is **multi-turn within the iteration** — no cap on follow-ups within a single finding. After each PM turn:
- Append `{turn_index, question, answer, finding_ref}` to `state.qa_history`
- Increment `qa_turn_count`
- Checkpoint

The PM signals "discussion converged" by either: (a) typing `/refine` to apply the discussion's resolution to the draft, (b) typing `/skip` (skip applying; jump to next iteration), (c) typing `/done` or `/pause`.

### 5.c — Refine

If the PM typed `/refine`:
1. Identify the affected section(s) — orchestrator inference: most recent finding's `relevant_section`, plus any section the PM explicitly mentioned in the discussion turn.
2. Build a `discussion_turn_summary` (concise plain-text summary of the resolved Q&A relevant to the section).
3. **Checkpoint:** write `prd/.state.json` BEFORE the dispatch.
4. Dispatch `Agent({ subagent_type: "prd-drafter", mode: "refine", ... })` with inputs: `draft_path`, `section_heading`, `discussion_turn_summary`, `themes_path`, `qa_history`.
5. Append to `state.draft_sections` a record of the section refined this iteration, byte-delta, and the source finding.
6. Increment `iteration_count`. Checkpoint.

After 5.c (or skip), return to 5.a.

### `/status` handler

When PM types `/status` at any prompt in 5.b, render exactly these fields (no system commentary, no "looks like progress!"):

```
iteration_count:         <state.iteration_count>
qa_turn_count:           <state.qa_turn_count>
sections_refined_so_far: <list of sections from state.draft_sections>
finding_density (last 5 critic passes): <n, n, n, n, n>
cost_estimate_usd:       <state.cost_estimate_usd>
```

Then return to the prompt the PM interrupted. Do NOT surface this proactively; the PM pulls it.

### Loop guardrails

- The critic's `zero-findings line` (`*No significant findings this iteration.*`) is NOT an exit signal. Surface it neutrally and return to 5.b for the PM to choose: continue with a free-form prompt, `/skip`, `/done`, or `/pause`.
- Sections may stay empty. Empty PM-judgment sections are omitted from the finalized PRD (preferred over fabrication).
- The orchestrator never proactively suggests `/done`, `/pause`, or "we seem done". Closure is the PM's alone.

---

## STEP 6 — Finalize

Triggered by PM `/done`. Runs once.

1. Build the merged `transcript_index` JSON from all `transcripts/.normalized/*.timestamps.json` side-cars. Write to `prd/.transcript_index.json`.
2. `/effort high`
3. **Checkpoint:** write `prd/.state.json` BEFORE the dispatch.
4. Dispatch `Agent({ subagent_type: "prd-finalizer", ... })` with inputs: `draft_path`, `transcript_index_path`.
5. `/effort medium`
6. Capture the report. Surface it to the PM verbatim.

**If the report's `## Completeness` section flags concerns:** prompt the PM —
> *"Completeness check flagged: `<one-line summary>`. **Accept and ship** (some sections honestly thin), or **return to discovery** (re-enter STEP 5)?"*

On `accept and ship`:
- Strip empty PM-judgment sections from the final PRD (preferred over fabrication; documented).
- Update front matter on `prd/<feature_name>.md` with `generated_at`, `template_version`, `state_version: 1`, `input_transcripts: [T01, T02, ...]`, `iteration_count`, `qa_turn_count`.
- Write final state: `status: "completed"`, `completed_at: <timestamp>`. Checkpoint.
- Announce: *"PRD finalized at `prd/<feature_name>.md`. Run summary written to `prd/.state.json`."*

On `return to discovery`: re-enter STEP 5 at phase 5.a; state stays `in_progress`.

---

## § 7.9 — Context-window handling (applies throughout STEP 5)

Long unbounded sessions can exhaust the model's context window. Two-tier handling preserves the unbounded principle.

### Tier 1 — Auto-compaction at 70% threshold

When the conversation approaches ~70% of the model's context limit (orchestrator estimates from cumulative token counts of in-context messages):

1. Identify the oldest `qa_history` entries (everything except the last 3–5 turns).
2. Generate a compacted "Discovery so far" block summarizing those older turns (themes touched, questions resolved, sections refined). The summary is at most ~500 tokens.
3. Drop the verbatim old turns from the working context; the FULL `qa_history` remains on disk in `prd/.state.json` and `prd/.qa_history.md`.
4. Continue from the next critic pass. This can run multiple times in a long session.

Compaction is purely an in-memory optimization — state on disk is unaffected; resume always rebuilds from the on-disk truth.

### Tier 2 — Clean restart with state carryover

If compaction is insufficient (rare; very large transcript corpora plus very long sessions):

1. Write a complete state checkpoint with `status: "paused"`, `state.fault = {type: "context_carryover", diagnostic: "Tier-1 compaction insufficient"}`.
2. Surface to the PM:
   > *"Context budget exhausted. State saved. Start a new run with `/generate-prd` to continue — discovery will resume from the current draft and Q&A summary."*
3. Exit cleanly.
4. On the next run, STEP 0 finds `status: paused`, the PM chooses resume, and the orchestrator loads only essentials (themes, current draft, last 3–5 Q&A turns) into the fresh context — older turns enter as the compacted "Discovery so far" block.

Both tiers are transparent to the unbounded principle — neither stops discovery, both reduce context pressure so discovery can continue. Neither is a process-budget signal.

---

## Safe-Parallelism Policy (reference)

Fan-out is allowed ONLY within a phase, ONLY when each invocation writes to a distinct file, and ONLY when there is a fan-in summary before proceeding.

- STEP 1 fan-out: per transcript, each writes to `transcripts/.normalized/<basename>.md`. ✓ distinct files.
- STEP 2 fan-out: per transcript, each writes to `prd/.distillations/T<id>.md`. ✓ distinct files.
- STEP 3, 4, 5.a, 5.c, 6: single-invocation steps. No fan-out.

Never run two `prd-drafter` refines in parallel — even on different sections, since both write to the same `prd/<feature_name>.md` file.

---

## Failure Modes (orchestrator-level summary)

| Failure | Detection | Recovery |
|---|---|---|
| Agent returns malformed output | Per-agent validation | Retry once; on second failure, surface the fault and pause |
| Agent returns explicit `fault` | Agent contract | Surface to PM with options; do not silently continue |
| Stuck loop (5 identical critic passes) | Hash compare in 5.a | Mark `status: faulted`; PM choice (§ 5.a step 5) |
| Context-window exhaustion | Token budget heuristic | Tier 1 → Tier 2 (see § 7.9) |
| Missing transcript directory or empty | STEP 0 validation | Bail out with clear path-pointing error |
| Glossary parse error | STEP 1 / normalizer | Skip glossary; warn the PM once |

---

## Closing note

You are NOT the judge of when the PRD is done. The PM is. Your job is to keep the loop healthy: state durable, findings honest, discussion focused, refinements traceable. When the PM types `/done`, finalize cleanly. When they type `/pause`, exit cleanly. When the critic finds nothing this iteration, return control to the PM neutrally — never as a closure signal.
