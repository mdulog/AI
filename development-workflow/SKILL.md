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

## Model policy

The intent: planning, review and verification on Opus; implementation on
Sonnet; the session back on its default afterwards. A skill can't switch the
session's model (`/model` is a human command), so two mechanisms do it:

- **`opusplan` routing** (the global `model` setting). The session runs on
  Opus while permission mode is `plan` (Phases 1–2) and on Sonnet otherwise
  (Phase 3 onward, once `ExitPlanMode` has run). Phase 0 runs before plan mode
  and so on Sonnet; it classifies and runs read-only preflight checks,
  including one that the setting is still `opusplan`. Nothing needs switching
  back at the end, because `opusplan` is the default.
- **Explicit `model:` on every subagent this skill dispatches.** Implementers,
  fixers and parallel agents get `model: sonnet` (unless the human has
  allowed Opus for a task, see Phase 3). Reviewers and auditors (the
  Phase 2 design audit and security review, the Phase 4 code review), and the
  Phase 4 and Phase 5 verification runs, get `model: opus`. An omitted `model`
  inherits the session's, which is Sonnet after `ExitPlanMode`. The interview
  fan-out lanes follow their own sub-rule in Phase 1.
- **Trade-off: Sonnet makes some judgment calls.** After `ExitPlanMode` the
  Sonnet main session builds the `ouroboros_qa` artifact and quality bar,
  triages review findings, and classifies a REVISE as implementation wrong or
  Seed wrong. Only reviewers and the test gate run on Opus. When that
  classification is ambiguous, dispatch an Opus reviewer (`model: opus`) to
  propose it, and show its reasoning to the human.

## Phase 0 — Classify and preflight

Run these in order.

1. **Resumable run.** First check for a resumable run (see State tracking). If
   the human is resuming one, skip step 2, run steps 3–4 for the phase it
   records, and carry on at that phase without creating a new run directory.
   Otherwise this is a new run.
2. **Classify** (new runs). In scope if any of these apply: a multi-file
   refactor or new feature spanning more than 2 files; requirements are
   ambiguous and need clarification before touching code; or an
   infrastructure change (CI/CD, migrations, dependency upgrades). Out of
   scope (e.g. a one-line typo fix): stop here, do nothing further — no todo
   list, no run directory, no preflight, just make the change directly. If
   the human explicitly asked for the workflow, say how you classified the
   request and why, and offer to run the pipeline anyway instead of silently
   making the change; create nothing unless they opt in.
3. **Model check.** Read `~/.claude/settings.json`, the project's
   `.claude/settings.json` and `.claude/settings.local.json`, and the
   `ANTHROPIC_MODEL` environment variable. Proceed only if they clearly
   leave `"model": "opusplan"` in effect. Otherwise say what you found and
   ask the human to confirm that `/model` shows `opusplan`: without it
   Phases 1–2 would not run on Opus and the Sonnet implementation would not
   be guaranteed. A session-level `/model` or `--model` can override every
   one of these and the agent can't see it, so when the files don't settle
   it, ask.
4. **Ouroboros tools.** A new run needs `ouroboros_interview`,
   `ouroboros_generate_seed` and `ouroboros_qa`. A resume in Phase 1 needs all three. A
   resume at Phase 2 or later needs only `ouroboros_qa`, since the interview and Seed tools are used only
   in Phase 1 (a Seed revision re-runs this step; see Seed versioning). The tools are usually deferred, so judging by their absence
   from the tool list is wrong. Load them with one ToolSearch query naming
   the ones needed; for a new run:
   `select:mcp__plugin_ouroboros_ouroboros__ouroboros_interview,mcp__plugin_ouroboros_ouroboros__ouroboros_generate_seed,mcp__plugin_ouroboros_ouroboros__ouroboros_qa`.
   Every name must come back. If one is missing, say which and stop. On a new
   run nothing has been created, so there is no run directory and no todo
   list; on a resume leave `state.json` untouched. Failing here is cheaper
   than failing in Phase 1 with state already written.
5. **Create the run** (new runs only). Create the run directory (see Artifact
   storage convention) with `state.json` (phase 0, `status` `in_progress`)
   and the `[dev-workflow]`-prefixed phase todo list (see State tracking).
   Read `references/run-lifecycle.md` when creating the run directory.
   Nothing is created before steps 2–4 have passed.

## Phase 1 — Requirements → Seed

