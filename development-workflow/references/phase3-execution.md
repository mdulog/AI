# Phase 3 execution details

Loaded from `SKILL.md` (Phase 3, before dispatching implementers). Section names below refer to sections of `SKILL.md`. The Models bullet is added here; the rest is moved from there, and the rules in `SKILL.md` still apply.

- **Models.** Every implementer subagent gets `model: sonnet`, stated
  explicitly in the dispatch. This overrides SDD's own Model Selection
  section and its BLOCKED remedies (under "Handle the report"), which would
  otherwise move the model both ways: a cheaper model for "mechanical" tasks,
  and a more capable one for design-judgment tasks, for a BLOCKED implementer
  whose task "requires more reasoning", and in its fix-loop escalation
  (rounds 4–5). Never escalate on your own. Stop and ask
  the human whether to allow Opus for a task only where SDD would raise the
  model: the task needs design judgment or broad codebase understanding, a
  BLOCKED implementer needs more reasoning, or a fix loop reaches round 4.
  The other BLOCKED remedies don't change the model, so follow them on Sonnet:
  more context with the same model, splitting the task, or ruling on a plan
  correction and ledgering it (a ruling that expands scope is the separate
  stop-and-ask trigger). If the human declines Opus: for a design-judgment task
  at first dispatch, go ahead on Sonnet with a fuller brief; for a BLOCKED
  implementer or a round-4 fix loop, don't retry the same model unchanged,
  which SDD forbids: change something else (more context, a smaller task, a
  fresh Sonnet implementer) or stop and report. Every
  subagent that reviews (SDD's per-task reviews, re-reviews, and final
  whole-branch review) gets `model: opus`, because the main session is on
  Sonnet after `ExitPlanMode`.
- Implementers follow `superpowers:test-driven-development` per task. For a multi-task
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
  review-package path and `model: opus` explicitly; the reviewer template
  has no field for either. Also tell it to cover tests, error handling, types
  and comments, and to report as Critical any finding that breaks one of the human's
  blocking criteria in a way a reviewer would block a merge on (a real missing
  test or SOLID break, not a naming or style nit), as Mode B in
  `reviewer-brief.md` words it. Phase 4 skips its own code review when this
  one comes back clean, so this is the only branch-level code review that
  path gets.

## Implementer commit brief

  - `subagent-driven-development` implementers commit on their own, so put
    these commit rules (explicit staging, never onto `main`/`master`, the
    subject-line rule, no push, and only committing green: the build succeeds,
    the project's typecheck passes and the step's own tests pass) in each
    implementer's brief. Add one more: any
    trailer (such as `Co-Authored-By`) goes after a blank line, never directly
    under the subject, or git folds it into the subject. Give the implementer
    the exact trailer text to use. After each implementer, check
    `git log -1 --format=%B` for the blank line, the subject length, and that
    exact trailer text. If a message breaks the rules, report it to the human
    instead of rewriting history unasked.

## SDD workspace

- One exception: `subagent-driven-development` keeps a git-ignored workspace
  at `<repo-root>/.superpowers/sdd/<plan-name>/` inside the target repo. It
  deletes that subdirectory only when its final whole-branch review is clean;
  a `.gitignore` inside `.superpowers/sdd/` stays. SDD names the workspace
  after the plan file's basename (`.superpowers/sdd/plan/`). If another run's
  workspace already holds that name, its script falls back to
  `.superpowers/sdd/plan-<run-dir-name>/`. Use the path the script prints; don't assume it.

## Worktree mechanics

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
