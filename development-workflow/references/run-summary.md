# Run summary (end of Phase 4)

Loaded from `SKILL.md` during Phase 4. Section names refer to sections of `SKILL.md`.

`summary.md` gives the human one page that says what the run did from the first request to the validated branch. It lives in the run directory, never in the target repo. It is a document under the human's tone rules: declarative claims, no lead-in such as "This document describes". It is not an instructional file (it reports what happened and tells nobody what to do), so the instructional-document audit does not apply.

## The results ledger: `phase4-results.json`

The summary has to survive a resume, and the session that ran Phase 4 may not be the one that writes it. So Phase 4 records each result in `phase4-results.json` in the run directory as it lands, not at the end. Create it when Phase 4 starts and update it in place:

```json
{
  "commands": [{"name": "test", "command": "npm test", "verdict": "pass", "evidence": "12 passing, exit 0"}],
  "qa": {"verdict": "PASS", "differences": []},
  "review": {"ran": true, "findings": [{"severity": "Critical", "summary": "...", "status": "repaired|deferred|ruled_invalid|open"}]},
  "dependency_audit": "not triggered",
  "accepted_skips": [{"check": "...", "accepted_by": "human"}],
  "deferred": [{"item": "...", "reason": "..."}],
  "technical_debt": [{"item": "symptom fix, not root cause", "where": "..."}],
  "repairs": 0
}
```

Add to it whenever the human defers a finding, rules one invalid, or accepts a skipped check, and whenever a repair is a symptom fix. Overwrite the whole file at the start of each new Phase 4 pass (after a repair loop or a Seed revision) so it always describes the current branch.

## When it runs

- When one rule holds: every Phase 4 gate has passed or been skipped with the human's explicit acceptance, `ouroboros_qa` is PASS or a REVISE the human accepted (a FAIL can't be accepted), and no Critical, Important, or reviewer-recommended Minor finding is unresolved.
- Before Phase 5 starts. Phase 5's doc-sync, final verification and finish choice haven't happened, so the summary says it covers the run up to validation and omits them.
- When Phase 4 hasn't passed, write no summary and tell the human it will be written once Phase 4 passes. A later pass through Phase 4 overwrites the file, so it always matches the branch you are about to finish.
- Spike runs have no implementation to validate and get no summary. An abandoned run gets none either.

## Sources

Build it from files, not from memory of the conversation, so a resumed run produces the same summary:

- `state.json`: `path`, `steps_completed`, the approval gates passed, the worktree path.
- `seed.yaml`: the goal, constraints and acceptance criteria.
- `design.md` and `plan.md`: decisions, trade-offs, the Assumptions section, task list.
- `phase4-results.json`: verification, QA, review, audit, skips, deferrals and debt.
- The branch: `git log --oneline <base>..HEAD` and `git diff --stat <base>...HEAD`, run in the worktree path from `state.json` (or the repo path). Take `<base>` from the branch the worktree was created from (the repo's default branch if `state.json` doesn't say). A target that isn't a git repo has no branch: leave out "What was built" and say so.

If a source is missing (a bounded run has no `plan.md`), leave that section out instead of inventing it.

## Template

```markdown
# Run summary: <task title>

## Executive summary
<3-5 sentences: what was asked, what was built, how it was validated, and the main trade-off or open risk.>

## What was asked
<The Seed's goal and the constraints that shaped it.>

## Path and gates
<bounded or architectural, and the approvals you gave, in order.>

## Design decisions
<The decisions and trade-offs from design.md, one line each.>

## What was built
<Commits, files changed (the diff stat), tasks completed.>

## Verification
<Test command, typecheck, lint, ouroboros_qa verdict, code review, dependency audit: each with its result, and anything skipped with who accepted it.>

## Findings and how they were resolved
<Each Critical and Important finding, the fix, and anything deferred or ruled invalid.>

## Deferred items and open assumptions
<Technical debt recorded, symptom fixes, and any assumption still tagged [Guessing].>

## Not covered
Phase 5 (doc-sync, final verification, merge or PR) had not run when this summary was written.
```

## Writing and opening it

1. Write `summary.md` in the run directory. Append `run_summary` to `steps_completed` only after the write succeeds. If it fails, say so and go on to Phase 5; the summary never gates.
2. Open it with the OS default app. Phase 4 runs outside plan mode, so run the open yourself: Linux `nohup xdg-open "<path>" >/dev/null 2>&1 &`, macOS `open "<path>"`, Windows `cmd //c start "" "<path>"` (Git Bash) or `Invoke-Item "<path>"` (PowerShell). Never use `$EDITOR` or `$VISUAL`. With no display (Linux with neither `DISPLAY` nor `WAYLAND_DISPLAY` set, or an SSH session), give the path alone.
3. Tell the human where it is, repeat the executive summary in chat, and continue straight to Phase 5 in the same turn. Opening the file is not a gate, and the human reads it while Phase 5 runs.