- Call `EnterPlanMode` at the start of Phase 1, before the first interview
  question or seed call. This puts discovery and planning on Opus (`opusplan`
  routing upgrades the model while permission mode is `plan`; see Model
  policy; `/fast` overrides this independently if it's on).
- Check whether goal, constraints, AND success criteria are all already stated.
  - No → run `ouroboros_interview` (conversational, multi-turn). This is a hard
    gate — wait for it to conclude. Then call `ouroboros_generate_seed` with
    the interview's `session_id`.
  - Yes → call `ouroboros_generate_seed` directly, with `session_context`.
    The tool wants structured keys (for example `goal`, `acceptance_criteria`,
    `constraints`, `project_type`), so copy each of the human's sentences
    verbatim into the matching key rather than paraphrasing. No interview.
- Invariant: a Seed YAML is always produced by the end of this phase, regardless of
  which path was taken. Never let Phase 2 start without one, or before the human approves it (see the Seed
  approval gate below).
- Seed generation can refuse or ask for more: an ambiguity refusal after an
  interview, or `gap_questions_required` on the direct path. Read
  `references/seed-generation-edge-cases.md` before calling
  `ouroboros_generate_seed`, and again if it refuses. Set `force` only with the
  human's explicit consent.
- **Seed QA sub-rule** (fires at the Phase 1→2 transition): first confirm,
  read-only, that `~/.ouroboros/config.yaml` still sets `models.pin: true` and
  `llm.qa_model: opus`, and tell the human if it doesn't (QA would then run on
  Sonnet; see the Phase 4 model policy). Then run `ouroboros_qa` on the
  generated Seed as an advisory check, never a gate. Read
  `references/seed-qa-refinement.md` for the exact call, how to handle REVISE
  or FAIL (carry every difference into Phase 2 as an open question, offer one
  opt-in refinement pass, never run it without an explicit yes, never
  hand-edit the Seed), and the refinement pass itself.
