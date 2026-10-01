# Design: `development-workflow` skill

Status: in use; later changes are recorded in the 2026-09-29 backport section
the "CLAUDE.md state, 2026-09-30" note above "CLAUDE.md impact", and the dated
sections at the end (2026-09-30, 2026-10-01). Where an older
section says Phase 0 classifies and then creates state, read it as superseded:
Phase 0 is now "classify and preflight" and creates state at its step 5.
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

## CLAUDE.md state, 2026-09-30 (read before "CLAUDE.md impact" and "Scope expansion")

The sections "CLAUDE.md impact" and "Scope expansion: full CLAUDE.md umbrella
absorption" describe a global `CLAUDE.md` that no longer exists in
that form. The global `CLAUDE.md` carried the full 🤖 Workflow Preferences umbrella
again (commit `2cf5d46` rewrote the repo copy to match it), and on
2026-09-30 it was offloaded again, this time into the skill by user
decision. Diff of the headings before and after:

- Removed from `~/.claude/CLAUDE.md` (now owned by this skill, with an
  auto-triggering superpowers skill as backstop for all but the last):
  🌳 Git Worktrees, 🚀 Parallel Agents, 🧠 Brainstorm First, 🔴 TDD,
  ✅ Before Claiming Work Complete, 🏁 When Implementation Is Complete, and
  🚢 Before Push. Pre-push doc-sync has no backstop outside a pipeline run;
  that was disclosed to the user and accepted.
- Kept in `CLAUDE.md`: 📁 Project-Level Overrides, ⚡ Skills, 📐 Plan Mode,
  ⏹️ Stop and Ask, 🛠️ Stack Defaults, 🔁 Commit Cadence (deliberately in both
  places), 🕵️ Auditing Generated Instructional Documents, and a shortened
  🔄 Development Workflow pointer.
- 🗂️ Memory moved out of the umbrella into Personal Preferences.

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
Language/Stack Defaults (values corrected 2026-09-30 from TypeScript/Jest to C#/.NET + TUnit and
React/TypeScript + Jest to match the current global CLAUDE.md; the copy stays
in the skill by design and needs re-checking when CLAUDE.md changes), TDD, Commit Cadence, Before-Claiming-Complete,
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
(Superseded 2026-10-01: Phase 2 now dispatches the mode C reviewer from
`references/reviewer-brief.md`; no `spec-auditor` is named. See the Mode C
section at the end.)

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

This fourth-pass audit's fixes were not independently re-verified at the
time. Later audits, described in the 2026-09-29 backport section, covered
them.

## Model policy (added 2026-09-29)

Intent: discovery, specs, plans and validation on Opus; implementation on
Sonnet. Phases 1–2 already satisfied this through `opusplan` (Opus while
permission mode is `plan`, Sonnet after `ExitPlanMode`). Phase 4 did not,
because validation runs after `ExitPlanMode`.

- **Review agents.** `silent-failure-hunter`, `type-design-analyzer`,
  `pr-test-analyzer` and `comment-analyzer` default to `model: inherit`
  (Sonnet outside plan mode), so `CLAUDE.md` now says to dispatch all four
  with `model: opus` (**superseded 2026-09-30**: the rewritten global
  `CLAUDE.md` has no such line; pipeline reviewers get `model: opus` from
  `references/reviewer-brief.md` and `references/phase3-execution.md`, and
  ad hoc spot-check agents inherit the session model). `comment-analyzer` was briefly exempted as a mechanical,
  non-blocking check; the exemption was dropped in favor of a rule with no
  special cases. Rejected:
  wrapper agents that copy the plugin agents with a pinned model, since they
  drift from upstream and a plugin update would not carry the pin.
