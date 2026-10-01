# development-workflow

> Part of the [Claude Code Skills](../README.md) collection. Sibling skills: [`generate-knowledge-base`](../generate-knowledge-base/README.md) and [`generate-prd`](../generate-prd/README.md).

Runs one piece of engineering work through a six-phase pipeline that combines Ouroboros (requirements and evaluation) with Superpowers (design, planning and execution). It is a resumable state machine: it stops at every human gate and saves its own artifacts, so a new session can pick a run back up.

The skill is opt-in. It runs only when you explicitly ask for the dev workflow or the full pipeline. It never intercepts `ooo auto`, and it never blocks direct use of `superpowers:brainstorming` or the Ouroboros tools.

---

## Pipeline

```
Phase 0  Classify & preflight   Sonnet
   │     resumable run? → in scope? → model is opusplan? → Ouroboros tools load? → create run dir + todos
   ▼
Phase 1  Requirements → Seed    Opus (plan mode)
   │     interview if goal/constraints/criteria are unclear → generate Seed → advisory Seed QA
   │     → HUMAN APPROVAL of the Seed
   ▼
Phase 2  Design review & plan   Opus (plan mode)
   │     brainstorming → bounded | architectural (+ writing-plans) | spike
   │     security review (auth / public surface) + design/plan audit → HUMAN APPROVAL
   ▼
Phase 3  Isolate & execute      Sonnet
   │     git worktree → TDD per task → one commit per green step (never pushes)
   ▼
Phase 4  Evaluate               Opus verifiers
   │     real test command + ouroboros_qa on the diff + pr-review-toolkit code review
   │     (code review is skipped when subagent-driven-development's final review was clean,
   │      and always runs after a repair loop)
   ▼
Phase 5  Finish & push          Opus verification
         doc-sync check → verification-before-completion → finishing-a-development-branch
```

| Phase | What happens | Human gate |
|---|---|---|
| 0 | Classifies the request (multi-file change, ambiguous requirements, or infrastructure work is in scope). Checks that `opusplan` is in effect and that `ouroboros_interview`, `ouroboros_generate_seed` and `ouroboros_qa` load. A resume at Phase 2 or later needs only `ouroboros_qa`. Creates nothing until all checks pass. Out-of-scope work, such as a typo fix, gets your call: the skill explains how it classified the request and offers to run the pipeline anyway, or makes the change directly. Nothing is created unless you opt in. | Confirm the model setting if the config files can't settle it; opt in to running out-of-scope work |
| 1 | Skips the interview when goal, constraints and success criteria are already stated; otherwise runs `ouroboros_interview`. Generates a Seed and saves it to `seed.yaml`. Grades the Seed with `ouroboros_qa` as an advisory check. Then shows you the Seed (goal, acceptance criteria, constraints, QA verdict, open questions) and waits for your approval before Phase 2. Asking for changes regenerates the Seed; the skill never hand-edits it. | Interview completion; opt-in Seed refinement; Seed approval (approve, request changes or abandon) |
| 2 | Hands the Seed to `superpowers:brainstorming` and follows its classification. A separate Opus reviewer audits Seed, design and plan against each other and the repo before you see them. A security reviewer runs too when the design touches auth or a public network surface. | Design approval (bounded), spec approval then plan approval (architectural), or approval of the question and probe (spike, plus permission to leave plan mode if the answer needs a throwaway build). A Seed gap the audit finds goes to you and blocks presenting |
| 3 | Creates a worktree (skipped outside a git repo) and implements with TDD. Multi-task plans run through `superpowers:subagent-driven-development`, one implementer at a time. Bounded changes run inline. | Confirm `/fast` is off; stop-and-ask triggers |
| 4 | Runs the project's real test command, grades the diff against the Seed with `ouroboros_qa`, and dispatches a reviewer to run `pr-review-toolkit:review-pr`, unless `subagent-driven-development`'s final whole-branch review already came back clean (a review always runs after a repair loop). Every check that ran must pass. | A REVISE or FAIL verdict is reported to you, never auto-retried |
| 5 | Establishes a doc baseline first if the repo has none (unless Phase 2 skipped it), syncs `README.md` and `docs/` to the branch diff, re-verifies in an Opus subagent, then finishes the branch. | PR creation and push stay manual |