- **Seed approval gate** (fires once the Seed is persisted, after Seed QA and any
  refinement pass, before Phase 2; both paths, interview or direct). The Seed is the
  source of truth every later artifact is hashed against, and the direct path builds
  it from the human's sentences without showing them the result, so the human
  approves it before design work starts. Present the goal, the acceptance criteria,
  the constraints, the Seed QA verdict and the open questions QA raised, not the
  YAML (`seed.yaml` stays readable on disk). Ask with `AskUserQuestion`: approve,
  request changes, or abandon. This is a human gate: never approve on their behalf,
  and the QA verdict stays advisory.
  - Approve: append `seed_approved` to `steps_completed` and record the Seed's hash
    as `seed_approved_hash` in `state.json`.
  - Request changes: on the direct path, merge the human's changes verbatim into
    `session_context` and call `ouroboros_generate_seed` again (re-sending unchanged
    input can't produce the requested change); on the interview path, feed the
    changes into the interview session as a new answer, then regenerate. A resumed
    run has neither the original `session_context` nor an interview session id
    (`state.json` doesn't store them), so rebuild `session_context` from
    `seed.yaml`'s goal, constraints and acceptance criteria plus the changes and
    take the direct path. Reload the Ouroboros tools with ToolSearch first, since schemas can unload between turns. Never hand-edit
    the Seed. The new Seed has a new hash, so run Seed QA and this gate again.
  - Abandon: set `state.json`'s `status` to `abandoned`, close the
    `[dev-workflow]` todos and call `ExitPlanMode`, so the session leaves plan mode.
  - If plan mode refused the `seed.yaml` write, still run the gate on the in-chat
    Seed. Hash the exact bytes you will persist, and record `seed_approved` and
    `seed_approved_hash` right after `ExitPlanMode`, together with the deferred
    `seed.yaml`.
- **Fan-out model assignment sub-rule** (fires during interview advisory
  fan-out): default mechanical/low-judgment lanes (`data_context`,
  `answer_simplifier`) to Haiku; reserve Sonnet/Opus for lanes needing deeper
  reasoning (`ambiguity_contrarian`). Any lane not named here uses the
  session model.
- If the human asks about the stack or language defaults in this phase, read
  `references/engineering-defaults.md`.
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
  - Bounded: short in-chat design, no plan document.
  - Architectural: invoke `superpowers:writing-plans` next. Tell `writing-plans` up front that the
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
  authorization, or a public network surface, dispatch a separate reviewer
  subagent to check the design for security risks. Persist `design.md` first
  (see the redirect rule below). Read `references/reviewer-brief.md` and use
  its mode A, once, at the design or spec approval; re-run it at the plan
  gate only if the plan changes the design's auth or network surface. Fix every Critical and
  Important finding in the design, or flag it to the human, before the design
  is presented. The `security-guidance` plugin can't do this job: it reviews
  code through hooks, not designs, and has nothing to invoke. A built-in
  `security-review` skill reviews pending branch changes, not a design, so it
  does not fit here either. If a reviewer subagent can't be dispatched, do the
  review yourself and say so.
- **Doc-baseline check** (architectural path only): if the target is a git repo
  with no doc baseline (no root `README.md` and no `docs/` taxonomy), put an
  explicit "establish doc baseline" step in the plan, before any
  implementation step. Nothing is written to the target repo until Phase 3
  executes it. Skip, and ask first, if the project looks intentionally
  doc-less, and record a skip as `doc_baseline_skipped` in `steps_completed`.
  Read `references/doc-baseline.md` for what the step must contain.
- **Design and plan audit** (fires before a design or plan is presented for
  approval): dispatch a separate reviewer subagent. Read
  `references/reviewer-brief.md` and use its mode C. It runs at each approval
  gate: on the bounded path at the design approval (Seed and design); on the
  architectural path at the spec approval (design alone) and again at the
  plan approval (design and plan). It checks that the Seed, the design and
  the plan trace to each other (every acceptance criterion has a design
  element and something that proves it), agree with each other and with the
  current repo (every file path, function, table and command they name exists
  as described), that the plan is sound, and that both hold to SOLID and, where
  the human's instructions give a security checklist, to that checklist. The
  reviewer reads files, so persist `design.md` (and `plan.md`) and record
  their `seed_hash` first (see the redirect rule below). If the security gate
  above also fires, dispatch both together; they are independent. Tell the
  mode C reviewer whether the security gate is running, so it doesn't repeat
  mode A's findings. If a reviewer subagent can't be
  dispatched, do the audit yourself and say so.
  - Handle findings per the "Controller handling" section of
    `references/reviewer-brief.md`: fix or flag every Critical and Important
    finding before presenting, a Seed gap goes to the human and blocks
    presenting, and re-run mode C once after a Critical fix.
  - Lead the presentation with a 3-5 sentence executive summary (what will
    change, why, the main trade-off or risk). On a resumed turn, at most two
    short status sentences may come before it; the summary comes before the
    audit result and the list of fixes. Then give the audit (the
    traceability table in brief, the severity counts, what you fixed or
    flagged) and the detail. Everything reflects the audit-corrected content,
    not the draft.
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
  paths — this returns to
  the prior permission mode and is what actually allows Phase 3's
  worktree creation and file edits to proceed; without it, a bounded run
  stays stuck in plan mode, which blocks writes.
- Redirect brainstorming's output to `design.md` and writing-plans's output to
  `plan.md`, both in the run directory, overriding each skill's own default
  doc-repo location (both skills' own conventions explicitly allow this
  override). Persist them under the same plan-mode write rule as `seed.yaml`
  above. Write the draft design to `design.md` and record its `seed_hash` in
  `state.json` before dispatching the design and plan audit or the security
  review, because the reviewers read the file. That includes the bounded
  path's in-chat design: write it as a draft, and update the file if approval
  changes it, so outside the Spike path `state.json` points at a real file once
  these writes have gone through. If plan mode refuses a write (this can hit `seed.yaml`, `state.json`
  and `plan.md` as well as `design.md`), pass the Seed, the design and the
  plan inline to the reviewer instead; mode C then skips the hash comparison
  and says so. Defer the `state.json` writes (`seed_hash`, `design_audit`) and
  the files themselves until right after `ExitPlanMode`, as with `seed.yaml`;
  until then `state.json` can lag the artifacts.
  Because nothing is written into the target repo, suppress brainstorming's own
  "commit the design document to git" instruction — there is nothing there to
  commit.

## Phase 3 — Isolate & execute

- If the target is a git repo: isolate a worktree for this task's branch
  (via `superpowers:using-git-worktrees`), keeping the main tree clean. Read
  the "Worktree mechanics" section of `references/phase3-execution.md`
  before creating it: it covers the native tool versus `git worktree add`,
  the consent and sandbox fallbacks, and the `.gitignore` commit to avoid. If
  the target isn't a git repo, skip isolation. Where no worktree gets
  created, treat isolation as skipped and follow the `main`/`master` rule
  below.
- **Model policy.** Implementers run on `model: sonnet` (see Model policy;
  Opus only if the human allows it for a task, see
  `references/phase3-execution.md`). `/fast` (unless `disableFastMode`
  applies) forces Opus and silently breaks the `opusplan` routing. The agent
  can't run or inspect `/fast`, so stop and ask the human to confirm it is off
  before starting this phase.
- If Phase 2 named a real-library spike, run it now: after isolation and the
  `/fast` check, before implementation. If it fails, stop and return to
  Phase 2.
- Invoke `superpowers:test-driven-development` per task. For a multi-task plan
  (architectural path only) use `superpowers:subagent-driven-development`, one
  implementer at a time. The bounded path has no plan: implement inline with
  test-driven-development, and the Phase 4 code review is then required. Run
  tasks in parallel only if the human asks and the plan's per-task `Files:`
  lists are disjoint. Read `references/phase3-execution.md` before dispatching:
  it has the parallel rules, what to do at SDD's Finish step, and how to
  dispatch the final review.
- Per-chunk spot-check agents named in the human's own instructions (code
  reviewer, simplifier and the like) don't run during a pipeline run. The
  per-task and final reviews in `subagent-driven-development`, where it runs,
  and the Phase 4 review whenever SDD's final review wasn't clean or SDD didn't
  run (always after a repair loop) cover them, and the simplifier would edit
  code after it was tested and reviewed.
- **Stop and ask** (see the standalone Stop and ask section; it applies here
  too). On scope expansion, let brainstorming's own ratchet decide whether the
  path upgrades (see Error handling) rather than absorbing the extra work.
  Inside `subagent-driven-development`, which would otherwise make a ruling
  and continue, stop and ask as its controller.
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
    these commit rules in each implementer's brief and check their commit
    messages afterward. Read `references/phase3-execution.md` for the exact
    brief and checks.
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
- Apart from the `/fast` confirmation above, there is no gate beyond the
  routine green checks and the stop-and-ask triggers (which include a model
  escalation and a failed spike).

## Phase 4 — Evaluate

- **Model policy.** Verification is back on Opus (see Model policy). Run the
  test-command gate (IDENTIFY/RUN/READ/VERIFY) through a fresh `model: opus`
  subagent that returns the command, the raw output and its verdict, with the
  worktree path from `state.json` (or the repo path), because the session's
  working directory may not be the worktree; don't re-judge it on Sonnet.
  Dispatch review agents on `model: opus` too. `ouroboros_qa` picks its own
  model and is configured for Opus through `~/.ouroboros/config.yaml`, which
  Phase 1's Seed QA rule already checks. Read `references/phase4-qa.md` for the
  details.
- **Always** run the project's real test command per
  `superpowers:verification-before-completion`'s IDENTIFY/RUN/READ/VERIFY
  gate — this is unconditional, not a fallback. Mechanical correctness (does
  it build, do tests pass) applies regardless of whether a Seed exists.
- **Additionally** — Phase 1's invariant guarantees a Seed always exists for
  any in-scope task — invoke `ouroboros_qa` on the complete, unelided diff plus
  the real test output, graded against the Seed's code-checkable acceptance
  criteria. Documentation criteria are left out; Phase 5's doc-sync check owns
  them. Do NOT use `ouroboros_evaluate`/`ouroboros_start_evaluate`: they need a
  session this pipeline never creates. Read `references/phase4-qa.md` for the
  exact parameters before calling.
- `ouroboros_qa`'s returned verdict label (with `pass_threshold` defaulting to
  0.80) is the semantic/spec-compliance check; `verification-before-completion`'s gate is
  the mechanical one. All of these must pass: the test command,
  `ouroboros_qa`, the dependency audit when it applies, and any code review
  that ran. A dependency audit that can't run is reported as skipped and
  counts only if the human explicitly accepts the skip. They cover different
  concerns, and none substitutes for another. The same tool is advisory at
  Phase 1 (grading the Seed) and a gate here (grading the implementation).