- **`ouroboros_qa`.** It has no model parameter and ignores the session
  model. It resolves `OUROBOROS_QA_MODEL`, then `llm.qa_model` (only when
  non-default), then `evaluation.semantic_model` (plugin Opus pin). An
  earlier draft of this change assumed QA ran on Sonnet; that was wrong, QA
  was already on Opus. `llm.qa_model` was briefly pinned to a full Opus ID,
  then reset to the shipped default: a pin buys a slightly newer model today
  but loses the plugin's automatic bumps, so QA now follows the plugin's Opus
  pin.
  **Superseded 2026-09-30 (Ouroboros 0.55.3).** QA is now a standard-tier
  role: with no config it resolves to the `sonnet` alias, and the
  `evaluation.semantic_model` fallback is gone. Decision: keep QA on Opus.
  `~/.ouroboros/config.yaml` (did not exist before) now sets `models.pin:
  true` and `llm.qa_model: opus`. Verified with the resolver in a throwaway
  `HOME` and then the real one: `qa` resolves to opus (source `pin`) and
  every other role is unchanged. Rejected: `models.default` / `OUROBOROS_MODEL`
  (applies to every role, including the Haiku and Sonnet ones), and env vars
  in `settings.json` (unclear they reach the MCP server process). Trade-off:
  `opus` is an alias, so QA still follows the Claude CLI's newest Opus
  without further config, but `models.pin` is now on globally.
- **`/fast`.** Forces Opus unless `disableFastMode` applies (untested at
  runtime), so it must be off in Phase 3 for the Sonnet-implementation goal
  to hold. It is an interactive user command the agent can neither run nor
  inspect, so Phase 3 makes it a stop-and-ask item.
- **(Superseded, see above) `llm.qa_model` must stay absent from `~/.ouroboros/config.yaml`.**
  `ouroboros setup` wrote the literal `claude-sonnet-4-6`; the loader counts a
  value as unset only while it equals the current shipped default, so the
  literal becomes an override after the next upstream Sonnet bump. Deleted
  2026-09-29. Re-check after running `ouroboros setup` or any config tool,
  since either may write it back. (Superseded 2026-09-30: under 0.55.3
  `llm.qa_model: opus` is set on purpose, see above. The concern here was a
  stale Sonnet id; `opus` is an alias, so it doesn't go stale. Phase 4 now
  checks the file still holds both settings.)
- **Haiku fan-out lanes** (see the fan-out model assignment rule) are an
  intentional exception to "discovery on Opus."

## Fixes backported from two dry runs (2026-09-29)

A public-release candidate was audited three times and dry-run twice against a
scratch repo. The first dry run took about 72 minutes, mostly because a broken
`python3` alias stalled tool calls; the second took about 13 minutes and ran
every phase. The correctness fixes were backported here. The public-only
changes (Requirements section, Phase 0 dependency check, generalized model
notes, removal of the `docs-as-code-baseline` and `spec-auditor` references,
the "author's defaults" label, conditional Context7) were not. Where an earlier
section of this file conflicts with this one, this section and `SKILL.md` win.
Pre-backport copies of both files are kept in
`~/.claude/dev-workflow-backups/2026-09-29/`.

Earlier text superseded by this section: the Phase 5 order (now doc-sync,
verification, then finishing), the always-run QA-revise rule, `revision_key`
versioning, `security-review` run against the design, the fan-out lane list,
`TodoWrite` as the mandatory and only resume pointer, SDD fan-out in parallel,
the "diff/output" QA artifact, the old repo-slug rule, the State tracking rule
that resumed from the todo list alone, the "docs untouched until Phase 4
validates success" rule (now with an exception for plans that include a
documentation task), and the security-review timing "before invoking
`writing-plans`" (now before the design or plan is presented).

- **Seed generation.** The two paths differ. The `session_id` call after an
  interview enforces the 0.2 ambiguity threshold and `force`. The direct
  `session_context` call has neither and returns `gap_questions_required`; it
  takes structured keys, with each request sentence copied verbatim into the
  matching key. When `OUROBOROS_REQUIRE_CLIENT_GATES` is 1, true, yes, or on, client
  gates fail the `session_id` call in 0.54.5 (re-verified in 0.55.3), so the variable stays unset;
  otherwise the call only shows a warning. The `session_id` call can also
  refuse when the interview needs to reopen.
