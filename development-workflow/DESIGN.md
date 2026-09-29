# Design: `development-workflow` skill

Status: draft, pending user review
Date: 2026-09-28
Author: Claude (brainstorming session with Mike Dulog)

## Problem

CLAUDE.md's 🔄 Development Workflow (Ouroboros → Superpowers) section describes
a multi-phase pipeline (ambiguity routing → Seed → design review/plan →
isolate/execute → evaluate → finish/push) as prose. CLAUDE.md says outright,
in 🏛️ Core Architecture phase 4: "This is a convention Claude applies at the
right moment, not a harness-enforced hook — CLAUDE.md prose doesn't execute
itself." In practice this means the pipeline only runs if the model happens
to recall and apply a long section correctly, every time.

## Goal

Convert that section into a Claude Code skill (`~/.claude/skills/development-workflow/`)
that functions as a **resumable state machine**, not a fire-and-forget
automation — it stops at every gate CLAUDE.md already makes mandatory and
waits for the human. Entry into the pipeline is **explicit, not
auto-triggered** (see Architecture, below) — you invoke it deliberately, the
same way `ooo` is already a deliberate trigger for Ouroboros onboarding. Once
the skill exists and is verified, the 🔄 Development Workflow section in
CLAUDE.md is deleted and replaced with a short pointer, along with every
cross-reference elsewhere in the file that currently points at its numbered
steps.

## Non-goals (v1)

- Ralph convergence loops, `evolve_step`, PM interviews, lateral-think
  personas, and brownfield scanning are **not** actively branched into by
  this skill. They remain separately-triggered tools the user invokes
  directly.
- `ooo auto` (`ouroboros_start_auto`) is explicitly excluded — CLAUDE.md
  names it as a tool that "owns its own execution path end-to-end and stays
  outside this chain." This skill must not intercept requests intended for
  `ooo auto`.
- Only the core interview→seed→execute→evaluate flow, plus three specific
  named sub-rules (below), are in scope.

## Architecture

**Pattern: orchestrator (saga), not choreography.** Single-responsibility
test: this skill changes only when the *sequence of phases* changes — never
when an individual phase's internal behavior changes (brainstorming's own
`<HARD-GATE>`, TDD's red-green-refactor, verification-before-completion's
evidence requirement are untouched and un-duplicated).

**Entry is explicit, not description-based auto-trigger.** Early drafts of
this design assumed `development-workflow` could compete for auto-trigger
priority against `superpowers:brainstorming` the way any two skills with
overlapping descriptions might. That assumption doesn't hold: `using-superpowers`
(a plugin skill, not user-owned) explicitly instructs, under `## The Rule`,
"Before entering plan mode: if you haven't already brainstormed, invoke the
brainstorming skill first" — and separately, under `## Skill Priority`, gives
a worked example, `"Let's build X" → superpowers:brainstorming first`, that
matches ordinary feature-request phrasing almost exactly. (Correction: an
earlier draft of this design misattributed that worked example to the
`<EXTREMELY-IMPORTANT>` block — a spec-auditor pass found it actually sits 14
lines after that block closes, which is generic skill-invocation enforcement,
not brainstorming-specific. The underlying argument is unaffected: `## The
Rule`'s line alone is sufficient reinforcement that a custom skill
description has no comparable counterpart.) A custom skill description has
no comparable reinforcement and would likely lose that race silently: `brainstorming` fires
alone, produces a plausible-looking design, and the Ouroboros interview/Seed
step never runs — with no error, no warning, and no indication anything was
skipped. That's worse than the status quo, not better, because it creates
false confidence that the pipeline ran when it didn't.

Fix: **entry into `development-workflow` is a deliberate, explicit trigger**,
extending the existing `ooo` convention (already used for Ouroboros
onboarding) rather than relying on fuzzy skill-description competition. A
`UserPromptSubmit` hook was considered as a second, automatic layer, but is
deliberately deferred (see Rejected alternatives) — this is a conscious
complexity-budget trade-off: explicit invocation is fully deterministic and
requires no new code, at the cost of not automatically triggering when you
forget to say the trigger phrase.