- **Code review**: dispatch a separate reviewer subagent to run
  `pr-review-toolkit:review-pr`, in addition to the test command and
  `ouroboros_qa`. Skip it only if `subagent-driven-development`'s
  final whole-branch review actually ran and came back with no Critical or
  Important findings and no Minor that the reviewer recommends fixing before
  merge (other Minors are deferred and ledgered), and say so when you skip. A
  Minor the reviewer recommends fixing counts as unresolved: repair it, or get
  the human's OK to defer it. Otherwise run it: on the bounded path, after a
  parallel run, or for a single-task plan. After any repair loop, always run
  it on the repair diff, whatever SDD's review said. Read
  `references/reviewer-brief.md` and use its mode B: it names the diff scope
  and the aspects to pass (never `all` or `simplify`, because `code-simplifier`
  edits code after tests and QA have run), and runs on `model: opus` (best
  effort for the agents `review-pr` itself launches). The
  `security-guidance` plugin also reviews the code on its own through hooks
  (on each turn and each commit), so there is nothing to invoke for it. Treat
  its findings like the review's Critical ones.
  - Critical issues are blocking. Important issues are unresolved until
    repaired or the human agrees to defer them. Suggestions are noted and
    don't gate.
  If `pr-review-toolkit` isn't installed, say the step was skipped, since that
  removes review coverage. A blocking finding is an implementation problem:
  repair it in Phase 3. It is never a reason to revise the Seed.