- **Seed versioning.** `seed_hash` (SHA-256 of `seed.yaml`) replaced
  `revision_key`, which only Ouroboros's `seed` skill writes, and only during
  an opted-in refinement pass. `state.json` gained `status`
  (`in_progress`/`complete`/`abandoned`), `steps_completed`, and defined write
  points, so a new session can resume from the run directory.
- **Seed QA.** The old "always run the refinement pass" rule contradicted
  Ouroboros's own opt-in rule. The Seed is now graded advisorily at the
  Phase 1→2 transition, the refinement pass is offered and never run
  unasked, and QA differences carry into brainstorming as open questions.
- **Plan mode.** Phases 1–2 write only to the run directory (plus the
  refinement pass's revision note). A refused write is kept in chat and saved
  after `ExitPlanMode`. The real-library spike moved to Phase 3, after
  isolation and the `/fast` check and before implementation. A Spike ends the
  run and exits plan mode.
- **Phase 3.** SDD forbids parallel implementers, so parallel work is opt-in,
  needs disjoint per-task `Files:` blocks, and is committed by the controller.
  Bounded changes have no plan file, so they run inline with TDD. SDD runs
  through its Finish section, and only its handoff to
  `finishing-a-development-branch` is skipped. Implementer briefs carry the
  commit rules, including a blank line before any trailer and the exact
  trailer text; the controller checks `git log -1 --format=%B`.
- **Phase 4.** `ouroboros_qa` needs the complete unelided diff plus real test
  and CLI output, and its `quality_bar` says documentation criteria are out of
  scope, because Phase 5's doc-sync check owns them (and `seed_content` still contains
  the README criterion). The bar also includes criteria that `design.md`
  resolved from the Seed QA differences. A REVISE whose only differences are
  Phase 5 items goes to the human as an accept-or-repair choice. Repairs are
  targeted, never a re-run of SDD, and always get code review.
- **Phase 5.** Doc-sync, then verification, then finishing, so nothing pushes
  before the docs are checked.
