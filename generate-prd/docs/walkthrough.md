# Walkthrough — a paused-and-resumed discovery session

A worked example showing what running `/generate-prd` actually feels like, with a `/pause` mid-session and a clean resume the next day. Names, transcript content, and timings are illustrative — your real session will look similar.

> **Note:** This is a *narrative* example written from the spec and the golden corpus. Once you run a real session you may want to replace this with a captured transcript (`runs/walkthrough.txt`). The narrative below is what the skill should produce; running the holistic playbook at [`../tests/durability/test_critic_holistic.md`](../tests/durability/test_critic_holistic.md) is the way to confirm the real behavior matches.

---

## Day 1 — start the session

Working directory: a fresh project; the skill is installed per [`install.md`](install.md). Five customer conversations from the past two weeks are sitting in `transcripts/`:

```bash
$ ls transcripts/
T01-onboarding-friction.vtt
T02-workflow-speed.docx-paste.md
T03-compliance-question.granola.md
T04-contradictory-pricing.vtt
T05-handtyped-notes.md
```

A `glossary.md` exists at the project root with one entry: `Looper: Loopr` (the PM consistently mistypes the product name in their hand-typed notes).

The PM kicks off:

```
/generate-prd
```

### STEP 0

```
> Found no existing discovery session.
> What's the short kebab-case identifier for this feature?
> (e.g., `onboarding-revamp`, `loopr-billing-v2`)
```

PM types: `loopr-onboarding`.

```
> Located 5 transcripts in ./transcripts/. Glossary found at ./glossary.md.
> Using default template (generate-prd/schema/prd-template.md).
> Initialized prd/.state.json (run_id: 20260515-093014-loopr-onboarding).
> Starting STEP 1 — Normalize transcripts.
```

### STEPS 1-3 (about 90 seconds wall-clock)

The orchestrator fans out the normalizer across the 5 transcripts in parallel, then the distiller, then runs the clusterer. The PM sees progress messages but no questions yet.

```
✓ STEP 1: 5 transcripts normalized → transcripts/.normalized/
✓ STEP 2: 5 distillations → prd/.distillations/
✓ STEP 3: 4 themes clustered → prd/.themes.md
    - Onboarding friction (5/5) — primary
    - Workflow speed (3/5) — secondary
    - Pricing — CONTRADICTION between T01 ($50/seat acceptable) and T04 (free-only)
    - Compliance (1/5) — low-frequency outlier
```

The PM glances at `prd/.themes.md` and sees the contradiction explicitly flagged. Good — they remember this came up.

### STEP 4 — initial draft

```
✓ STEP 4: initial draft → prd/loopr-onboarding.md

Initial draft ready at prd/loopr-onboarding.md. Entering discovery loop.
Type /done when you want to finalize, /pause to save and exit, /status for a neutral snapshot.
```

The PM opens the draft in their editor. The evidence-anchored sections (Background, Target Users, User Stories, Functional Requirements, Risks) are populated with cited claims. Goals & Non-Goals, Success Metrics, Non-Functional Requirements, and Constraints all show just their headings and italic intent lines — deliberately blank, as documented. The discovery loop is where the PM fills them.

### Iteration 1 — the contradiction

The critic runs:

```
### Finding 1: CONTRADICTION
The Background & Problem section frames pricing as if there's consensus, but
the corpus contains a direct contradiction between T01 (00:05:12 — "we'd pay
$50/seat") and T04 (00:04:33 — "free is the only acceptable price"). Either
the Background should acknowledge this, or Goals & Non-Goals must take a
position on pricing before downstream sections can be confident.

### Finding 2: GOAL_METRIC_MISMATCH
Goals & Non-Goals is empty, but Functional Requirements §1 implies a metric
("reduce week-one drop-off"). Either the Goals section needs to be populated,
or the Functional Requirements should defer until it is.

### Finding 3: EVIDENCE_THIN
Risks & Open Questions raises compliance scope as the second-listed risk
based on a single mention in T03 (1/5). Either re-weight relative to evidence,
or note that compliance is a low-frequency theme worth watching, not a primary
risk for v1.

**Recommended starting point:** Finding 1
```

The PM presses Enter (default to recommended).

```
> Pricing comes up directly contradicting itself in the transcripts. What
> stance should the PRD take — acknowledge the contradiction in Background,
> resolve it in Goals & Non-Goals, or defer pricing out of scope for this PRD?
```

PM responds:

```
Defer pricing entirely. This PRD is about onboarding mechanics. Pricing is
a separate decision the founders are working through.
```