- **Dependency audit**: if the diff adds or changes a dependency (a manifest
  or lockfile), run the ecosystem's audit tool in the same `model: opus`
  verification subagent as the test command. A known vulnerability in an added
  or changed dependency is Critical. Read
  `references/phase4-qa.md` for the commands and what to do when no audit tool
  exists.
- Soft gate: a non-pass QA verdict (REVISE or FAIL) is reported as a new visible step,
  never auto-retried (Ralph is out of scope, and `ouroboros_qa` has no
  `auto_evolve` parameter to chain into it regardless). Repeated verdicts just
  resurface as new visible steps; the human can manually invoke
  `ouroboros_ralph` or `ouroboros_lateral_think` for convergence looping, and
  this skill never does so on its own. The human may
  explicitly accept a REVISE result and proceed; never accept one on their
  behalf. A difference that only names something Phase 5 owns (such as a
  missing README) is an expected difference, not a repair reason: note it and
  continue. If every remaining difference is of that kind, present the
  verdict to the human as REVISE with only Phase 5 differences and ask
  whether to accept it. Otherwise, classify which repair path applies before
  doing anything else — see Seed versioning below, and the Model policy if
  the call is ambiguous:
  - Implementation wrong, Seed still valid → normal repair, back to Phase 3, no
    Seed change, no invalidation. Repair is targeted: one fix subagent (on
    `model: sonnet`) or an inline TDD cycle scoped to the finding. Don't re-invoke
    `subagent-driven-development` on the whole plan; it deletes its ledger at
    finish and would redispatch every task. Re-run Phase 4 on the result,
    including the dependency audit if the repair touched a dependency, and
    code review of the repair diff.
  - Seed wrong → this is a Seed revision. Apply the Seed-versioning invalidation
    rule: regenerate the Seed through Phase 1, then return to Phase 2, not
    Phase 3.

## Phase 5 — Finish & push

Run these three steps in this order.