- **Also changed.**
  - Model notes: reviewers dispatched inside SDD choose their own model under
    SDD's guidance (**superseded 2026-09-30**: `references/phase3-execution.md`
    now sets `model: opus` on every SDD reviewer), and `ouroboros_qa` ignores the session model "in Claude
    Code", including the Seed QA call in Phase 1.
  - Phase 3 asks the human to confirm `/fast` is off (a gate this skill
    introduces), runs the real-library spike if Phase 2 named one (after
    isolation, before implementation), and stops to ask before
    `using-git-worktrees` commits a `.gitignore` change in the main tree. `EnterWorktree` binds to the session directory, so a target repo
    elsewhere uses `git worktree add`, and the skill tells
    `using-git-worktrees` which mechanism to use.
  - The security review now goes to a subagent that reads the design text,
    because the built-in `security-review` skill reviews branch changes.
  - Fan-out lanes: `gap-hunting` and the lateral personas were removed (they
    aren't interview lanes), and lanes not named use the session model.
  - Run slugs are `owner-repo` with `-2`, `-3` suffixes for same-day
    collisions, and state paths are forward-slash, never 8.3 short names.
    Runs saved under the old folder-name slug won't be found by resume.
  - Phase 4 treats a Minor the reviewer recommends fixing as unresolved, and
    runs code review on any repair diff. Phase 5 asks for confirmation before
    a local merge into the default branch, records `doc_criteria_met`, and
    stops to ask if a documentation criterion can't be met.
    `doc_baseline_skipped` lets the baseline backstop respect a deliberate
    Phase 2 skip.
  - Resume re-enters plan mode when it restarts at Phase 1 or 2, because plan
    mode doesn't carry across sessions. This replaced the "or before invoking
    brainstorming" clause in the Phase 1 trigger.
  - The spike path asks the human to approve the question and probe first,
    matching brainstorming's own gate.
  - The SDD workspace is `.superpowers/sdd/plan/`, or
    `plan-<run-dir-name>/` when another run holds that name; use the path the
    script prints.
  - Deliberately dropped: the qualifier "skip both steps only for plans
    bounded enough that Phase 0 wouldn't have triggered", because such plans
    never reach Phase 2.
- **Environment notes.** No todo tool existed in the dry-run sessions, so the
  todo list is optional and `state.json` is the authoritative pointer. On this
  machine a `python3` shim from the Python install manager hung for about 29
  minutes and then failed; `python3.exe` was copied next to the real Python to
  fix it.
- **Not exercised.** The bounded path (no plan, inline TDD), the Spike path,
  the opt-in parallel path, and the Seed refinement pass were never run. The
  second dry run covered the architectural path only, with `EnterPlanMode`,
  `ExitPlanMode` and every human gate simulated.
- **Unverified here.** The "returns permission mode to `auto`" claim and the
  `/fast` behavior are Claude Code harness claims that can't be checked from
  plugin sources. The run durations above and the `python3` details are
  observations from one machine.

## Deliverables

1. `~/.claude/skills/development-workflow/SKILL.md` (the directory already
   exists and holds this design doc; only the skill file itself is new)
2. Edits to `~/.claude/CLAUDE.md` per the CLAUDE.md impact section above,
   plus the 🧭 General Engineering Practices section added during the scope
   expansion
3. Auditing-agent findings resolved for both files, across four independent
   passes, plus further passes during the 2026-09-29 backport
4. RED+GREEN subagent dry-run results for the five scenarios above (run
   against the pre-expansion `SKILL.md`; not yet re-run against the
   expanded version). The 2026-09-29 dry runs exercised a public-release
   candidate derived from this file, not this file itself.

## `references/` split (2026-09-30)

`SKILL.md` was 629 lines and loaded in full on every invocation. Edge-case and
tool-quirk detail moved verbatim into `references/` (seed generation refusals
and client gates, Seed QA and the refinement pass, the doc-baseline step,
Phase 3 execution and SDD details, Phase 4's model policy and `ouroboros_qa`
call). Each moved block left a pointer in `SKILL.md` that keeps the hard rule
(advisory QA, never hand-edit the Seed, `force` only with consent, one
implementer at a time) and says when to read the file. State tracking,
artifact storage, Seed versioning, and the phase gates stayed in `SKILL.md`:
they run on every pass, so a pointer there would only add a read. Three
Error-handling bullets (entry reliability, trivial requests, `ooo auto`)
were dropped as restatements of "When this applies" and Phase 0; the entry
reliability rationale is the trade-off already recorded in this document's
Error handling section. Rejected: splitting by phase, which would have made
every phase a two-file read. Risk: an agent skips a reference it should have
read. The nine evals log which references were read, and when.

## Phase 4 code review uses `pr-review-toolkit:review-pr` (2026-09-30)

Phase 4 said "a code-review skill or agent, if available", so the tool an
agent picked varied; the eval baseline chose the bare `code-reviewer` agent.
It now names `pr-review-toolkit:review-pr`, which fans out to the specialist
agents (code, tests, errors, types, comments) and groups findings as Critical,
Important, and Suggestions. Two defaults of that command are wrong for this
pipeline and are overridden in `SKILL.md`: it reviews the working tree, which
is empty after Phase 3's per-step commits, so the scope is passed as
`git diff <base>...HEAD`; and "all" ends with `code-simplifier`, which edits
code after the tests and `ouroboros_qa` ran, so the aspects are listed and
`simplify` is left out. Rejected: the `code-review` skill, which has no
per-aspect control. Phase 2's design-text security review was briefly moved to `review-pr`
too. Superseded the same day by the dedicated reviewer below: `review-pr`
is built for diffs and its `code` aspect checks guidelines and bugs, not
design security. Risk:
the agent model can't be set through the command, so `model: opus` is passed
as an instruction to the command and is best effort.

## Dedicated reviewer subagent for Phase 2 and Phase 4 (2026-09-30)

Both reviews now run in a separate subagent instead of the controller's own
session, briefed from `references/reviewer-brief.md`. Mode A reviews
`design.md` for security at the Phase 2 gate; mode B runs
`pr-review-toolkit:review-pr` on the branch diff at Phase 4. A fresh agent on
`model: opus` shares none of the implementer's context, so it can't grade its
own work, and it also gives `review-pr`'s agent model a real place to be
set, since the command has no model parameter.

The human asked for "a separate agent that performs review-pr and
security-guidance". Two parts of that needed correcting. `security-guidance`
is a hook plugin (pattern warnings on `Edit`/`Write`, an LLM diff review when
a turn ends, an agentic reviewer on `git commit`). It has no skill or agent to
invoke and it reviews code, not designs, so it can't be the Phase 2 reviewer.
Mode A is a security brief written for designs (authz and IDOR, injection and
path traversal, SSRF, secrets, data exposure, transport), and `SKILL.md` says
the plugin keeps running through its hooks during Phase 3 and Phase 4, with its
findings treated like Critical ones. Second, one agent doing both jobs is one
brief with two modes, dispatched fresh each time, not a long-lived agent.

Verified before building: a dispatched general-purpose agent can invoke
`review-pr` and spawn the reviewer agent it names (probe on the fixture branch,
no errors, real findings returned).

Rejected: an installed agent definition in `~/.claude/agents/` (breaks the
self-contained rule from the 2026-09-28 decision, needs a registration step,
and drifts, the same objection that ruled out wrapper agents in the model
policy); a reviewer that runs `review-pr` on the design (diff-oriented, no
security aspect); and leaving the review in the controller (the implementer
reviewing itself).

Risks: the brief is a prompt, so its security checklist is only as good as the
categories listed, and it can miss design flaws outside them. A dispatched
reviewer that fails to spawn leaves Phase 2 falling back to the controller
reviewing itself, which `SKILL.md` requires it to say out loud. Evals 10 and 11
cover the code-review and security dispatches (eval 11 also exercises mode C
and its re-run, three dispatches in all); eval 11's fixture has planted flaws (an IDOR against
the Seed's "only their own exports", error-message leakage, and an S3 key built
from caller input).

