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

Before classifying anything as new, check for a resumable run (see State
tracking).

In scope: after that check, create the run directory (see Artifact storage
convention) and the `[dev-workflow]`-prefixed phase todo list (see State
tracking).

## Phase 1 — Requirements → Seed

- Call `EnterPlanMode` at the start of Phase 1, before the first interview
  question or seed call. This
  puts discovery/planning on Opus (the `opusplan` model routing auto-upgrades
  while permission mode is `plan`; `/fast` overrides this independently if
  it's on).
- Check whether goal, constraints, AND success criteria are all already stated.
  - No → run `ouroboros_interview` (conversational, multi-turn). This is a hard
    gate — wait for it to conclude. Then call `ouroboros_generate_seed` with
    the interview's `session_id`.
  - Yes → call `ouroboros_generate_seed` directly, with `session_context`.
    The tool wants structured keys (for example `goal`, `acceptance_criteria`,
    `constraints`, `project_type`), so copy each of the human's sentences
    verbatim into the matching key rather than paraphrasing. No interview.
- Invariant: a Seed YAML is always produced by the end of this phase, regardless of
  which path was taken. Never let Phase 2 start without one.
- Seed generation can refuse or ask for more, and the two paths differ
  (checked against Ouroboros 0.54.5):
  - The `session_id` call after an interview can refuse: it enforces an
    ambiguity threshold of 0.2 unless `force` is set, and it can also refuse
    when the interview needs to reopen. If it refuses, show the refusal to the
    human and return to the interview. Set `force` only with the human's
    explicit consent.
  - The direct `session_context` call has no ambiguity refusal and no `force`.
    If the input is incomplete it returns `gap_questions_required`: ask the
    human those questions, merge the answers into `session_context`, and call
    again.
- Ouroboros can require "client gates" on the `session_id` call. With
  `OUROBOROS_REQUIRE_CLIENT_GATES` set to 1, true, yes, or on, that call fails
  unless `client_gates` are passed. This skill and Ouroboros's interview skill
  don't pass them (`ooo auto` does), so leave the variable unset. Even then
  the call may show a "Client Gate Warning" in its output or metadata;
  expect it and ignore it. The direct path has neither the failure nor the warning.
- **Seed QA sub-rule** (fires at the Phase 1→2 transition): run `ouroboros_qa`
  on the generated Seed — `artifact` = the Seed YAML, `artifact_type` =
  `document`, `quality_bar` = whether the goal, constraints, and acceptance
  criteria are specific, measurable, and consistent with each other,
  `pass_threshold` = 0.90 (the bar Ouroboros's own seed skill uses). Report the
  verdict as advisory and never gate on the score. Branch on the returned
  verdict label, not on your own score comparison. If it is REVISE or FAIL,
  keep the returned QA session id (shown on the `Session:` line) for the
  pass's re-check, list the top two or three suggestions, carry every listed
  difference into Phase 2 as an open question for brainstorming to resolve
  explicitly and cite, and offer the human one opt-in
  refinement pass. To run it, read only the "Wonder → Reflect → Refine →
  Restate" section of Ouroboros's `seed` skill (`skills/seed/SKILL.md` in the
  plugin) and follow that section alone. Skip the rest of that skill: its
  generation step, its "After Seed Generation" section, and its closing
  breadcrumb, which include a GitHub-star prompt and setup steps that don't
  belong in this pipeline. Never run the pass, or chain another, without an
  explicit yes, and never hand-edit the Seed YAML outside that opted-in pass.
  After the pass, re-persist `seed.yaml`; its hash changes, so apply the Seed
  versioning rule below. The pass may load tools this skill otherwise doesn't
  branch into (see Non-goals). That is Ouroboros's own opt-in behavior, not
  this skill's.
- **Fan-out model assignment sub-rule** (fires during interview advisory
  fan-out): default mechanical/low-judgment lanes (`data_context`,
  `answer_simplifier`) to Haiku; reserve Sonnet/Opus for lanes needing deeper
  reasoning (`ambiguity_contrarian`). Any lane not named here uses the
  session model.
- Persist the Seed to `seed.yaml` in the run directory immediately — don't let it
  live only in chat. Writes to the run directory (outside the target repo) are
  the only writes Phases 1–2 make, plus the revision note that Ouroboros's
  `seed` skill writes to `~/.ouroboros/seed-revisions/` if the human opts into
  the refinement pass. Plan mode may prompt the human to approve them or
  refuse them, depending on the Claude Code version; a skill can't override
  that. If a write is refused, keep the artifact in chat, say so, and persist
  it right after `ExitPlanMode`. Resume is incomplete until then.

## Phase 2 — Design review & plan

- Invoke `superpowers:brainstorming` with the Seed as context.
- Defer entirely to brainstorming's own classification (bounded,
  architectural, or spike) — don't hardcode a path here. If brainstorming's complexity
  ratchet upgrades a bounded task to architectural mid-session, let it; this skill
  doesn't fight that.
  - Bounded: short in-chat design, no plan document — proceed directly to Phase 3
    once the design is approved.
  - Architectural: invoke `superpowers:writing-plans` next — proceed to Phase 3
    once the plan is approved. Tell `writing-plans` up front that the
    execution method is subagent-driven, so it uses its own "method already
    supplied" branch and asks only for plan review. If it still asks at its
    handoff choice, answer subagent-driven without asking the human. Phase 3
    executes that way by default because it reviews each task independently,
    where native defers all review to the end. Don't start execution at that
    choice: Phase 3 begins only after plan approval, `ExitPlanMode`, and the
    `/fast` check below.
  - Spike (a feasibility question whose output is an answer, not code to
    keep): no design document and no plan. Get the human's
    approval of the question and the probe first, then answer from reading
    and reasoning. If the answer needs a throwaway build, ask the human to allow
    leaving plan mode first, build under `<run>/spike/` in the run directory,
    and label it throwaway. Then report the recommendation, call
    `ExitPlanMode` if still in plan mode, set `state.json`'s `status` to
    `complete`, mark the remaining
    `[dev-workflow]` todos done or delete them, and stop. Start the pipeline
    again if the human then decides to build it.