**Confirmed requirement, not just an accepted trade-off: this skill must not
become the only door into engineering work.** `brainstorming`, direct
Ouroboros tool calls, and every other existing workflow stay fully reachable
on their own, exactly as they work today — `development-workflow` is
additive and opt-in, never a gate other skills have to pass through. This is
why explicit invocation was the right call over anything that tries to
intercept or absorb those paths (a hook that rewrites intent, or a skill
description broad enough to out-compete `brainstorming` for every feature
request, would both risk exactly the lock-in this requirement rules out).

**Rejected alternative — description-based auto-trigger competing with
`brainstorming`.** Rejected because it's not actually deterministic — it's
the same category of soft, in-context competition CLAUDE.md prose already
suffers from, just with an extra voice added to the pile.

**Rejected alternative — `UserPromptSubmit` hook for automatic detection.**
Considered as a way to catch cases where you forget the explicit trigger.
Deferred for v1 per the complexity-budget principle: a hook requires writing
and maintaining pattern-matching code with its own false-positive/negative
surface, to solve a problem (forgetting to invoke it) that hasn't been
demonstrated to actually occur yet. Revisit only if explicit invocation proves
insufficient in practice — YAGNI until then.

**Rejected alternative — split into a "router" skill (phases 0-1) and a
"continuation" skill (phases 2-5).** Rejected because it reintroduces the
two-places-to-look problem this project exists to eliminate, for an SRP
benefit that doesn't matter when both halves share one trigger moment and
one state (the todo list).

## State machine

Once explicitly invoked, the skill applies these phases:

