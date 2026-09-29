---
name: development-workflow
description: "Runs the Ouroboros→Superpowers engineering pipeline (classify → requirements/Seed → design review/plan → isolate & execute → evaluate → finish & push) as a resumable state machine that durably persists its own artifacts and stops at every human gate the pipeline requires. Use only when explicitly asked to run the dev workflow / full pipeline for a piece of engineering work — this skill is never auto-triggered by an ordinary feature request. Hard constraint: this skill must never become the only door into engineering work — brainstorming, direct Ouroboros tool calls, and every other skill stay fully reachable on their own, with or without this skill in the loop."
---

## When this applies

- Entry is explicit and deliberate, the same way `ooo` is a deliberate trigger for
  Ouroboros onboarding — extend that convention rather than trying to out-compete
  `superpowers:brainstorming` on skill-description auto-trigger. If the human didn't
  explicitly ask for the full workflow, don't run any part of it; fall back to
  ordinary ad hoc skill behavior instead.
- Never intercept a request clearly intended for `ooo auto` (`ouroboros_start_auto`)
  — it owns its own execution path end-to-end and stays outside this chain.
- This skill is additive and opt-in. It must never behave as a gate other skills or
  tools have to pass through — if the human goes straight to
  `superpowers:brainstorming` or calls an Ouroboros tool directly instead of
  invoking this skill, that is a fully valid, unblocked path, not a shortcut to
  discourage.

## Phase 0 — Classify

In scope if any of these apply: a multi-file refactor or new feature spanning
more than 2 files; requirements are ambiguous and need clarification before
touching code; or an infrastructure change (CI/CD, migrations, dependency
upgrades). Out of scope (e.g. a one-line typo fix): stop here, do nothing
further — no todo list, no run directory, just make the change directly.

In scope: before anything else, create the run directory (see Artifact
storage convention) and the `[dev-workflow]`-prefixed TodoWrite phase list
(see State tracking).

## Phase 1 — Requirements → Seed

- Call `EnterPlanMode` immediately, before the first interview question or
  before invoking `superpowers:brainstorming` — whichever comes first. This
  puts discovery/planning on Opus (the `opusplan` model routing auto-upgrades
  while permission mode is `plan`; `/fast` overrides this independently if
  it's on).
- Check whether goal, constraints, AND success criteria are all already stated.
  - No → run `ouroboros_interview` (conversational, multi-turn). This is a hard
    gate — wait for it to conclude.
  - Yes → call `ouroboros_generate_seed` directly, no interview.
- Invariant: a Seed YAML is always produced by the end of this phase, regardless of
  which path was taken. Never let Phase 2 start without one.
- **QA-revise sub-rule** (fires at the Phase 1→2 transition): if `ouroboros_qa`'s
  verdict on the generated Seed is REVISE or FAIL, always run the Wonder → Reflect
  → Refine → Restate refinement pass before invoking brainstorming. Never
  hand-edit the Seed YAML directly to fix QA findings.
- **Fan-out model assignment sub-rule** (fires during interview advisory
  fan-out): default mechanical/low-judgment lanes (`data_context`,
  `answer_simplifier`) to Haiku; reserve Sonnet/Opus for lanes needing deeper
  reasoning (`ambiguity_contrarian`, gap-hunting, lateral `contrarian`/`architect`
  personas).
- Persist the Seed to `seed.yaml` in the run directory immediately — don't let it
  live only in chat.

## Phase 2 — Design review & plan

- Invoke `superpowers:brainstorming` with the Seed as context.
- Defer entirely to brainstorming's own classification of bounded vs.
  architectural — don't hardcode a path here. If brainstorming's complexity
  ratchet upgrades a bounded task to architectural mid-session, let it; this skill
  doesn't fight that.
  - Bounded: short in-chat design, no plan document — proceed directly to Phase 3
    once the design is approved.
  - Architectural: invoke `superpowers:writing-plans` next — proceed to Phase 3
    once the plan is approved.
- **Security-review gate sub-rule** (fires within this phase): if the design
  touches authentication, authorization, or a public network surface, run
  `security-review` (or the `pr-review-toolkit:code-reviewer` agent) against the
  design section before invoking `writing-plans`.
- **Doc-baseline check** (architectural path only): if the target is a git
  repo with no doc baseline (no root `README.md` and no `docs/` taxonomy),
  include an explicit "establish doc baseline" step in the plan itself —
  authored as part of `superpowers:writing-plans`, before any implementation
  step — invoking the `docs-as-code-baseline` skill. Surfacing it here lets
  the doc scope get reviewed alongside the rest of the plan instead of
  landing unannounced at Phase 5. Skip, and ask first, if the project looks
  intentionally doc-less (private script folder, monorepo subpackage,
  spike/scratch dir, non-repo working directory).
- **Before presenting the plan for approval**: verify every file path,
  function/service/table name, command, and factual claim the plan
  references still matches the current codebase and system state — use a
  dedicated auditing agent (e.g. a `spec-auditor`-style agent) if one is
  configured in the environment, otherwise perform the check manually. Fix
  or flag every finding before presenting — don't silently drop one. Then
  lead the
  presentation with a 3-5 sentence executive summary (what will change, why,
  the main trade-off or risk) above the detailed plan, reflecting the
  audit-corrected content, not the draft. Skip both steps only for plans
  bounded enough that Phase 0 itself wouldn't have triggered.
- If the design depends on an unfamiliar library's runtime behavior (not
  just its documented API), spike the highest-risk integration point for
  real — install the dependency and run one real test — before finalizing
  the plan. A Context7 lookup (see Documentation lookups below) verifies the
  API is real; it doesn't verify the code compiles and runs against it.