### The three paths in Phase 2

- **Bounded:** short in-chat design, no plan document, implemented inline in Phase 3.
- **Architectural:** written spec, then a plan from `superpowers:writing-plans`, with two sequential approvals.
- **Spike:** a feasibility question. The output is an answer, not code to keep. The run ends after the recommendation.

If brainstorming discovers hidden complexity, it upgrades a bounded task to architectural. The skill doesn't fight that.

### When Phase 4 fails

A non-pass `ouroboros_qa` verdict is classified before anything is repaired:

- **Implementation wrong, Seed still valid:** targeted repair in Phase 3 (one fix subagent or an inline TDD cycle), then Phase 4 again, including a review of the repair diff.
- **Seed wrong:** regenerate the Seed in Phase 1, get it approved at the Seed gate again, and return to Phase 2 for fresh design approval.

Three more rules apply. You may accept a REVISE verdict and proceed; the skill never accepts one for you. A difference that only names something Phase 5 owns, such as a missing README, is expected and isn't a reason to repair. A blocking code-review finding is always an implementation problem: it goes back to Phase 3 and never revises the Seed.

---

## Key mechanisms

**Seed versioning.** The Seed is the single source of truth. Its identity is `seed_hash`, the SHA-256 of the exact bytes of `seed.yaml`. `state.json` records the hash each `design.md` and `plan.md` was built against, plus `seed_approved_hash`, the hash of the Seed you approved. Any byte change to the Seed invalidates the design and plan, and the run returns to Phase 2. A `seed.yaml` that no longer matches `seed_approved_hash` is treated as a Seed revision and regenerated through Phase 1, never approved as edited. A run with no `seed_approved_hash` predates the gate: at Phase 2 or earlier it gets the gate, and at Phase 3 or later it is grandfathered. A stale spec or plan never carries forward.

**Model split.** A skill can't switch the session's model, so two mechanisms do the work. First, `opusplan` routing runs the session on Opus in plan mode (Phases 1–2) and on Sonnet after `ExitPlanMode`. Second, every dispatched subagent gets an explicit `model:`. Implementers and fixers get Sonnet, or Opus for a single task when you allow it. Reviewers, auditors and the Phase 4 and 5 test gates get Opus. The interview fan-out lanes follow their own rule: mechanical lanes run on Haiku, and any lane the skill doesn't name uses the session model.

**Resumability.** `state.json` is the authoritative phase pointer. A `[dev-workflow]`-prefixed todo list mirrors it, and `state.json` wins if they disagree. A new session finds unfinished runs under `~/.claude/dev-workflow-runs/<repo-slug>/` and offers to resume at the recorded phase.

**Commit cadence.** Phase 3 commits after every completed step, but only when the build is green and that step's own tests pass. It stages explicit paths, never commits onto `main`/`master`, and never pushes.

**Doc-sync before push.** Phase 5 updates the README and `docs/` the diff invalidates before any `git push`, and checks the Seed's documentation criteria, which Phase 4 deliberately leaves out.

---

## Requirements