```
> Got it. To confirm — Goals & Non-Goals should explicitly call out "Pricing
> model" as a non-goal for this PRD scope?
```

PM responds:

```
Yes. And Background should note that pricing is contested but out of scope here.
```

PM types `/refine`. The drafter updates Background & Problem and Goals & Non-Goals. The orchestrator checkpoints state. Iteration count → 1.

### Iteration 2 — the goal/metric pair

Next critic pass surfaces:

```
### Finding 1: GOAL_METRIC_MISMATCH
Goals & Non-Goals now exists (good — added in iteration 1), but Success
Metrics is still empty. The Goal "reduce week-one onboarding drop-off"
needs at least one measurable signal.

### Finding 2: PERSONA_STORY_MISMATCH
Target Users declares "SMB ops manager" as the primary persona. User Story
§3 ("As a teammate, I want my onboarding tasks visible so that...") names
"teammate" — a persona not declared. Either add teammate as a persona, or
rewrite the story from the ops manager's perspective.

### Finding 3: EVIDENCE_THIN
(Still active from iteration 1 — PM skipped it. No closure penalty; just
re-surfaced.)

**Recommended starting point:** Finding 1
```

PM presses Enter, then engages the discussion on metric:

```
> What measurable signal would tell you week-one drop-off has improved?
```

```
Team milestone completion rate. We track 3 milestones; week-one completion
of all 3 should go from 38% to 60% in Q3.
```

```
> Got it. Counter-question: is there a metric you'd watch to make sure you
> haven't just *shifted* the friction (e.g., to support tickets)?
```

```
Good point. Support ticket volume tagged "onboarding" should be flat or down.
```

PM types `/refine`. The drafter populates Success Metrics. Iteration count → 2.

### Iteration 3 — addressing the lingering EVIDENCE_THIN

Critic re-surfaces the compliance risk. PM addresses it this time:

```
You're right — let me move that to a secondary risk and note it's 1/5.
```

`/refine`. Iteration count → 3.

### Iteration 4 — the persona/story alignment

PM addresses Finding 2 from iteration 2 (the teammate persona):

```
Rewriting that story from the ops manager's view: "As an SMB ops manager,
I want to see at a glance which teammates are stuck so that I can unblock
them before they churn from the rollout."
```

`/refine`. Iteration count → 4.

### `/status` check

PM is wondering how deep they are:

```
/status
```

```
iteration_count:         4
qa_turn_count:           7
sections_refined_so_far: Background & Problem, Goals & Non-Goals, Target Users,
                         User Stories, Success Metrics, Risks & Open Questions
finding_density (last 5 critic passes): 3, 3, 2, 2 findings
cost_estimate_usd:       3.40
```

PM thinks: "Good — Functional Requirements and NFR haven't been touched yet, and Constraints is still empty. There's more work, but I need to grab lunch."

### Day 1 — pause

```
/pause
```

```
> State saved with status: paused. Run /generate-prd to resume.
> Last checkpoint: 2026-05-15T12:47:33Z.
```

Orchestrator exits cleanly. PM closes the laptop.

---

## Day 2 — resume

PM opens Claude Code in the same project the next morning:

```
/generate-prd
```

### STEP 0 finds the paused session

```
> Found an unfinished discovery session for `loopr-onboarding` (4 iterations,
> last checkpoint at 2026-05-15T12:47:33Z). Resume, archive and start fresh,
> or cancel?
```

PM types: `Resume`.

```
> Loaded state. Skipping STEPS 1-4 (already complete).
> Entering discovery loop at iteration 5.
```

`prd/.state.json` is rewritten — `status` flips from `paused` back to `in_progress`. Loop resumes.

### Iteration 5 — Functional Requirements depth

Critic surfaces:

```
### Finding 1: SOLUTION_BIAS
Functional Requirements §2 reads "bulk-invite flow with REST API" — the
REST detail is implementation. Capabilities only at the FR level.

### Finding 2: COVERAGE_GAP
The "workflow speed" theme (3/5) is mentioned only in passing in Background.
Either elevate it to a User Story / Functional Requirement, or document
why it's deferred.

**Recommended starting point:** Finding 1
```

PM addresses both over the next two iterations. By iteration 7, the draft has:

- Background that acknowledges pricing contradiction + workflow-speed signal
- Goals & Non-Goals with explicit non-goals (pricing, enterprise compliance)
- Target Users with one persona, well-described
- 4 User Stories all traceable to the ops manager persona
- 5 Functional Requirements that describe capabilities, not implementations
- Success Metrics with primary + counter-metric
- Risks with the corpus contradiction + one low-frequency theme
- NFR still empty (PM judgment, to revisit before launch)
- Constraints with the Q3 ship window