| Phase | Entry condition | Action | Exit condition | Human gate |
|---|---|---|---|---|
| 0. Classify | Skill explicitly invoked | Apply `EnterPlanMode`'s own bar (new feature / multi-file / ambiguous / multi-step / architectural) to decide if the pipeline applies at all | Classified: out-of-scope (stop, do nothing further, e.g. a one-line typo fix) / in-scope | No |
| 1. Requirements→Seed | In-scope | Are goal, constraints, AND success criteria **all** already stated? No → `ouroboros_interview` (conversational). Yes → `ouroboros_generate_seed` directly, no interview. | **Invariant: a Seed YAML is always produced**, regardless of which path was taken — Phase 2 never starts without one | **Yes, if interview ran** — multi-turn Q&A. No gate if `generate_seed` path taken. |
| 2. Design review & plan | Seed exists | `superpowers:brainstorming` (Seed as context). Brainstorming's own classification then determines whether this is bounded (short in-chat design, no plan document, proceed directly to Phase 3) or architectural (→ `superpowers:writing-plans`) | Bounded: design approved. Architectural: plan approved, `ExitPlanMode` called | **Yes — hard gate** either way: design approval (bounded) or spec approval then plan approval (architectural) |
| 3. Isolate & execute | Design/plan approved | Worktree (🌿 When to Use Git Worktrees) → `superpowers:test-driven-development` per task, `superpowers:subagent-driven-development` for independent fan-out → commit per 🔁 Commit Cadence During Implementation (only commit green, explicit staging, never onto main/master) | All tasks done | No (routine green checks only) |
| 4. Evaluate | Execution done | **Always** run the project's real test command per `verification-before-completion`'s IDENTIFY/RUN/READ/VERIFY gate — unconditional, not a fallback; mechanical correctness applies regardless of whether a Seed exists. **Additionally** (Phase 1's invariant guarantees a Seed always exists for any in-scope task), invoke `ouroboros_qa`: `artifact` = the implementation's diff/output, `seed_content` = the current Seed, `quality_bar` = a restatement of the Seed's acceptance criteria. | Both a test result and a QA verdict returned | **Soft gate** — a below-threshold QA verdict is reported to you as a new visible step, never auto-retried (Ralph is out of scope) |
| 5. Finish & push | Evaluate/verification passed | `finishing-a-development-branch` → `verification-before-completion` → doc-sync check | Docs verified in sync | **Yes — hard gate**: push always manual, confirm-first |

**Why `ouroboros_qa`, not `ouroboros_evaluate` (design history, corrected after live testing):** the original design routed this step through `ouroboros_evaluate`/`ouroboros_start_evaluate`'s three-stage pipeline (mechanical → semantic AC-compliance → optional consensus). Two rounds of dry-run testing found that mechanism structurally incompatible with this project's stated architecture (Ouroboros specs and validates; Superpowers plans and executes; Ouroboros never runs implementation itself):

1. `ouroboros_evaluate`/`start_evaluate` hard-require a `session_id`. A bounded, budget-limited spike (schema-only, no live call — see the project's own bounded-spike-investigation discipline) confirmed sessions in Ouroboros's data model are created *by execution* (`ouroboros_execute_seed`/`start_execute_seed`'s own schema: "if not provided, a new session is created" — as a side effect of running the seed, not as a standalone registration). A Seed produced via the interview-less `generate_seed` path never executes anything, so it structurally can never have a session_id — independent of any workaround.
2. A live test confirmed the danger mode concretely: substituting a Seed's `seed_id` as a fake `session_id` passes schema validation and returns a *plausible-looking* `REJECTED` verdict, but the evaluator's own reasoning showed it graded against `Goal: "Not specified"`/`Constraints: "None specified"` and a fabricated acceptance criterion — i.e., a session-keyed lookup silently fell back to empty state instead of erroring. This is worse than a loud failure.
3. A follow-up desk-check of `execute_seed`/`start_execute_seed` (stopped safely at the schema-review step per the bounded-spike discipline, before any live call) confirmed those tools are the actual `ooo run` execution engine (`max_iterations` default 10, `model_tier`, `auto_evolve`→Ralph chaining) — not a lightweight session-minting call. Using them just to obtain a session_id would mean handing Ouroboros real execution authority, contradicting the stated architecture.
4. Six other session-lifecycle-shaped tools (`session_status`, `session_signal`, `record_conductor_decision`, `query_events`, `query_projection`) were checked and are all either read-only queries against an *existing* session or tied to Ouroboros's own Active Conductor orchestration — none register a session for externally-performed work.
5. `ouroboros_qa`'s schema, by contrast, requires only `artifact` and `quality_bar` — no `session_id`, required or optional. It explicitly accepts `seed_content` ("optional seed YAML for additional context: goal, constraints") and was already used successfully, session-less, in this project's own scenario-5 dry run. This is the tool that actually matches "grade an externally-produced artifact against a spec Ouroboros generated," which is precisely this project's architecture.

**Trade-off accepted:** `ouroboros_qa` doesn't run `evaluate`'s Stage 1 mechanical checks (lint/build/test) or Stage 3's optional multi-model consensus. Stage 1's coverage is why `verification-before-completion`'s gate is now unconditional rather than an "otherwise" branch — the two tools cover different concerns and both always run. Stage 3 was opt-in by default anyway (`trigger_consensus: false`), so nothing is lost there in practice. This also eliminates the `auto_evolve`/Ralph-chaining concern entirely: `ouroboros_qa` has no `auto_evolve` parameter, so there is nothing to explicitly disable.

### Seed versioning (invalidation rule)

The Seed is the single source of truth. Three places in the pipeline can revise
it after a spec or plan already exists downstream:

1. Mid-brainstorming discovery (brainstorming's questions reveal the Seed's
   requirements were incomplete or wrong).
2. A Phase 4 rejection that traces back to the Seed being wrong, not the
   implementation (see the fork below).
3. Any future manual or QA-triggered refinement beyond the one instance
   already modeled in the QA-revise rule.

**Rule: any Seed revision, regardless of trigger, invalidates every spec and
plan derived from the prior version.** The pipeline returns to Phase 2,
re-runs `brainstorming` with the updated Seed as context, and requires a fresh
design/plan approval before Phase 3 resumes or continues. A stale spec is
never silently carried forward — this mirrors the exact staleness problem the
spec-auditor caught in CLAUDE.md's own cross-references, one layer down.

**Version identifier: don't invent one — Ouroboros already tracks Seed
revision history.** Ouroboros persists a full audit trail at
`~/.ouroboros/seed-revisions/<revision_key>.md` on every revision — iteration
number, QA score, all candidates considered, accept/reject decisions, and a
diff against the previous iteration (existing, unmodified Ouroboros behavior,
not something this skill adds). `state.json` (see Artifact storage
convention) records the `revision_key` a given `design.md`/`plan.md` was
built against; checking staleness means comparing that recorded key against
the Seed's current revision key, not maintaining a parallel version scheme.

**Phase 4 rejection forks into two repair paths**, since a below-threshold
`ouroboros_qa` verdict doesn't by itself say which is wrong:
- **Implementation wrong, Seed still valid:** the QA verdict shows the code
  doesn't satisfy correct acceptance criteria → normal repair, back to
  Phase 3, no Seed change, no invalidation.
- **Seed wrong:** repair investigation shows the acceptance criteria or goal
  were mis-specified → this is a Seed revision, which triggers the
  invalidation rule above and returns to Phase 2, not Phase 3.

`ouroboros_measure_drift` (goal/constraint/ontology drift of current output
vs. the original Seed) is a candidate future signal for helping distinguish
these two paths automatically, but is not required for v1 — noted as a
possible enhancement, not built against now. `ouroboros_lineage_status` and
`ouroboros_evolve_rewind` are evolutionary-lineage tools belonging to the
Ralph/evolve machinery already excluded under Non-goals; they don't apply to
Seed versioning as scoped here.

### Named sub-rules (migrated in full, not dropped)

1. **QA-revise rule** (fires during Phase 1→2 transition): if `ouroboros_qa`'s
   verdict on a generated Seed is REVISE or FAIL, always run the
   Wonder→Reflect→Refine→Restate refinement pass before invoking brainstorming.
   Never hand-edit the Seed YAML directly to fix QA findings.
2. **Security-review gate** (fires within Phase 2): if the design touches
   authentication, authorization, or a public network surface, run
   `security-review` (or the `pr-review-toolkit:code-reviewer` agent) against
   the design section before invoking `writing-plans`.
3. **Fan-out model assignment** (fires within Phase 1, during interview
   advisory fan-out): default mechanical/low-judgment lanes (`data_context`,
   `answer_simplifier`) to Haiku; reserve Sonnet/Opus for lanes requiring
   deeper reasoning (`ambiguity_contrarian`, gap-hunting, lateral
   `contrarian`/`architect` personas).

## State tracking

One `TodoWrite` entry per phase 1–5, created the moment Phase 0 classifies a
request as in-scope. Each entry is prefixed `[dev-workflow]` so the skill can
distinguish its own state from unrelated todos in the same session (e.g. a
subagent-driven-development task list from a different piece of work). On
every new turn, the skill's first action is: check for an open todo list with
that prefix. If one exists with incomplete items, resume at the first
incomplete phase. Otherwise, this is a fresh Phase 0 classification. This is
what lets the pipeline survive context compaction or a new session without
re-running the interview from scratch — **provided** the actual artifacts are
durably stored (see Artifact storage convention below); the todo list alone
is a phase pointer, not a state container.

### Artifact storage convention

Fixes three related gaps found during design review: (1) the Seed defaults to
existing only as inline chat text — CLAUDE.md itself notes the interview
skill "returns it inline; it only persists to `~/.ouroboros/seeds/` on the
CLI `ouroboros init` path" — so a context compaction between Phase 1 and
Phase 4 could lose it entirely; (2) a todo checkbox can't carry the concrete
references later phases need (which Seed revision a spec/plan was built from,
for the invalidation rule; which worktree is active); (3) specs should never
be committed to the target repo, and must keep working even when the target
isn't a git repo at all (this happened during this very design session).

**Working artifacts — Seed, spec, plan — are never written into the target
repo.** They live centrally at
`~/.claude/dev-workflow-runs/<repo-slug>/<YYYY-MM-DD>-<task-slug>/` —
deliberately a *sibling* of `~/.claude/skills/development-workflow/`, not
nested inside it: that directory is skill *definition*, scanned and synced by
the harness, and accumulating unbounded per-run mutable state inside it would
mix the two. Phase 0 creates this directory the moment it classifies a
request as in-scope, deriving `<repo-slug>` from the target directory's git
remote or folder name when one exists, and falling back to the working
directory's basename (or `no-repo` if that's not meaningful either) when it
doesn't — the fallback matters because gap (3) above specifically requires
this to keep working outside a repo entirely.

- `seed.yaml` — the current Seed, durably persisted the moment Phase 1
  produces or revises it, plus the `revision_key` of its latest entry in
  Ouroboros's own `~/.ouroboros/seed-revisions/` history (the version
  identifier the invalidation rule checks against — see Seed versioning)
- `state.json` — current phase, worktree path, and pointers to `design.md`/
  `plan.md` with the `revision_key` each was built against. No `session_id`
  is tracked here: Phase 4 uses `ouroboros_qa` (session-less by schema) rather
  than `ouroboros_evaluate`, so there is no session identifier to cache in
  the first place — see Phase 4's design-history note for why
- `design.md` — brainstorming's spec, redirected here instead of its own
  default `docs/superpowers/specs/` location (brainstorming's own convention
  explicitly allows this override)
- `plan.md` — `writing-plans`'s output, redirected here instead of its own
  default `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md` location —
  the exact twin of brainstorming's override, documented the same way in
  `writing-plans`'s own skill file — since it's a pre-validation working
  artifact, not project documentation

Note: Ouroboros also has its own default worktree root
(`~/.ouroboros/worktrees/`). This skill's `state.json` doesn't compete with
it — it records whichever worktree path Phase 3 actually used, which is
governed by CLAUDE.md's own 🌿 worktree rules, not Ouroboros's default.

Because this lives outside the repo, it's unaffected by which worktree is
currently checked out, and it works identically whether or not the target
directory is a git repo. It also means brainstorming's own "commit the
design document to git" instruction is suppressed, not just its default file
location — there's nothing in the target repo to commit, and in the
non-git-repo case "commit" has no meaning to begin with.

**Project documentation is a separate category and is untouched until
Phase 5.** README, ADRs, and any docs-as-code baseline content only get
updated *after* Phase 4 validates success, per the existing 🚢 Before Push
doc-sync check — never before, and never from the working artifacts above.

## Error handling / edge cases

- **QA verdict below threshold:** report findings, stop, and classify which of
  the two repair paths under Seed versioning applies (implementation wrong vs.
  Seed wrong) before proceeding — never assume it's an implementation-only
  fix. Treat next step as a new visible planning step (not hidden
  auto-retry). Since Ralph is out of scope (and `ouroboros_qa` has no
  `auto_evolve` behavior to chain into it regardless), repeated below-threshold
  verdicts just keep surfacing each time — the user can manually invoke
  `ouroboros_ralph` or `ouroboros_lateral_think` if they want convergence
  looping.
- **Mid-pipeline scope upgrade:** brainstorming's own ratchet ("hidden
  complexity upgrades the path, never downgrades") already handles a bounded
  task turning out to need the architectural path. The skill doesn't fight
  this — Phase 2 defers entirely to brainstorming's own classification rather
  than hardcoding a path.
- **Entry reliability:** resolved by explicit invocation (see Architecture) —
  if you didn't say the trigger phrase, you get ordinary ad hoc `brainstorming`
  behavior, not a silently broken pipeline. This is an intentional trade-off,
  not an unaddressed gap.
- **Trivial requests:** Phase 0 must correctly classify these as out-of-scope
  and do nothing, or every one-line fix would spawn a todo list and an
  interview.
- **`ooo auto` requests:** if a request is clearly intended for
  `ouroboros_start_auto` (an end-to-end autonomous run), this skill must not
  intercept it — see Non-goals.
- **Resolved: `session_id` on the interview-less path.** This was originally
  logged as an open risk (would `ouroboros_generate_seed`'s interview-less
  path yield a `session_id` usable by Phase 4's evaluate call?). A live test
  confirmed the answer is no, and confirmed why: sessions are created by
  execution, not Seed generation, and this skill's Phase 4 no longer uses a
  session-keyed tool at all — see Phase 4's design-history note. No open risk
  remains here.

## CLAUDE.md impact

**Superseded by the Scope expansion section below** — this bullet list
described the original, narrower plan (delete only the 🔄 Development
Workflow subsection, keep 🏛️ Core Architecture, patch four cross-references,
add one line to 🧩 Skills). The user later decided to remove the entire
umbrella instead, which deleted 🏛️ Core Architecture and 🧩 Skills
(Superpowers) outright rather than editing them. Kept here for history, not
as a current instruction:

- Delete the 🔄 Development Workflow subsection (5 numbered steps + 3 named
  sub-bullets) — content now lives in the skill.
- ~~Keep 🏛️ Core Architecture as a short conceptual "why"~~ — superseded;
  the whole section was deleted along with the rest of the umbrella.
- Fix every cross-reference elsewhere in the file that currently points at
  "🔄 Development Workflow": 🏛️ Core Architecture phase 1, 📐 When to Use
  Plan Mode, 🧠 When to Brainstorm First, and the "Ouroboros —
  Specification-First AI Development" section. Of these, only 🧠 Brainstorm
  First and the Ouroboros section still exist post-expansion; the other two
  were deleted, not fixed.
- ~~Add one line to 🧩 Skills (Superpowers)~~ — superseded; that section no
  longer exists. The equivalent pointer now lives in 🔄 Development Workflow
  under 🧭 General Engineering Practices (CLAUDE.md line ~263).

## Verification plan

- Per CLAUDE.md's own "🕵️ Auditing Generated Instructional Documents" rule
  (explicitly covers "CLAUDE.md/AGENTS.md edits, and skill files"): run
  `spec-auditor` against both the new `SKILL.md` and the edited `CLAUDE.md`
  before either is considered final.
- Per `writing-skills`' own testing convention
  (`testing-skills-with-subagents.md`), dry-run the finished skill through its
  full RED → Verify RED → GREEN → Verify GREEN → REFACTOR sequence before
  calling it done — the doc's stated core principle is "if you didn't watch
  an agent fail without the skill, you don't know if the skill prevents the
  right failures":
  - **RED (baseline, skill absent):** run each scenario below without the
    skill installed and observe what actually happens.
  - **GREEN (skill present):** re-run the same scenarios with the skill and
    confirm correct routing.
  - **REFACTOR:** close any loopholes the GREEN runs exposed while staying
    compliant, per the convention's own close-loopholes step.
  - Scenarios: a trivial one-line fix (must NOT trigger the pipeline); an
    ambiguous multi-step request (must route to `ouroboros_interview`); a
    clear, settled request (must route to `ouroboros_generate_seed` directly);
    a design touching auth (must trigger the security-review gate); a Seed
    that receives a QA REVISE verdict (must trigger the
    Wonder→Reflect→Refine→Restate loop).

**Status (2026-09-28): first full dry-run round completed.** All 5 scenarios
ran RED+GREEN. Findings: two Medium spec-auditor findings were fixed
(security-review gate restored as an unconditional CLAUDE.md rule so the ad
hoc path retains it; the architectural path's two-step approval wording was
corrected). One High finding — the settled-request scenario's Phase 4
`session_id` gap — was confirmed as real and dangerous (a faked session_id
produced a plausible-looking but meaningless verdict) and led to the Phase 4
redesign documented above (`ouroboros_qa` instead of `ouroboros_evaluate`).
That redesign was then re-verified live: the corrected Phase 4 was run
end-to-end against the existing Seed and completed implementation from the
original failing test (no Phase 1-3 rework needed). Result: PASS — mechanical
check 3/3, `ouroboros_qa` scored 0.93/1.00, and its reasoning traced every
judgment to a specific, named acceptance criterion from the real Seed (even
flagging one, AC4's call-count assertion, as under-tested rather than
ignoring or hallucinating it). No "Not specified," no fabricated criteria —
the specific failure mode that broke the old `evaluate`-based design does not
reproduce. Phase 4 is now considered fully closed.

## Scope expansion: full CLAUDE.md umbrella absorption (2026-09-28)

After the dry-run round above, the user explicitly and repeatedly decided
(across several rounds of pushback) to remove CLAUDE.md's entire "🤖 Claude
Code Workflow Preferences" umbrella — not just the already-migrated 🔄
Development Workflow subsection, but all 18 subsections (Plan Mode, Git
Worktrees, Parallel Agents, Brainstorm-First, Stop-and-Ask, Context7,
Language/Stack Defaults, TDD, Commit Cadence, Before-Claiming-Complete,
Finishing, Before-Push, Docs-as-Code Baseline, and Auditing Generated
Instructional Documents) — and to have `SKILL.md` absorb everything
pipeline-relevant so the skill reads as a fully independent, self-contained
pipeline definition with no fragile cross-references into CLAUDE.md prose.

Two subsections were deliberately left out of the migration, having no home
in a pipeline skill: 📁 Project-Level Overrides (config-file-location
convention, unrelated to running a pipeline) and 🧩 Skills (Superpowers)'s
general skill-checking mandate (circular to restate inside the skill it
would be checking for; already covered by `using-superpowers`).

**Separately, the same session found and fixed a hardcoded personal
dependency**: `SKILL.md`'s migrated plan-approval-audit step named the
user's personal `spec-auditor` agent directly. Reworded to describe the
*purpose* (verify file paths/names/claims against the codebase) with
`spec-auditor` as an example, falling back to a manual check when no
dedicated auditing agent is configured — full strength in this environment
(where the agent exists), still meaningful in one that lacks it.

**A fourth spec-auditor pass, run specifically because this absorption had
never been independently checked, found real problems** — the umbrella
removal correctly emptied CLAUDE.md (verified: zero dangling references to
any of the 18 deleted headings), but the absorption into `SKILL.md` had
distorted or dropped several rules in the process:

- **High — `ExitPlanMode` was only called on the architectural branch**,
  inherited from a rule that was originally path-agnostic. A bounded-path run
  would have stayed stuck in `plan` permission mode into Phase 3, which
  blocks the writes that phase needs to do. Fixed: moved `ExitPlanMode` to
  the Phase 2 hard-approval gate, which already covers both paths.
- **High — the "🕵️ Auditing Generated Instructional Documents" rule was lost
  entirely**, from both files. It's a general document-authoring rule (fires
  on any generated runbook/ADR/skill file, not specifically on pipeline
  runs), so it was the wrong candidate for `SKILL.md` in the first place.
  Fixed: restored to CLAUDE.md, genericized the same way as the plan-audit
  step above (no hardcoded `spec-auditor` dependency).
- **High — the commit-cadence "this overrides the default 'only commit when
  asked'" clause was dropped**, leaving Phase 3's per-step commit instruction
  in live conflict with the harness's own default. Fixed: restored the
  override clause explicitly.
- **Medium — five formerly-unconditional rules became reachable only through
  this opt-in, never-auto-triggered skill**: Context7 lookups, Language/Stack
  defaults, TDD, `EnterPlanMode`-on-brainstorming (narrowed from "whenever
  brainstorming or interview is invoked" to "only inside Phase 1"), and
  Brainstorm-First itself (absent from both files). This is the exact same
  failure mode already caught once for the security-review gate earlier in
  this project — a universal engineering rule silently becoming
  skill-gated. Fixed: restored all five as unconditional rules in a new
  CLAUDE.md section (see below), with `SKILL.md` keeping its
  phase-specific elaboration alongside.
- **Medium — Phase 5's doc-baseline backstop mislabeled a legitimate bounded-
  path case as a process gap** (on the bounded path, Phase 2 never runs the
  doc-baseline check *by design*, so Phase 5 surfacing it first is the
  intended path, not a missed step). Fixed: qualified the causal wording to
  the architectural path specifically.
- **Medium — parallel-agents guidance lost its load-bearing guard**: "never
  for tasks with sequential dependencies," plus the
  `superpowers:dispatching-parallel-agents` skill name and the
  concurrent-research use case. Fixed: restored, as a universal rule (not
  pipeline-specific — parallel dispatch applies to ad hoc work too).
- **Medium — the default-branch commit fallback was dropped**: "if the work
  is already sitting on the default branch, stop and ask" had no equivalent
  once Phase 3's worktree-isolation step became conditional (git repos
  only). Fixed: restored as an explicit stop-and-ask fallback.
- **Low, several**: Context7's tool names were abbreviated rather than the
  real invocable MCP identifiers (fixed); Phase 3's Stop-and-ask content was
  fully duplicated against the new standalone section rather than pointing
  to it (trimmed to a pointer plus the one phase-specific clause); 📁
  Project-Level Overrides was confirmed correctly absent from `SKILL.md` but
  wrongly absent from CLAUDE.md too (restored); the general skill-registry
  mandate remains intentionally absent, covered by `using-superpowers`.

**Net result**: CLAUDE.md gained a new "🧭 General Engineering Practices"
section holding the rules identified as needing to stay universal — 📁
Project-Level Overrides, 🧠 When to Brainstorm First (with the corrected
path-agnostic `EnterPlanMode` pairing), 🧪 When to Use TDD, 🚀 When to Use
Parallel Agents, 📚 Documentation Lookups (Context7), 🛠️ Language & Stack
Defaults, ⏹️ When to Stop and Ask, 🚢 Before Push, 🕵️ Auditing Generated
Instructional Documents, and a short 🔄 Development Workflow pointer to this
skill. This is not a reversal of the umbrella-removal decision — none of
the pipeline-orchestration mechanics (which skill fires in which phase, in
what order, producing what artifacts) moved back. It's the same correction
already applied once to the security-review gate, generalized to every rule
that turned out to share its property: genuinely universal, not
pipeline-specific, and therefore wrong to gate behind an explicitly-invoked,
never-auto-triggered skill.

**A fifth spec-auditor pass, run to verify the fourth pass's fixes, found
two more instances of this same pattern** — one the fourth pass introduced,
one it never checked for:

- **`EnterPlanMode` was restored without its `ExitPlanMode` counterpart.**
  The M1 fix made ad hoc `superpowers:brainstorming` correctly enter plan
  mode, but nothing told it to exit — the exact failure class H1 fixed,
  relocated from the pipeline's bounded path to the ad hoc path entirely.
  Fixed: added the `ExitPlanMode` bullet to 🧠 When to Brainstorm First,
  explicitly not delegated to any skill.
- **The "must not be skill-gated" test was applied to five rules but not
  checked against four others with the same property**:
  `verification-before-completion`, `docs-as-code-baseline`,
  `using-git-worktrees`, and the pre-push doc-sync check. A decision was
  made, not left implicit: the first three are backstopped by their own
  auto-triggering skill descriptions (each fires on its own "use when..."
  match regardless of CLAUDE.md content), so leaving them pipeline-elaborated
  in `SKILL.md` only is deliberate, not an oversight. The fourth — the
  pre-push doc-sync check — is plain prose with no skill backstop of its
  own, so it was restored as a 🚢 Before Push subsection alongside the
  others. "Exactly the rules that needed to stay universal" above is
  corrected by this addition — the fourth pass's list wasn't exhaustive.

This fourth-pass audit's fixes have not yet been independently re-verified
by a fifth pass — the fixes were applied directly based on the audit's
findings, following the same fix pattern already validated three times
prior in this project.

## Deliverables

1. `~/.claude/skills/development-workflow/SKILL.md` (the directory already
   exists and holds this design doc; only the skill file itself is new)
2. Edits to `~/.claude/CLAUDE.md` per the CLAUDE.md impact section above,
   plus the 🧭 General Engineering Practices section added during the scope
   expansion
3. Auditing-agent findings resolved for both files, across four independent
   passes
4. RED+GREEN subagent dry-run results for the five scenarios above (run
   against the pre-expansion `SKILL.md`; not yet re-run against the
   expanded version)
