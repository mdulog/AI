# Review documents (Phase 2)

Loaded from `SKILL.md` at every Phase 2 approval gate: the bounded design, the architectural spec and the architectural plan. Section names refer to sections of `SKILL.md`. The Spike path has no design document and is exempt.

The human reviews `design.md` and `plan.md` far better in an editor than in terminal scrollback, so each gate puts an executive summary at the top of the file and hands the file to the OS default app.

## 1. Executive summary in the file

- `design.md` gets `## Executive summary` directly under its H1.
- `plan.md` keeps `writing-plans`'s mandatory header block first (H1, agentic-worker note, Goal, Architecture, Tech Stack, Spec). The summary follows it, before `## Global Constraints`.
- Three to five declarative sentences: what changes, why, and the main trade-off or risk. A plan's summary also gives the task count and names the riskiest task.
- Draft it with the document, before dispatching mode C or mode A, so the audit's summary check (mode C item 8) has something to read. Refresh it after the audit fixes are written, so it describes the corrected content. The chat presentation uses the same sentences.

## 2. Hand the file to the human

Once the audit fixes are written and the summary is refreshed, before the chat presentation:

1. Snapshot the file. Read it and write the copy as `design.presented.md` or `plan.presented.md` in the run directory with the Write tool: a `cp` is a non-readonly Bash call, which plan mode blocks. A run-directory write is normally allowed, but plan mode may prompt for it or refuse it (`SKILL.md`, Phase 1); if it refuses, go to step 6. Hash the original and the copy with `sha256sum` (read-only), or `Get-FileHash -Algorithm SHA256` in PowerShell. If they differ, write the copy again. When they match, record the lowercase hex as `design_presented_hash` or `plan_presented_hash` in `state.json`. Compare hashes case-insensitively.
2. End the chat presentation with a line the human can paste. Every Phase 2 gate runs in plan mode, where the harness tells the model not to run non-readonly tools, so an agent-run open is normally blocked. The `!` prefix runs on the human's side, outside that restriction.
   - Linux: `! xdg-open "<path>"`
   - macOS: `! open "<path>"`
   - Windows (Git Bash): `! cmd //c start "" "<path>"`, or in PowerShell `! Invoke-Item "<path>"`
3. Don't run the open yourself while in plan mode. The harness forbids non-readonly tools there and every Phase 2 gate runs in plan mode, so the `!` line is the handoff, not a fallback.
4. Never use `$EDITOR` or `$VISUAL`. A terminal editor blocks or fails without a TTY.
5. With no display (Linux with neither `DISPLAY` nor `WAYLAND_DISPLAY` set, or an SSH session), give the path alone, without the `!` line.
6. If plan mode refused the file write itself, there is nothing to snapshot and the human isn't looking at a file. Present inline, take no snapshot and record no hash. That gate then has no edit detection, and its `state.json` writes are deferred until after `ExitPlanMode` (see section 3 for how the audit is judged meanwhile).

Opening never gates anything. Whether or not it worked, the presentation gives the full path.

## 3. Every turn at a gate: compare first

On any turn at an approval gate where a presented hash is recorded, a resume or an answer, run this comparison before anything else: before you re-present, re-snapshot or apply a change the human asked for. Skipping it lets a re-snapshot overwrite the human's edit and make it look presented.

Which hashes each gate compares:

- Bounded design gate and architectural spec gate: `design_presented_hash` against `design.md`.
- Architectural plan gate: `plan_presented_hash` against `plan.md`, and `design_presented_hash` against `design.md`. The plan audit can change the design, and the human can edit it between the two approvals.

Compute the current hash as in section 2 and compare it with the recorded one. The cases:

- **Equal:** the answer applies as given.
- **Absent, and this gate's audit already ran:** the run predates this step, or plan mode refused the snapshot. No edit detection, and the answer applies as given. If you re-present the document on this branch, snapshot it and record the hash then, so detection starts.
  - "This gate's audit already ran" means `design_audit` appears in `steps_completed` after the last `design_drafted` (design gates) or the last `plan_drafted` (plan gate), and that `design_drafted` or `plan_drafted` comes after the last `seed_approved`. Every draft and redraft appends a fresh one, so a redraft after a Seed revision can't inherit an earlier audit. `design_approved` and `plan_approved` likewise count only when they follow the last `seed_approved`. Judge by order: `steps_completed` is append-only.
  - If plan mode refused the `state.json` writes and they are deferred, judge from this conversation's record of the audits you ran. On a resumed turn with nothing on disk, treat the audit as not run.
- **Absent, audit not run:** the document was never audited or presented. Treat it as a first presentation: run the audits, then present, and take no approval answer yet. A missing hash never turns an approval into permission to skip the audit or the security review.
- **Differs, and the snapshot file is missing:** treat the document as changed. Give the executive summary and the path instead of a diff, and take the "differs" path below.
- **Differs only in whitespace or line endings** (`git diff --no-index --quiet --ignore-space-at-eol --ignore-cr-at-eol --ignore-blank-lines <presented> <current>` exits 0), as an editor's normalization would produce: say so and ask whether it was intentional. An indentation change is not whitespace-only, because it can change a list or a code block. On yes, re-snapshot, record the new hash and take the answer. On no, restore the presented copy over the file with the Write tool, then take the answer. No mode C re-run either way.
- **Differs:** the human edited it.
  1. Show the change in brief: `git diff --no-index <presented> <current>`.
  2. Re-run mode C on the edited document, and mode A too if the edit touches authentication, authorization or the public network surface. Re-audit even when the answer is "approve": approval covers the version they saw audited.
  3. Never silently rewrite an edited passage. A Critical or Important finding inside human-edited text goes to the human with a proposed fix and is not applied on its own. The executive summary is yours, not theirs: refresh it if the edit made it wrong, and say so.
  4. Re-snapshot, record the new presented hash, reopen per section 2, and ask for approval again. If the edited file is `design.md` at the plan gate, the spec approval no longer covers it: say so and ask for the design approval again before the plan approval.

When a presented hash exists, approval counts only if the current hash equals it.

## 4. Changes you make after presenting

Any change you make to a presented document (applying a change the human asked for, or a fix from a re-run audit) is yours, not theirs. Run the section 3 comparison first so a human edit isn't folded into yours. Then re-audit as the change requires, re-snapshot, record the new hash and re-present. If a plan-gate fix touches `design.md`, re-snapshot it too and tell the human.