1. **Doc-sync check**, before any `git push` (including `-u`,
   `--force-with-lease`, and post-amend re-pushes — these get rationalized as
   exceptions, they aren't): verify the project's docs are in sync with the
   branch's changes since the upstream divergence point — diff against the
   base branch and update `README.md` plus any `docs/` taxonomy the diff
   invalidates (or invoke a `/pre-commit`-style skill if the project has
   one). Commit doc updates on the branch before verification and finishing;
   never push with the docs out of sync. Where the human's own instructions
   require an audit of generated instructional documents (runbooks, ADRs, setup
   guides), run it on those updates before committing them, in a subagent on
   `model: opus` that reports findings and never edits. Put the findings to the
   human and don't commit the updates until they have ruled on each one; it adds to the
   checks here. Also check that the Seed's documentation criteria, which Phase 4 left out,
   are met by the doc updates, and record `doc_criteria_met` in
   `steps_completed`. If they aren't met, update the docs and re-check; if a
   criterion can't be met, stop and ask before verification or finishing.
2. `superpowers:verification-before-completion` — before saying anything is
   "done," "fixed," or "passing," this must have actually run and its output
   confirmed; never assert success from the per-step green checks in Phase 3
   alone. Run it the way Phase 4 does, through a subagent on `model: opus`
   (with the worktree path, or the repo path), since the main session is on Sonnet. It runs
   again here, after Phase 4,
   because the doc commits above changed the branch.
3. `superpowers:finishing-a-development-branch`, last. Its options (merge
   locally, push and open a PR, or keep the branch; discard only if the human
   asks) are the human's choice, and
   some of them push or merge on their own, which is why the doc-sync check
   comes first. Phase 3's rule against committing onto `main`/`master` does
   not cover a local merge, so if the human picks a merge into the default
   branch, name that explicitly and get confirmation. When finishing is
   done, set `state.json`'s `status` to `complete`.

- Before step 1: if the target is a git repo with no doc baseline, establish
  it as the backstop unless Phase 2 recorded `doc_baseline_skipped`. Read the
  "Phase 5 backstop" section of `references/doc-baseline.md` for when to flag
  a process gap, when to ask first, and how.
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
- A revised Seed also needs fresh approval at the Phase 1 Seed approval gate:
  `seed_approved_hash` must equal the current Seed's hash before Phase 2 starts.
- Identify a Seed version by its `seed_hash`: the SHA-256 of the exact bytes
  of `seed.yaml` as persisted (commands in `references/run-lifecycle.md`). Record the `seed_hash` each
  `design.md` and
  `plan.md` was built against in `state.json`. Check staleness by recomputing
  the hash of the current `seed.yaml` and comparing; a mismatch means the
  spec or plan is stale. Any byte change, including whitespace, counts as a
  revision; details are in `references/run-lifecycle.md`.
- A Seed is revised after Phase 1 by returning to Phase 1 and regenerating
  it, with the human's agreement. That re-runs Phase 0 step 4 first, because
  the interview and Seed tools are needed again, then the Phase 1 steps, then
  Phase 2 as above. The opt-in refinement pass is only a response to Seed QA
  at the Phase 1→2 transition: it depends on that QA session and its
  suggestions, which a resume loses. Never hand-edit the Seed outside that
  pass.

## State tracking

- `state.json` is the authoritative phase pointer. The todo list, when a todo
  tool exists, mirrors it, and if the two disagree `state.json` wins. If no
  todo tool is available, skip the list.
- Create one todo entry per phase 1–5 at Phase 0 step 5, once the preflight
  has passed. Prefix every entry `[dev-workflow]` and end it with the run directory's name,
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
- When you resume a run, run Phase 0 steps 3–4 before recreating the todo
  list, so a missing tool stops the resume before anything is rewritten. Tool
  schemas can unload between turns, so also reload the Ouroboros tool you are
  about to call with ToolSearch instead of assuming Phase 0's load still
  holds.
- When entering Phase 1 or 2 by any route (a resume, or a return from a later
  phase: a failed spike, a wrong Seed, a Seed revision), call `EnterPlanMode`
  before continuing if the session isn't already in plan mode. Plan mode
  doesn't carry across sessions. From Phase 3 on it isn't needed.
- The todo list is a phase pointer only, never a state container — correct
  resumption also requires the durably-stored artifacts below.
- `state.json` write points:
  - Create it at Phase 0 step 5 with phase 0 and `status` `in_progress`.
  - Update `phase` at every phase transition.
  - Record `path` (`bounded`, `architectural` or `spike`) as soon as
    brainstorming classifies the work. A resumed Phase 2 needs it, together
    with `design_drafted` and `design_approved`, to know which approval gate
    comes next.
  - Append to `steps_completed` as each step finishes (for example
    `seed_generated`, `seed_qa: REVISE`, `seed_approved`, `design_drafted`, `design_audit`,
    `design_approved`, `plan_approved`, `qa_on_diff`), so a
    resumed run knows what already ran.
  - Store paths as full forward-slash paths that both your shell and git
    accept, never 8.3 short names.
  - Record the worktree path when Phase 3 creates one. It can go stale after
    finishing cleans up, so check the path exists before reusing it.
  - Record the `seed_hash` next to `design.md` and `plan.md` when each is
    persisted.
  - Record `seed_approved_hash` (top-level) and append `seed_approved` when the
    human approves the Seed at the Phase 1 gate. `steps_completed` is
    append-only, so judge approval by `seed_approved_hash` equalling the current
    `seed.yaml` hash, never by the step's presence.
  - Check staleness (recompute the hash and compare) on resume and again
    before Phase 3 starts.
  - On resume and before Phase 3, also compare the current `seed.yaml` hash with
    `seed_approved_hash`. That puts the run in one of three states:
    - Equal: the Seed is approved.
    - Present but different: a Seed revision. Regenerate through Phase 1 with the
      human's agreement (see Seed versioning). Never offer to approve the edited
      file, which would bless a hand edit.
    - Absent: a run from before the gate. A missing hash is not a mismatch. At
      Phase 2 or earlier it gets the Seed approval gate before design work
      continues, and asking for changes there is a Seed revision. At Phase 3 or
      later it is grandfathered, since its design and plan were approved on that
      Seed; if it later returns to Phase 2 (a failed spike, a Seed-wrong repair),
      it gets the gate then.
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
- Derive `<repo-slug>` from the target directory's git remote (as
  `owner-repo`, so two organizations' repos of the same name don't collide).
  Without a remote, use the folder name of the git repo's main working tree
  (not a linked worktree or subdirectory), or the working directory's
  basename outside a repo, or
  `no-repo` if even that isn't meaningful. This fallback keeps the pipeline
  working outside a git repo entirely.