## Model routing re-confirmed: opusplan plus explicit subagent models (2026-09-30)

Intent, restated by the user: every phase on Opus except Phase 3
implementation on Sonnet, verification back on Opus, then the session back
on its default. An audit found `settings.json` had drifted to `opus`
(then the user's `/model` command saved `sonnet`), so the `opusplan`
assumptions in the skill no longer matched the machine.

Options weighed: (A) main session stays on Opus with Sonnet implementer
subagents, (B) `opusplan` routing, (C) manual `/model` stops. A was built
first and then dropped. The user chose B and set `"model": "opusplan"`.

Resulting policy, written as a Model policy section in `SKILL.md`:

- Phases 1–2 run on Opus because plan mode is on. Phase 0 runs before plan
  mode, on Sonnet, and classifies and runs read-only preflight checks. Phase 3 onward runs on Sonnet
  after `ExitPlanMode`. `/fast` stays a stop-and-ask item, since it forces
  Opus and breaks the routing.
- Implementers get an explicit `model: sonnet`. Reviewers get `model: opus`.
- Verification returns to Opus even though the main session is on Sonnet:
  the Phase 4 test gate, and the Phase 5 re-run, go through a fresh subagent
  on `model: opus` that returns command, raw output and verdict. Rejected:
  re-entering plan mode for Phase 4, since plan mode blocks running the tests.
- Phase 0 now checks that `model` is `opusplan`: it reads `settings.json`, the
  project settings files and `ANTHROPIC_MODEL`, and asks the human when they
  don't settle it (a session `/model` can override all of them unseen).
- SDD's Model Selection and its BLOCKED remedies (under "Handle the report")
  are overridden: they would move the model down for "mechanical" tasks
  ("fast, cheap model") and up for design-judgment tasks, BLOCKED
  implementers, and fix rounds 4–5. The skill never escalates on
  its own; a BLOCKED task that needs more reasoning, a design-judgment task, or a round-4 fix loop is a stop-and-ask.

Known trade-offs: Phase 0 and Phase 5 doc work run on Sonnet, not Opus.
Only the verification runs get an Opus subagent. The Opus test-gate
subagent pays for context the main session already has. The user's wish
for "the default afterwards" costs nothing, since `opusplan` is the default.

## Phase 0 reachability check (2026-09-30)

`CLAUDE.md` claimed Phase 0 checks that `ouroboros_interview`,
`ouroboros_generate_seed` and `ouroboros_qa` are reachable. It didn't: Phase
0 only classified, so a missing Ouroboros server surfaced in Phase 1, after
the run directory and todos existed. Phase 0 now loads the tools through
ToolSearch before creating anything, and stops if one can't be loaded.

## Mode C: Phase 2 design and plan audit (2026-10-01)

Problem: Phase 2's pre-approval check said to verify the plan's facts with "a
`spec-auditor`-style agent if one is configured, otherwise manually". Its
quality depended on the machine, and nothing audited the Seed against the
design and plan. Seed QA (Phase 1) grades the Seed document alone.

Decision: one reviewer at each Phase 2 approval gate, as mode C in
`references/reviewer-brief.md`. It is dispatched like modes A and B: a fresh
`general-purpose` subagent on `model: opus`, read-only, documents treated as
data. It runs once on the bounded path (at design approval) and twice on the
architectural path (design alone at spec approval, design plus plan at plan
approval). It checks (1) traceability, each Seed acceptance criterion to a
design element and to its proof, which is the plan task and test when a plan
exists and the design's testing section otherwise, plus scope creep and
violated constraints; (2) consistency between `design.md`, `plan.md` and the
current `seed_hash`, and that every Seed QA difference was resolved; (3) the
repo facts the documents assert; (4) plan quality when a plan exists. The
controller computes the current hash and passes it in, so the reviewer needs
only read-only tools under plan mode.

Rules that came out of the first audit of this design:

- Persist the draft `design.md`, and record its `seed_hash`, before dispatching
  mode A or C. On the bounded path the design used to be written only after
  approval, so the reviewers would have had no file. If plan mode refuses the
  write, the design goes inline with the current hash.
- Findings marked "Seed gap" go to the human as a possible Seed revision and
  never become a silent design fix; the design or plan isn't presented while a
  Seed gap is unresolved. A revision after Phase 1 either returns to Phase 1
  (re-running the tool preflight) or uses the opt-in refinement pass (needs
  only `ouroboros_qa`).
- After a Critical fix from mode C or from the security review, mode C re-runs
  once on the changed documents; remaining findings are flagged, not looped.
- No agent substitution. An earlier draft let mode C dispatch an installed
  `spec-auditor`. That agent is the knowledge-base document auditor
  (byte-identical to `generate-knowledge-base/Agents/spec-auditor.md`), with its
  own inputs and High/Medium/Low labels, so it would not return the table and
  severity counts the skill gates on. A user's own "audit every plan with
  `spec-auditor`" rule is met by mode C's dispatch.

Alternatives rejected: an installed agent file (drifts from the skill, absent
on other machines, the same reason modes A and B are briefs); `ouroboros_qa`
on `design.md` and `plan.md` (grades a document against a bar and cannot check
the codebase, so it can't catch a plan that names a function that doesn't
exist).

Costs: one more Opus subagent per approval gate (two on the architectural
path), a second dispatch next to mode A when the design touches auth, and a
re-run after a Critical fix.

## Decisions from the second Mode C audit (2026-10-01)

- **Refused writes.** Plan mode can refuse `seed.yaml`, `state.json` and
  `plan.md` as well as `design.md`. The fallback passes the Seed, design and
  plan inline, mode C skips the hash comparison and says so, and the
  `state.json` writes wait until after `ExitPlanMode`.
- **Seed revision after Phase 1.** Only by regenerating through Phase 1, with
  the human's agreement. The opt-in refinement pass stays what it was, a
  response to Seed QA at the Phase 1→2 transition; it needs that QA session
  and its suggestions, which a resume loses. A resume in Phase 1 needs all
  three Ouroboros tools, a resume at Phase 2 or later only `ouroboros_qa`.
- **Policy conflict.** The user's global Plan Mode rule names `spec-auditor`.
  A skill can't declare that rule met by a different agent, so the global rule
  was amended to accept mode C as the gate inside a pipeline run, with the
  reason (the installed `spec-auditor` is the knowledge-base document auditor).
- **Evals without fixtures.** Evals 17, 18 and 20 are marked simulation-only.
  Evals 4, 10 and 11 name the `build-fixtures.sh` flag that builds their
  scenario. Real plan-gate and bounded-draft fixtures can come later.
- **Explicit request, out-of-scope change.** Phase 0 now says what eval 9
  already required: explain the classification and offer the pipeline, and
  create nothing unless the human opts in.
- **State fields.** `path`, `design_drafted` and `design_approved` are now
  documented write points; a resumed Phase 2 needs them to know which gate
  comes next. The build-fixtures script already wrote them.

## SKILL.md shrink: what moved where (2026-10-01)

SKILL.md was 641 lines. Rarely-needed detail moved verbatim into references,
and text already stated elsewhere was collapsed. Result: 584 lines. The
~500-line guideline was not reached, and the plan said so up front: a plan
audit showed the rest would mean moving rules that fire mid-run into files
that are only read at Phase 0 or on resume.

Moved (verbatim): worktree mechanics to `phase3-execution.md`; same-slug
collisions, the Ouroboros worktree-root note, the outside-the-repo note and the
`seed_hash` command and byte-change details to the new `run-lifecycle.md`;
the Context7 and stack-defaults bodies to the new `engineering-defaults.md`;
the Phase 5 doc-baseline backstop paragraph to `doc-baseline.md`; and the
controller handling of mode A and mode C findings to `reviewer-brief.md`,
in a section that is not part of the reviewer's prompt.

Collapsed: the Phase 3 and Phase 4 model-policy bullets (the Model policy
section and `phase4-qa.md` already hold the detail), the Phase 3 stop-and-ask
bullet, the repeated below-threshold verdicts bullet, the duplicate
run-directory sentence, and the "proceed to Phase 3 once approved" clauses
that the Hard gate bullet repeats.

Rules that stay in SKILL.md because they fire where no reference is loaded:
the per-turn resume check and "never restart without asking", the
`EnterPlanMode` re-entry rule, the `state.json` write points, Phase 0 step 2's
classification rules, the bounded path's commit rules, Phase 4's code-review
skip conditions, the Non-goals list, and the "never hand-edit the Seed" rule.
A first draft moved State tracking and several of these into a reference; the
plan audit rejected that, because a sentence-coverage check would still have
passed while the rules were unreachable when they fire.

Check used: every sentence of the old SKILL.md must appear in the new SKILL.md
or in the touched references. The 19 sentences that didn't were reviewed by
hand: 9 are the deliberate collapses above, 6 are verbatim moves the sentence
splitter glued to a neighbouring heading, and 4 are pointer stubs whose
full text now lives in a reference.

## Summary-first rule and three corrected eval expectations (2026-10-01)

The Phase 2 presentation rule now reads: lead with a 3-5 sentence executive
summary, and on a resumed turn at most two short status sentences may come
before it; the summary comes before the audit result and the list of fixes.

Why: the first full eval run (iteration 2) showed the new skill's eval 17 run
opening with status sentences before the summary, while the pre-refactor
snapshot's run opened with the summary. The stricter clause added earlier
("resume status comes after it, not before") did not change that. The
original wording ("lead … above the detailed plan") was the skill's own, from
commit `47ead98`; it is not a CLAUDE.md rule, and an earlier note in the
planning for this change wrongly said it was. The user chose the relaxed
standard (up to two short status sentences).

Eval expectations corrected, with reasons:

- Eval 17: now states the relaxed standard (above).
- Eval 16: a faithful run may name model-neutral alternatives (more context, a
  smaller task, a fresh Sonnet implementer, stop and report) after a declined
  Opus, as `phase3-execution.md` lists them. The old wording forbade that.
- Eval 7: when the human asks "before we start", answering the stack question
  and deferring the `generate_seed` call until they say go is acceptable; the
  old wording required the call to be logged.

Caveat: these corrections were made after seeing the failures, so the
corrected scores are not an unbiased pass rate. The original scores
(51/53 new skill vs 53/53 snapshot on the matched evals; 5/6 on eval 16) are
kept in the eval-run report.

## Seed approval gate (2026-10-01)

Phase 1 now ends with a human gate on the Seed, on both the interview and the
direct path. Before this change nothing asked the human to approve the Seed,
although `SKILL.md` calls it the single source of truth and every design and
plan is hashed against it. The direct path was the weak spot: the Seed is built
from the human's own sentences and never shown back, so a defect surfaced at the Phase 2 audit at best
and at Phase 4 QA at worst, and cost a rerun of Phases 2-4.

Decisions:

- **Both paths gated.** An interview does not guarantee the generated YAML says
  what the human meant, so the interview path is gated too. The prompt is cheap
  after an interview and the most valuable on the direct path.
- **The human sees a summary, not the YAML.** Goal, acceptance criteria,
  constraints, the Seed QA verdict and the open questions QA raised.
  `seed.yaml` stays on disk for anyone who wants it.
- **Seed QA stays advisory.** The human decides, not a model score.
- **Approval is keyed on `seed_approved_hash`, not on the step.**
  `steps_completed` is append-only, so `seed_approved` survives a regeneration;
  only a hash equal to the current `seed.yaml` proves the current Seed was
  approved.
- **A hash mismatch is a Seed revision.** On resume or before Phase 3 a
  `seed.yaml` that no longer matches `seed_approved_hash` goes back through
  Phase 1 regeneration. It is never offered as "approve the edited file",
  which would bless a hand edit.
- **Request changes regenerates.** On the direct path the changes are merged
  verbatim into `session_context`; on the interview path they go back into the
  interview as a new answer. Regenerating with the same input would return the
  same Seed.
- **Runs created before the gate are grandfathered at Phase 3 and later.** At
  Phase 2 they get the gate before design work continues. Their design and plan
  were approved on that Seed, and gating mid-execution would meet a worktree and
  an approved plan outside plan mode.

Rejected alternatives: making the Seed QA score a gate (wrong authority);
folding Seed review into the design approval (a coherent design hides a Seed
defect); showing the gate only on the direct path (the interview path can still
produce a Seed the human did not intend).

Limits: the gate is prose in `SKILL.md`, and a model can skip prose. The hash
check at Phase 3 start is the backstop: a run still at Phase 2 with an absent or
mismatched `seed_approved_hash` stops there (the gate for an absent hash,
regeneration for a mismatch). A script that refuses Phase 3 without a matching
`seed_approved_hash` would be stronger and is not built. The new evals (23-30)
were checked by hand against the fixtures, not run, and evals 3, 5, 7, 8, 17,
18, 20 and 21 were edited to expect the gate or an approved Seed.

A final audit found that an absent `seed_approved_hash` was undefined: the
mismatch, legacy and grandfather rules each read it differently. All three are
now keyed on the hash (equal is approved, different is a revision, absent is a
pre-gate run), and eval 27 covers the grandfathered Phase 3 case.