- **Security-review gate sub-rule** (fires within this phase, before the design
  or plan is presented for approval): if the design touches authentication,
  authorization, or a public network surface, have a separate reviewing
  subagent (or an available code-review agent such as
  `pr-review-toolkit:code-reviewer`) read the design text and check it for
  security risks. Pass it the design text directly. A built-in
  `security-review` skill reviews pending branch changes, not a design, so it
  does not fit here. If no reviewing agent is available, do the review
  yourself and say so.
- **Doc-baseline check** (architectural path only): if the target is a git
  repo with no doc baseline (no root `README.md` and no `docs/` taxonomy),
  include an explicit "establish doc baseline" step in the plan itself —
  authored as part of `superpowers:writing-plans`, before any implementation
  step — invoking the `docs-as-code-baseline` skill. Surfacing it here lets
  the doc scope get reviewed alongside the rest of the plan instead of
  landing unannounced at Phase 5. Skip, and ask first, if the project looks
  intentionally doc-less (private script folder, monorepo subpackage,
  spike/scratch dir). Record a skip as
  `doc_baseline_skipped` in `steps_completed`.
- **Before presenting the plan for approval**: verify every file path,
  function/service/table name, command, and factual claim the plan
  references still matches the current codebase and system state — use a
  dedicated auditing agent (e.g. a `spec-auditor`-style agent) if one is
  configured in the environment, otherwise perform the check manually. The
  audit's output is a short list of what was checked and how, including
  whether `design.md` and `plan.md` (on the bounded path, the design alone) agree with each other and with the Seed;
  present it with the plan. Fix or flag every finding before presenting —
  don't silently drop one. Then
  lead the presentation with a 3-5 sentence executive summary (what will change, why,
  the main trade-off or risk) above the detailed plan, reflecting the
  audit-corrected content, not the draft.
- If the design depends on an unfamiliar library's runtime behavior (not
  just its documented API), name the highest-risk integration point in the
  design and make a real spike — install the dependency and run one real
  test — the first task of Phase 3, after isolation and before implementation. Don't run it
  during Phases 1–2: plan mode blocks it, and those phases write only to the
  run directory. A Context7 lookup (see Documentation lookups below)
  verifies the API is real; it doesn't verify the code compiles and runs
  against it.