- Four files live in the run directory (plus an optional `spike/` folder, see
  Phase 2):
  - `seed.yaml` — the current Seed, persisted the moment Phase 1 produces or
    revises it.
  - `state.json` — current phase, `status` (`in_progress`, `complete`, or
    `abandoned`), `path` (`bounded`, `architectural` or `spike`),
    `steps_completed` (see State tracking), `seed_approved_hash`, worktree path (if one exists — see
    Phase 3), and pointers to
    `design.md`/`plan.md` with the `seed_hash` each was built against.
  - `design.md` — brainstorming's spec, redirected here instead of its default
    `docs/superpowers/specs/` location.
  - `plan.md` — writing-plans's output, redirected here instead of its default
    `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md` location, since it is a
    pre-validation working artifact, not project documentation.
- One exception: `subagent-driven-development` keeps a git-ignored workspace
  inside the target repo; `references/phase3-execution.md` has its path and
  cleanup, and its script prints the real path, so don't assume it.
- Read `references/run-lifecycle.md` when creating the run directory: it
  covers same-slug collisions, how these artifacts relate to worktrees and to
  Ouroboros's own worktree root, and non-git targets.


## Stop and ask

Applies throughout, not just Phase 3 — the trigger conditions can surface at
any phase:

- If a required action is destructive and irreversible (data deletion, force
  push, deleting branches).
- If requirements seem to conflict with security or SOLID principles.
- If the scope of a task expands unexpectedly mid-implementation.
- If a task needs a model escalation that `subagent-driven-development` would
  make on its own (see `references/phase3-execution.md`): ask before allowing
  Opus.

## Documentation lookups (Context7)

When a library, framework, SDK, API, or CLI tool is involved in Phase 2 design
or Phase 3 implementation, look it up with Context7
(`mcp__plugin_context7_context7__resolve-library-id` +
`mcp__plugin_context7_context7__query-docs`), even well-known ones. Never rely
on trained knowledge alone. `references/engineering-defaults.md` says what to
use it for.

## Language & stack defaults

Defaults apply to new/greenfield work only: C# / .NET, React/TypeScript, TUnit
and Jest. An existing project's own conventions win. If the human's own
instructions (their `CLAUDE.md`) name a different stack, say so during Phase 2
and ask; don't silently pick one. Read `references/engineering-defaults.md` for
the full list, and also when the human asks about the stack in Phases 0–1.

## Error handling / edge cases

- **QA verdict below threshold:** handled in Phase 4's soft gate, including
  the choice between the two repair paths and why a failing verdict is never
  auto-retried. Never assume it's an implementation-only fix.
- **Mid-pipeline scope upgrade:** brainstorming's own ratchet ("hidden
  complexity upgrades the path, never downgrades") already handles a bounded
  task turning out to need the architectural path. The skill doesn't fight
  this — Phase 2 defers entirely to brainstorming's own classification rather
  than hardcoding a path.

## Non-goals

- Ralph convergence loops, `evolve_step`, PM interviews, lateral-think personas,
  and brownfield scanning are not branched into by this skill — they stay
  separately-triggered tools invoked directly by the human. The one exception
  is the opt-in Seed refinement pass in Phase 1, which may load lateral-think
  personas as part of Ouroboros's own flow.
- `ooo auto` (`ouroboros_start_auto`) is out of scope entirely — see "When this
  applies."