- The [Ouroboros](https://github.com/Q00/ouroboros) plugin (the `ouroboros_*` MCP tools).
- The `superpowers` and `pr-review-toolkit` plugins. If `pr-review-toolkit` is missing, the skill says the code review was skipped.
- `"model": "opusplan"` in `~/.claude/settings.json`. Phase 0 also checks the project-level settings and `ANTHROPIC_MODEL`, and asks you to confirm `/model` when the files can't settle it.
- `~/.ouroboros/config.yaml` with `models.pin: true` and `llm.qa_model: opus`, so `ouroboros_qa` runs on Opus. Without it QA runs on Sonnet, and the skill tells you before the Seed check.
- `/fast` off during Phase 3. It forces Opus and breaks the `opusplan` routing.

Context7 is used for library lookups in Phases 2 and 3. Phase 0 doesn't check for it, but the skill expects it and tells the model not to rely on trained knowledge alone.

---

## Install

The skill installs at user level, not per project:

```bash
mkdir -p ~/.claude/skills/development-workflow
cp -r development-workflow/SKILL.md development-workflow/references ~/.claude/skills/development-workflow/
```

`SKILL.md` loads files from `references/` at the phase that needs them, so copy the directory with it. The installed copy is a plain copy. After editing the repo, run the same command again. The install command doesn't copy `README.md`, `DESIGN.md` or `evals/`; they stay in the repo.

## Usage

```
/development-workflow add rate limiting to the upload endpoint
```

To resume, invoke it again in the same repo. It offers any unfinished run it finds.

---

## Artifacts

Working artifacts are never written into the target repo. Each run gets a directory at:

```
~/.claude/dev-workflow-runs/<repo-slug>/<YYYY-MM-DD>-<task-slug>/
  seed.yaml    the current Seed
  state.json   phase, status (in_progress | complete | abandoned), path (bounded | architectural | spike),
               steps_completed, seed_approved_hash, worktree path, and design/plan pointers {path, seed_hash}
  design.md    brainstorming's spec
  plan.md      writing-plans output (architectural path only)
  spike/       throwaway build, spike path only
```

`<repo-slug>` is `owner-repo` from the git remote, with fallbacks for repos without one. The one in-repo exception is `subagent-driven-development`'s git-ignored workspace. See [`references/phase3-execution.md`](references/phase3-execution.md).

---

## Repository layout

```
development-workflow/
  README.md     This file
  SKILL.md      The skill definition and source of truth for phase order, gates and state tracking
  references/   Detail loaded on demand from named phases
  evals/        evals.json (30 authored prompts with expectations) and files/build-fixtures.sh
  DESIGN.md     Dated design decisions and audit history
```

| Reference file | Loaded from |
|---|---|
| [`seed-generation-edge-cases.md`](references/seed-generation-edge-cases.md) | Phase 1, before calling `ouroboros_generate_seed` and again if it refuses |
| [`seed-qa-refinement.md`](references/seed-qa-refinement.md) | Phase 1→2, Seed QA and the opt-in refinement pass |
| [`reviewer-brief.md`](references/reviewer-brief.md) | Phase 2 design and security audits, Phase 4 code review |
| [`doc-baseline.md`](references/doc-baseline.md) | Phase 2 plan check and the Phase 5 backstop |
| [`phase3-execution.md`](references/phase3-execution.md) | Phase 3, worktree mechanics and implementer briefs |
| [`phase4-qa.md`](references/phase4-qa.md) | Phase 4, the `ouroboros_qa` call and model policy |
| [`run-lifecycle.md`](references/run-lifecycle.md) | Phase 0 run creation and Seed hashing |
| [`engineering-defaults.md`](references/engineering-defaults.md) | Phase 1 stack questions, and the Phase 2-3 Context7 lookups |

## Evals

`evals/evals.json` holds 30 authored prompts with expectations. Nothing runs them automatically. Build a sandbox for them with:

```bash
bash development-workflow/evals/files/build-fixtures.sh <dest> [--with-resume | --empty | --at-phase4 | --at-phase2-design | --seed-mismatch | --legacy-seed]
```

The script creates a small `billing-app` git repo plus an empty `dev-workflow-runs/` directory, then the flag seeds one scenario:

- `--with-resume`: a phase 2 run whose design is stale because the Seed was edited after the design was written. The Seed itself is approved.
- `--empty`: builds `new-service` (only `.gitkeep`) instead of `billing-app`, for greenfield prompts.
- `--at-phase4`: a bounded-path run on branch `dev-workflow/retry-backoff` with one commit and a `test` script. Its `state.json` worktree points at the main repo, so no real worktree exists.
- `--at-phase2-design`: an architectural-path run whose drafted `design.md` is deliberately insecure (an IDOR on `exportId`, exception messages returned to callers), to exercise the security review.
- `--seed-mismatch`: a phase 2 run whose `seed.yaml` was edited after approval, so it no longer matches `seed_approved_hash`.
- `--legacy-seed`: a phase 2 run from before the Seed approval gate, with no `seed_approved` step.

## Editing this skill

- `SKILL.md` uses CRLF line endings. Edit it with a CRLF-preserving tool, since a text-mode rewrite turns the diff into thousands of changed lines.
- Keep the installed copy identical to the repo copy.
- A model-policy change touches several files at once. See the `development-workflow` section of the repo [`CLAUDE.md`](../CLAUDE.md) for the list.
- The pre-push docs hook does not watch this directory.