### `/done`

PM is ready:

```
/done
```

### STEP 6 — finalize

The orchestrator builds the merged `transcript_index.json` and dispatches `prd-finalizer`. After ~10 seconds:

```
## Completeness

- **Non-Functional Requirements:** section is empty (heading + intent line
  only). Suggest either populating or removing before circulating.

## Citations

All citations resolve.

## Recommendations

- Functional Requirements §3 currently runs 4 sentences; trim to 1-2 for
  consistency with §§1, 2, 4, 5.
- Risks §1 could be tightened — the workflow-speed deferral rationale is
  good but the prose meanders.
- Consider reordering Functional Requirements: §4 (per-team milestone
  definition) is more foundational than §3 (inactivity reminders); a
  reader skimming top-down will want the foundation first.
```

```
> Completeness flagged: Non-Functional Requirements section is empty.
> Accept and ship (NFR can stay empty; some sections are honestly thin),
> or return to discovery (re-enter STEP 5)?
```

PM types: `Accept and ship`.

```
> NFR section stripped from the final PRD per the empty-is-better-than-fabricated rule.
> Front matter written:
>   generated_at: 2026-05-16T11:14:22Z
>   template_version: v1
>   state_version: 1
>   input_transcripts: [T01, T02, T03, T04, T05]
>   iteration_count: 7
>   qa_turn_count: 13
> State written: status=completed, completed_at=2026-05-16T11:14:22Z.
> PRD finalized at prd/loopr-onboarding.md.
> Run summary in prd/.state.json.
```

PM opens `prd/loopr-onboarding.md` — 8 sections (NFR stripped), every claim cited, contradictions surfaced not hidden, no fabricated content anywhere. Total time across both days: ~45 minutes of PM-engaged time (the LLM calls took maybe 4 minutes; the rest was reading, thinking, and typing). Cost estimate: $7.12.

---

## What the state file evolution looks like

For reference, here's the rough shape of `prd/.state.json` at three points in the session:

### After STEP 4 (initial draft, iteration 0)

```json
{
  "schema_version": 1,
  "run_id": "20260515-093014-loopr-onboarding",
  "feature_name": "loopr-onboarding",
  "status": "in_progress",
  "iteration_count": 0,
  "qa_turn_count": 0,
  "themes": [/* 4 themes */],
  "draft_sections": {},
  "qa_history": [],
  ...
}
```

### After /pause on Day 1 (iteration 4)

```json
{
  ...
  "status": "paused",
  "iteration_count": 4,
  "qa_turn_count": 7,
  "draft_sections": {
    "Background & Problem":   {...},
    "Goals & Non-Goals":      {...},
    "Target Users":           {...},
    "User Stories":           {...},
    "Success Metrics":        {...},
    "Risks & Open Questions": {...}
  },
  "qa_history": [/* 4 critic passes + 7 discussion turns + 1 user_command(/pause) */],
  ...
}
```

### After /done on Day 2 (iteration 7)

```json
{
  ...
  "status": "completed",
  "completed_at": "2026-05-16T11:14:22Z",
  "iteration_count": 7,
  "qa_turn_count": 13,
  "draft_sections": {/* 8 sections; NFR stripped at finalize */},
  ...
}
```

The full files validate against `generate-prd/schema/state.schema.json`. Synthetic versions of the in-progress, paused, and faulted states are in [`../tests/durability/state-fixtures/`](../tests/durability/state-fixtures/) — they're checked into the test suite specifically so resume behavior has a stable target.

---

## What this walkthrough doesn't show

- **Stuck-loop fault.** If PM had `/skip`'d the recommended finding 5 iterations in a row, the orchestrator would have written `status: faulted` and offered three choices. See [`../tests/durability/test_stuck_loop_detection.md`](../tests/durability/test_stuck_loop_detection.md).
- **Context compaction.** In a long session (~25-30 deep iterations), the orchestrator would compact older Q&A turns into a "Discovery so far" summary at ~70% of the context limit. The on-disk state remains intact regardless. See [`../tests/durability/test_context_compaction.md`](../tests/durability/test_context_compaction.md).
- **Faulted resume with diagnostic.** Same shape as paused-resume but the diagnostic is surfaced verbatim. See [`../tests/durability/test_resume_faulted.md`](../tests/durability/test_resume_faulted.md).

If you run a real session that exercises any of these, capturing the chat transcript as a follow-on doc here is worth it.