- Hard gate on the bounded and architectural paths — do not proceed to Phase 3
  without explicit human approval (design approval for bounded; spec approval
  then plan approval for architectural — two sequential approvals, not one).
  Call `ExitPlanMode` once that approval is granted, on **either** of those
  paths — this returns
  permission mode to `auto` and is what actually allows Phase 3's
  worktree creation and file edits to proceed; without it, a bounded run
  stays stuck in plan mode, which blocks writes.
- Redirect brainstorming's output to `design.md` and writing-plans's output to
  `plan.md`, both in the run directory, overriding each skill's own default
  doc-repo location (both skills' own conventions explicitly allow this
  override). Persist them under the same plan-mode write rule as `seed.yaml`
  above. On the bounded path the approved in-chat design is also written to
  `design.md`, so outside the Spike path `state.json` always points at a real
  file.
  Because nothing is written into the target repo, suppress brainstorming's own
  "commit the design document to git" instruction — there is nothing there to
  commit.

## Phase 3 — Isolate & execute

- If the target is a git repo: isolate a worktree for this task's branch
  (via `superpowers:using-git-worktrees`), keeping the main tree clean. The
  native `EnterWorktree` tool binds to the session's working directory, so if
  the target repo isn't that directory, use `git worktree add` with a path
  outside the repo instead. Tell `using-git-worktrees` in its dispatch
  arguments which mechanism to use: its own guidance prefers the native tool
  and calls the manual path a mistake, and the native tool also changes the
  session's working directory. If
  the target isn't a git repo at all, there's nothing to isolate — skip this
  step; the artifact storage convention below already works independent of
  git-repo status, so this doesn't block anything downstream.
  `using-git-worktrees` asks for the human's consent only when no preference
  is declared, works in place if the human declines, and does the same if the
  sandbox denies creating a worktree.
  In either case where no worktree gets created, treat isolation as skipped
  and follow the `main`/`master` rule below. `using-git-worktrees` may also
  add its worktree directory to `.gitignore` and commit that in the main tree,
  and may run dependency installs. Stop and ask before that commit, or use a
  worktree directory outside the repo, so nothing lands on the default branch.
- **Model policy.** Implementation runs on Sonnet. `/fast` forces Opus
  unless `disableFastMode` applies and silently breaks the `opusplan`
  routing. The agent can't run or inspect `/fast`, so stop and ask the human to
  confirm it is off before starting this phase.
- If Phase 2 named a real-library spike, run it now: after isolation and the
  `/fast` check, before implementation. If it fails, stop and return to
  Phase 2.
- Invoke `superpowers:test-driven-development` per task. For a multi-task
  plan (which exists only on the architectural path, since SDD needs a plan
  file), invoke `superpowers:subagent-driven-development`. On the bounded path
  there is no plan: implement inline with test-driven-development, don't
  invoke SDD, and note that the Phase 4 code review is then required. SDD runs one
  implementation subagent at a time with a review after each and forbids
  parallel implementers, so do not fan implementation out through it. Run
  tasks in parallel only if the human asks for it, only when the approved
  plan lists the files each task touches and those lists are disjoint, and
  then via `superpowers:dispatching-parallel-agents`. The `Files:` block
  (Create / Modify / Test) that `superpowers:writing-plans` writes into each
  task is that list, so it exists on the architectural path. The bounded
  path has no plan document, so it always stays serial. If the plan doesn't
  show disjoint files, stay serial and say why. In the parallel case the
  controller makes all commits after integration and tells each parallel
  agent not to commit, because concurrent agents
  committing in one worktree contend for the git index lock, and runs the
  full test suite. No per-task review happens there, so the Phase 4 code
  review is required.
- Follow `subagent-driven-development` through its Finish section and surface
  its "Rulings I made" list and any residual findings from its final review
  to the human. Skip only its final handoff to
  `superpowers:finishing-a-development-branch`: return to Phase 4 instead.
  Finishing runs only at Phase 5 step 3, after `ouroboros_qa` and the
  doc-sync check. SDD's Finish step deletes its workspace when the final
  review is clean. Phase 4 doesn't need that ledger, but copy anything you
  want to keep (the Rulings list, review packages) into the run directory
  first. When dispatching SDD's final whole-branch review, pass the
  review-package path and name the most capable model explicitly; the
  reviewer template has no field for either.
