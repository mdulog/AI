# Run lifecycle details

Loaded from `SKILL.md` (Phase 0 step 5, when creating the run directory; and the Seed versioning section). Section names below refer to sections of `SKILL.md`. Text is moved verbatim from there; the rules in `SKILL.md` still apply.

## Run directory extras (supplements "Artifact storage convention")

- If a run directory with the same slug and date already exists and isn't the run being resumed, append `-2`, `-3`, and so on to `<task-slug>`.
- This doesn't compete with Ouroboros's own default worktree root
  (`~/.ouroboros/worktrees/`) — `state.json` just records whichever worktree
  Phase 3 actually used (via `superpowers:using-git-worktrees`), when one exists.
- Because these artifacts live outside the repo, they are unaffected by which
  worktree is checked out and work identically whether or not the target
  directory is a git repo at all.

## Seed hash details (supplements "Seed versioning")

- Commands for computing `seed_hash`: for example `sha256sum seed.yaml`, or `Get-FileHash -Algorithm SHA256 seed.yaml` in PowerShell 7; that can fail from a Git Bash-launched PowerShell 5.1.
- Any byte change, including whitespace, counts as a revision. That errs toward re-approval, which is the safe direction. This pipeline relies only on `seed_hash`. Ouroboros's `seed` skill writes its own revision notes during an opted-in refinement pass, but this skill never reads them.