- Hard gate either way — do not proceed to Phase 3 without explicit human approval
  (design approval for bounded; spec approval then plan approval for
  architectural — two sequential approvals, not one). Call `ExitPlanMode`
  once that approval is granted, on **either** path — this returns
  permission mode to `auto` and is what actually allows Phase 3's worktree
  creation and file edits to proceed; without it, a bounded run stays stuck
  in plan mode, which blocks writes.
- Redirect brainstorming's output to `design.md` and writing-plans's output to
  `plan.md`, both in the run directory, overriding each skill's own default
  doc-repo location (both skills' own conventions explicitly allow this override).
  Because nothing is written into the target repo, suppress brainstorming's own
  "commit the design document to git" instruction — there is nothing there to
  commit.

## Phase 3 — Isolate & execute

- If the target is a git repo: isolate a worktree for this task's branch
  (via `superpowers:using-git-worktrees`), keeping the main tree clean. If
  the target isn't a git repo at all, there's nothing to isolate — skip this
  step; the artifact storage convention below already works independent of
  git-repo status, so this doesn't block anything downstream.
- Invoke `superpowers:test-driven-development` per task. Where tasks are
  independent, invoke `superpowers:subagent-driven-development` to fan them
  out in parallel rather than running them serially.
- **Stop and ask** (see the standalone Stop and ask section — applies here
  too). On scope expansion specifically, let brainstorming's own ratchet
  decide whether the path upgrades (see Error handling) rather than
  silently absorbing the extra work.
- Commit after every completed step — this overrides the harness's default
  "commit only when asked." A step is one plan item, one todo item, or one
  finished red→green→refactor cycle, not one file and not one edit:
  - Only commit green: the build succeeds and that step's own tests pass
    locally. Never checkpoint a knowingly broken tree.
  - Stage explicitly (`git add <paths>`), never `git add -A`.
  - Commit only, never push — pushing happens in Phase 5.
  - Never auto-commit onto `main`/`master`. The worktree isolated above
    covers this when the target is a git repo; if worktree isolation was
    skipped or the work is already sitting on the default branch, stop and
    ask rather than committing there.
  - Subject line: imperative, ≤72 chars, naming the change ("Add retry
    policy to payer lookup client"). Read `git log` before the first commit
    to match the repo's existing convention (Conventional Commits, ticket
    prefixes) if it has one; fall back to the imperative-subject rule above
    if it doesn't.
  - "Don't commit"/"no commits" from the human suspends this for the rest of
    the session.
- No gate beyond the routine green checks and the stop-and-ask triggers
  above — this phase doesn't introduce additional human approval points of
  its own.

## Phase 4 — Evaluate

- **Always** run the project's real test command per
  `superpowers:verification-before-completion`'s IDENTIFY/RUN/READ/VERIFY
  gate — this is unconditional, not a fallback. Mechanical correctness (does
  it build, do tests pass) applies regardless of whether a Seed exists.
- **Additionally** — Phase 1's invariant guarantees a Seed always exists for
  any in-scope task — invoke `ouroboros_qa`: `artifact` = the implementation's
  diff/output, `seed_content` = the current Seed, `quality_bar` = a
  restatement of the Seed's acceptance criteria. Do NOT use
  `ouroboros_evaluate`/`ouroboros_start_evaluate` for this — those tools
  hard-require a `session_id`, and sessions in Ouroboros only exist for work
  Ouroboros itself executed (`execute_seed`/`start_execute_seed`), which this
  pipeline never does. `ouroboros_qa` requires no session at all and is built
  for exactly this "grade an externally-produced artifact against a spec"
  case.
- `ouroboros_qa`'s verdict (score vs. `pass_threshold`, default 0.80) is the
  semantic/spec-compliance check; `verification-before-completion`'s gate is
  the mechanical one. Both must pass — they cover different concerns, neither
  substitutes for the other.
- Soft gate: a below-threshold QA verdict is reported as a new visible step,
  never auto-retried (Ralph is out of scope, and `ouroboros_qa` has no
  `auto_evolve` parameter to chain into it regardless). On a below-threshold
  verdict, classify which repair path applies before doing anything else —
  see Seed versioning below:
  - Implementation wrong, Seed still valid → normal repair, back to Phase 3, no
    Seed change, no invalidation.
  - Seed wrong → this is a Seed revision. Apply the Seed-versioning invalidation
    rule and return to Phase 2, not Phase 3.
- Repeated below-threshold verdicts just keep resurfacing as new visible
  steps; the human can manually invoke `ouroboros_ralph` or
  `ouroboros_lateral_think` for convergence looping — this skill never does
  so on its own.

## Phase 5 — Finish & push

- `superpowers:finishing-a-development-branch` →
  `superpowers:verification-before-completion` — before saying anything is
  "done," "fixed," or "passing," this must have actually run and its output
  confirmed; never assert success from the per-step green checks in Phase 3
  alone.
- **Doc-sync check**, before any `git push` (including `-u`,
  `--force-with-lease`, and post-amend re-pushes — these get rationalized as
  exceptions, they aren't): verify the project's docs are in sync with the
  branch's changes since the upstream divergence point — diff against the
  base branch and update `README.md` plus any `docs/` taxonomy the diff
  invalidates (or invoke a `/pre-commit`-style skill if the project has
  one). Apply doc updates in the same response as the push — never push
  first and fix docs later.
- On the architectural path, if this is the first time a missing doc
  baseline surfaces, that means Phase 2's doc-baseline check was skipped or
  missed — treat it as a process gap worth flagging. On the bounded path,
  Phase 2 never runs that check by design, so surfacing here is the intended
  path, not a gap. Either way, invoke `docs-as-code-baseline` here as the
  backstop.
- Hard gate: PR creation and pushing both stay manual, confirm-first steps.
- Project documentation (README, ADRs, docs-as-code baseline content) is
  untouched until this phase's doc-sync check — never earlier, and never
  sourced from the working artifacts below.

## Seed versioning (invalidation rule)

- The Seed is the single source of truth. Any Seed revision — regardless of
  trigger: mid-brainstorming discovery, a Phase 4 QA rejection traced to the
  Seed, or any manual/QA-triggered refinement beyond the QA-revise rule
  above — invalidates every spec and plan derived from the prior version.
- On any Seed revision: return to Phase 2, re-run brainstorming with the updated
  Seed as context, and require a fresh design/plan approval before Phase 3
  resumes or continues. Never silently carry a stale spec or plan forward.
- Don't invent a version identifier. Ouroboros already tracks full Seed revision
  history at `~/.ouroboros/seed-revisions/<revision_key>.md` (iteration number, QA
  score, candidates, accept/reject decisions, diff vs. previous). Record the
  `revision_key` a given `design.md`/`plan.md` was built against in `state.json`;
  check staleness by comparing that recorded key to the Seed's current revision
  key, not by maintaining a parallel scheme.

## State tracking

- Create one TodoWrite entry per phase 1–5, the moment Phase 0 classifies a
  request as in-scope. Prefix every entry `[dev-workflow]` so this skill's own
  state is distinguishable from unrelated todos in the same session (e.g. a
  `subagent-driven-development` list from different work).
- On every new turn this skill is active, first check for an open
  `[dev-workflow]`-prefixed todo list. If one exists with incomplete items,
  resume at the first incomplete phase instead of restarting. If none exists,
  this is a fresh Phase 0 classification.
- The todo list is a phase pointer only, never a state container — correct
  resumption also requires the durably-stored artifacts below.

## Artifact storage convention

- Working artifacts — Seed, design, plan — are never written into the target
  repo. They live at
  `~/.claude/dev-workflow-runs/<repo-slug>/<YYYY-MM-DD>-<task-slug>/`,
  deliberately a sibling of this skill's own directory
  (`~/.claude/skills/development-workflow/`), not nested inside it — that
  directory is skill *definition*, scanned and synced by the harness, and must
  not accumulate unbounded per-run mutable state.
- Phase 0 creates this run directory the moment it classifies a request as
  in-scope. Derive `<repo-slug>` from the target directory's git remote or folder
  name when one exists; fall back to the working directory's basename, or
  `no-repo` when even that isn't meaningful, when it doesn't — this fallback
  keeps the pipeline working outside a git repo entirely.
- Four files live in the run directory:
  - `seed.yaml` — the current Seed, persisted the moment Phase 1 produces or
    revises it, plus the `revision_key` of its latest
    `~/.ouroboros/seed-revisions/` entry.
  - `state.json` — current phase, worktree path (if one exists — see Phase 3),
    and pointers to `design.md`/`plan.md` with the `revision_key` each was
    built against. No `session_id` is tracked: Phase 4 uses `ouroboros_qa`
    (session-less by schema), not `ouroboros_evaluate`, so there is nothing
    session-related to cache.
  - `design.md` — brainstorming's spec, redirected here instead of its default
    `docs/superpowers/specs/` location.
  - `plan.md` — writing-plans's output, redirected here instead of its default
    `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md` location, since it is a
    pre-validation working artifact, not project documentation.
- This doesn't compete with Ouroboros's own default worktree root
  (`~/.ouroboros/worktrees/`) — `state.json` just records whichever worktree
  Phase 3 actually used (via `superpowers:using-git-worktrees`), when one exists.
- Because these artifacts live outside the repo, they are unaffected by which
  worktree is checked out and work identically whether or not the target
  directory is a git repo at all.

## Stop and ask

Applies throughout, not just Phase 3 — the trigger conditions can surface at
any phase:

- If a required action is destructive and irreversible (data deletion, force
  push, deleting branches).
- If requirements seem to conflict with security or SOLID principles.
- If the scope of a task expands unexpectedly mid-implementation.

## Documentation lookups (Context7)

- Always use Context7 (`mcp__plugin_context7_context7__resolve-library-id` +
  `mcp__plugin_context7_context7__query-docs`) during Phase 2
  design or Phase 3 implementation when a library, framework, SDK, API, or
  CLI tool is involved — even well-known ones. Never rely on trained
  knowledge alone; training data may not reflect recent API changes,
  version migrations, or deprecations.
- Use for: API syntax, configuration options, version migration guides,
  setup instructions, CLI usage, library-specific debugging. Not needed for:
  general programming concepts, refactoring, business logic, or code review.

## Language & stack defaults

- Primary language: TypeScript/Node.js (latest LTS) for new/greenfield work
  in Phase 3, unless the target project specifies otherwise.
- Frontend: React/TypeScript for new/greenfield UI work. For an existing
  project, match whatever's already there instead (Angular, Vue, etc.) —
  check the repo (package.json, existing components) before assuming
  greenfield applies.
- Default test framework: Jest (backend and frontend) for new/greenfield
  work. An existing project's tests follow whatever test convention that
  project already uses, not this default.
- These are defaults for new/greenfield work only — always defer to what the
  target project's own conventions or existing codebase specifies.

## Error handling / edge cases

- **QA verdict below threshold:** report findings, stop, and classify which
  of the two repair paths under Seed versioning applies (implementation
  wrong vs. Seed wrong) before proceeding — never assume it's an
  implementation-only fix. Treat next step as a new visible planning step
  (not hidden auto-retry). Since Ralph is out of scope (and `ouroboros_qa`
  has no `auto_evolve` behavior to chain into it regardless), repeated
  below-threshold verdicts just keep surfacing each time — the user can
  manually invoke `ouroboros_ralph` or `ouroboros_lateral_think` if they
  want convergence looping.
- **Mid-pipeline scope upgrade:** brainstorming's own ratchet ("hidden
  complexity upgrades the path, never downgrades") already handles a bounded
  task turning out to need the architectural path. The skill doesn't fight
  this — Phase 2 defers entirely to brainstorming's own classification rather
  than hardcoding a path.
- **Entry reliability:** resolved by explicit invocation (see "When this
  applies") — if the human didn't say the trigger phrase, they get ordinary
  ad hoc `brainstorming` behavior, not a silently broken pipeline. This is
  an intentional trade-off, not an unaddressed gap.
- **Trivial requests:** Phase 0 must correctly classify these as out-of-scope
  and do nothing beyond the direct fix, or every one-line fix would spawn a
  todo list and an interview.
- **`ooo auto` requests:** if a request is clearly intended for
  `ouroboros_start_auto` (an end-to-end autonomous run), this skill must not
  intercept it — see Non-goals.
- **Unverified: `session_id` on the interview-less path** is moot — Phase 4
  no longer uses a session-keyed tool at all (see Phase 4).

## Non-goals

- Ralph convergence loops, `evolve_step`, PM interviews, lateral-think personas,
  and brownfield scanning are not branched into by this skill — they stay
  separately-triggered tools invoked directly by the human.
- `ooo auto` (`ouroboros_start_auto`) is out of scope entirely — see "When this
  applies."