- **Stop and ask** (see the standalone Stop and ask section — applies here
  too). On scope expansion specifically, let brainstorming's own ratchet
  decide whether the path upgrades (see Error handling) rather than
  silently absorbing the extra work. Inside `subagent-driven-development`,
  which would otherwise make a ruling and continue, treat scope expansion as a
  stop condition for this pipeline while acting as its controller: stop and
  ask.
- Commit after every completed step — this overrides the harness's default
  "commit only when asked." A step is one plan item, one todo item, or one
  finished red→green→refactor cycle, not one file and not one edit:
  - Only commit green: the build succeeds and that step's own tests pass
    locally. Never checkpoint a knowingly broken tree.
  - Stage explicitly (`git add <paths>`), never `git add -A`. Untracked build
    artifacts (Python's `__pycache__`, for example) can keep `git status` from
    ever being clean. Explicit staging is what keeps them out, and they aren't
    a failure.
  - Commit only, never push — pushing happens in Phase 5.
  - `subagent-driven-development` implementers commit on their own, so put
    these commit rules (explicit staging, never onto `main`/`master`, the
    subject-line rule, no push) in each implementer's brief. Add one more: any
    trailer (such as `Co-Authored-By`) goes after a blank line, never directly
    under the subject, or git folds it into the subject. Give the implementer
    the exact trailer text to use. After each implementer, check
    `git log -1 --format=%B` for the blank line, the subject length, and that
    exact trailer text. If a message breaks the rules, report it to the human
    instead of rewriting history unasked.
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
- Apart from the `/fast` confirmation above, there is no gate beyond the routine green checks and the
  stop-and-ask triggers — this phase introduces no other human approval
  points.

## Phase 4 — Evaluate

- **Model policy.** Review agents and `ouroboros_qa` run on Opus even though
  `ExitPlanMode` has already dropped the session to Sonnet. Dispatch any
  review agents with `model: opus`. The main-session verification gate below
  (reading test output) runs on the session model. Reviewers dispatched
  inside `superpowers:subagent-driven-development` choose their own model
  under that skill's guidance.
  `ouroboros_qa` has no model parameter and, in Claude Code, ignores the
  session model — plan mode has no effect on it, including the Seed QA call
  in Phase 1. Resolution order, verified against Ouroboros 0.54.5:
  `OUROBOROS_QA_MODEL`, then `llm.qa_model` (only when it differs from the
  shipped Sonnet default), then `OUROBOROS_SEMANTIC_MODEL`, then
  `evaluation.semantic_model`, which defaults to the plugin's Opus pin.
  `llm.qa_model` is absent from `~/.ouroboros/config.yaml` on purpose: a
  literal there stops matching the shipped default when upstream bumps it,
  and QA then silently drops to Sonnet. Do not pin it or re-add it. Rolling
  forward on an Opus bump assumes upstream keeps the old pin in its
  legacy-defaults list. Re-check after any `ouroboros setup` or config
  change.
- **Always** run the project's real test command per
  `superpowers:verification-before-completion`'s IDENTIFY/RUN/READ/VERIFY
  gate — this is unconditional, not a fallback. Mechanical correctness (does
  it build, do tests pass) applies regardless of whether a Seed exists.
- **Additionally** — Phase 1's invariant guarantees a Seed always exists for
  any in-scope task — invoke `ouroboros_qa`: `artifact` = the complete,
  unelided diff plus the real test output and any CLI or behavior transcript
  the acceptance criteria refer to, pasted inline (there is no file
  parameter, and `ouroboros_qa` runs nothing itself, so missing evidence shows
  up as a finding), `seed_content` = the current Seed, `quality_bar` = a
  restatement of the Seed's acceptance criteria that the code diff can
  satisfy. Leave out criteria about documentation: Phase 5's doc-sync check
  owns those. Say so inside `quality_bar`
  ("documentation criteria, including any README requirement in the Seed's
  goal or criteria, are out of scope for this artifact and are checked in a
  later phase"), because `seed_content` still contains them and QA otherwise
  lists the missing README as its top difference. Also add the criteria that
  `design.md` resolved from the Seed QA differences: the Seed isn't edited,
  so QA would otherwise never check them. Do NOT use
  `ouroboros_evaluate`/`ouroboros_start_evaluate` for this — those tools
  hard-require a `session_id`, and sessions in Ouroboros only exist for work
  Ouroboros itself executed (`execute_seed`/`start_execute_seed`), which this
  pipeline never does. `ouroboros_qa` requires no session at all and is built
  for exactly this "grade an externally-produced artifact against a spec"
  case.
- `ouroboros_qa`'s returned verdict label (with `pass_threshold` defaulting to
  0.80) is the semantic/spec-compliance check; `verification-before-completion`'s gate is
  the mechanical one. All of these must pass: the test command,
  `ouroboros_qa`, and any code review that ran. They cover different
  concerns, and none substitutes for another. The same tool is advisory at
  Phase 1 (grading the Seed) and a gate here (grading the implementation).
- **Code review** (if a code-review skill or agent is available): run it
  against the diff, in addition to the test command and `ouroboros_qa`. Skip
  it only if `subagent-driven-development`'s final whole-branch review
  actually ran and came back with no Critical or Important findings and no
  Minor that the reviewer recommends fixing before merge (other Minors are
  deferred and ledgered), and say so when you skip. A Minor the reviewer
  recommends fixing counts as unresolved: repair it, or get the human's OK to
  defer it. Otherwise run it: on the bounded path, after a
  parallel run, or for a single-task plan. After any repair loop, always run
  it on the repair diff, whatever SDD's review said. If no review skill or
  agent is installed, say the step was skipped, since that removes review coverage. A blocking finding is an
  implementation problem: repair it in Phase 3. It is never a reason to
  revise the Seed.
- Soft gate: a non-pass QA verdict (REVISE or FAIL) is reported as a new visible step,
  never auto-retried (Ralph is out of scope, and `ouroboros_qa` has no
  `auto_evolve` parameter to chain into it regardless). The human may
  explicitly accept a REVISE result and proceed; never accept one on their
  behalf. A difference that only names something Phase 5 owns (such as a
  missing README) is an expected difference, not a repair reason: note it and
  continue. If every remaining difference is of that kind, present the
  verdict to the human as REVISE with only Phase 5 differences and ask
  whether to accept it. Otherwise, classify which repair path applies before
  doing anything else — see Seed versioning below:
  - Implementation wrong, Seed still valid → normal repair, back to Phase 3, no
    Seed change, no invalidation. Repair is targeted: one fix subagent or an
    inline TDD cycle scoped to the finding. Don't re-invoke
    `subagent-driven-development` on the whole plan; it deletes its ledger at
    finish and would redispatch every task. Re-run Phase 4 on the result,
    including code review of the repair diff.
  - Seed wrong → this is a Seed revision. Apply the Seed-versioning invalidation
    rule and return to Phase 2, not Phase 3.
- Repeated below-threshold verdicts just keep resurfacing as new visible
  steps; the human can manually invoke `ouroboros_ralph` or
  `ouroboros_lateral_think` for convergence looping — this skill never does
  so on its own.

## Phase 5 — Finish & push

Run these three steps in this order.

1. **Doc-sync check**, before any `git push` (including `-u`,
   `--force-with-lease`, and post-amend re-pushes — these get rationalized as
   exceptions, they aren't): verify the project's docs are in sync with the
   branch's changes since the upstream divergence point — diff against the
   base branch and update `README.md` plus any `docs/` taxonomy the diff
   invalidates (or invoke a `/pre-commit`-style skill if the project has
   one). Commit doc updates on the branch before verification and finishing;
   never push with the docs out of sync. Also check that the Seed's documentation criteria, which Phase 4 left out,
   are met by the doc updates, and record `doc_criteria_met` in
   `steps_completed`. If they aren't met, update the docs and re-check; if a
   criterion can't be met, stop and ask before verification or finishing.
2. `superpowers:verification-before-completion` — before saying anything is
   "done," "fixed," or "passing," this must have actually run and its output
   confirmed; never assert success from the per-step green checks in Phase 3
   alone.
3. `superpowers:finishing-a-development-branch`, last. Its options (merge
   locally, push and open a PR, or keep the branch; discard only if the human
   asks) are the human's choice, and
   some of them push or merge on their own, which is why the doc-sync check
   comes first. Phase 3's rule against committing onto `main`/`master` does
   not cover a local merge, so if the human picks a merge into the default
   branch, name that explicitly and get confirmation. When finishing is
   done, set `state.json`'s `status` to `complete`.

- Before step 2, so its doc changes land before verification and finishing:
  on the architectural path, if this is the first time a missing doc
  baseline surfaces, that means Phase 2's doc-baseline check was skipped or
  missed — treat it as a process gap worth flagging. On the bounded path,
  Phase 2 never runs that check by design, so surfacing here is the intended
  path, not a gap. Either way, invoke `docs-as-code-baseline` here as the
  backstop, unless Phase 2 recorded a deliberate skip (`doc_baseline_skipped`
  in `steps_completed`) or the target isn't a git repo. On the bounded path,
  ask first if the project looks intentionally doc-less (the same test as
  Phase 2).
- Hard gate: PR creation and pushing both stay manual, confirm-first steps.
- Project documentation (README, ADRs, docs-as-code baseline content) is
  untouched until this phase's doc-sync check — never earlier, unless the
  approved plan itself includes a documentation task — and never sourced from
  the working artifacts below.

## Seed versioning (invalidation rule)

- The Seed is the single source of truth. Any Seed revision — regardless of
  trigger: mid-brainstorming discovery, a Phase 4 QA rejection traced to the
  Seed, or an opted-in Seed refinement pass (see the Seed QA rule in
  Phase 1) — invalidates every spec and plan derived from the prior version.
- On any Seed revision: return to Phase 2, re-run brainstorming with the updated
  Seed as context, and require a fresh design/plan approval before Phase 3
  resumes or continues. Never silently carry a stale spec or plan forward.
- Identify a Seed version by its `seed_hash`: the SHA-256 of the exact bytes
  of `seed.yaml` as persisted (for example `sha256sum seed.yaml`, or
  `Get-FileHash -Algorithm SHA256 seed.yaml` in PowerShell 7; that can fail
  from a Git Bash-launched PowerShell 5.1). Record the `seed_hash` each
  `design.md` and
  `plan.md` was built against in `state.json`. Check staleness by recomputing
  the hash of the current `seed.yaml` and comparing; a mismatch means the
  spec or plan is stale. Any byte change, including whitespace, counts as a
  revision. That errs toward re-approval, which is the safe direction. This
  pipeline relies only on `seed_hash`. Ouroboros's `seed` skill writes its own
  revision notes during an opted-in refinement pass, but this skill never
  reads them.

## State tracking

- `state.json` is the authoritative phase pointer. The todo list, when a todo
  tool exists, mirrors it, and if the two disagree `state.json` wins. If no
  todo tool is available, skip the list.
- Create one todo entry per phase 1–5, the moment Phase 0 classifies a
  request as in-scope. Prefix every entry `[dev-workflow]` and end it with the run directory's name,
  so this skill's own
  state is distinguishable from unrelated todos in the same session (e.g. a
  `subagent-driven-development` list from different work).
- On every new turn this skill is active, first check for an open
  `[dev-workflow]`-prefixed todo list (with no todo tool, check whether the
  active run is already known from this conversation instead). If one exists
  with incomplete items, check that run's `state.json` first. If its `status` is `complete` or
  `abandoned`, close the stale todos and treat this as a fresh Phase 0.
  Otherwise resume at the phase `state.json` records instead of restarting.
- If there is no todo list, as in a new session, look in
  `~/.claude/dev-workflow-runs/<repo-slug>/` for run directories whose
  `state.json` has `status` other than `complete` or `abandoned`. Exactly one: offer to
  resume it at its recorded phase and recreate the todo list from
  `state.json`. Several: ask the human which. None: this is a fresh Phase 0
  classification. Never restart a run that has a resumable run directory
  without asking.
- When entering Phase 1 or 2 by any route (a resume, or a return from a later
  phase: a failed spike, a wrong Seed, a Seed revision), call `EnterPlanMode`
  before continuing if the session isn't already in plan mode. Plan mode
  doesn't carry across sessions. From Phase 3 on it isn't needed.
- The todo list is a phase pointer only, never a state container — correct
  resumption also requires the durably-stored artifacts below.
- `state.json` write points:
  - Create it in Phase 0 with phase 0 and `status` `in_progress`.
  - Update `phase` at every phase transition.
  - Append to `steps_completed` as each step finishes (for example
    `seed_generated`, `seed_qa: REVISE`, `plan_approved`, `qa_on_diff`), so a
    resumed run knows what already ran.
  - Store paths as full forward-slash paths that both your shell and git
    accept, never 8.3 short names.
  - Record the worktree path when Phase 3 creates one. It can go stale after
    finishing cleans up, so check the path exists before reusing it.
  - Record the `seed_hash` next to `design.md` and `plan.md` when each is
    persisted.
  - Check staleness (recompute the hash and compare) on resume and again
    before Phase 3 starts.
  - Set `complete` when Phase 5 finishes or a Spike ends.
  - Set `abandoned` if the human drops the run, so resume stops offering it.

## Artifact storage convention

- Working artifacts — Seed, design, plan — are never written into the target
  repo. They live at
  `~/.claude/dev-workflow-runs/<repo-slug>/<YYYY-MM-DD>-<task-slug>/`,
  deliberately a sibling of this skill's own directory
  (`~/.claude/skills/development-workflow/`), not nested inside it — that
  directory is skill *definition*, scanned and synced by the harness, and must
  not accumulate unbounded per-run mutable state.
- Phase 0 creates this run directory the moment it classifies a request as
  in-scope. Derive `<repo-slug>` from the target directory's git remote (as
  `owner-repo`, so two organizations' repos of the same name don't collide).
  Without a remote, use the folder name of the git repo's main working tree
  (not a linked worktree or subdirectory), or the working directory's
  basename outside a repo, or
  `no-repo` if even that isn't meaningful. This fallback keeps the pipeline
  working outside a git repo entirely. If a run directory with the same slug
  and date already exists and isn't the run being resumed, append `-2`, `-3`,
  and so on to `<task-slug>`.
- Four files live in the run directory (plus an optional `spike/` folder, see
  Phase 2):
  - `seed.yaml` — the current Seed, persisted the moment Phase 1 produces or
    revises it.
  - `state.json` — current phase, `status` (`in_progress`, `complete`, or
    `abandoned`),
    `steps_completed` (see State tracking), worktree path (if one exists — see
    Phase 3), and pointers to
    `design.md`/`plan.md` with the `seed_hash` each was built against.
  - `design.md` — brainstorming's spec, redirected here instead of its default
    `docs/superpowers/specs/` location.
  - `plan.md` — writing-plans's output, redirected here instead of its default
    `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md` location, since it is a
    pre-validation working artifact, not project documentation.
- One exception: `subagent-driven-development` keeps a git-ignored workspace
  at `<repo-root>/.superpowers/sdd/<plan-name>/` inside the target repo. It
  deletes that subdirectory only when its final whole-branch review is clean;
  a `.gitignore` inside `.superpowers/sdd/` stays. SDD names the workspace
  after the plan file's basename (`.superpowers/sdd/plan/`). If another run's
  workspace already holds that name, its script falls back to
  `.superpowers/sdd/plan-<run-dir-name>/`. Use the path the script prints;
  don't assume it.
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

## Non-goals

- Ralph convergence loops, `evolve_step`, PM interviews, lateral-think personas,
  and brownfield scanning are not branched into by this skill — they stay
  separately-triggered tools invoked directly by the human. The one exception
  is the opt-in Seed refinement pass in Phase 1, which may load lateral-think
  personas as part of Ouroboros's own flow.
- `ooo auto` (`ouroboros_start_auto`) is out of scope entirely — see "When this
  applies."
