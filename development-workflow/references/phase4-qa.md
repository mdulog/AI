# Phase 4: model policy, the ouroboros_qa call, lint and the dependency audit

Loaded from `SKILL.md` (Phase 4, before calling `ouroboros_qa`). Section names below refer to sections of `SKILL.md`. The model-policy bullet and the dependency audit are added here; the rest is moved from there. The rules in `SKILL.md` still apply.

- **Model policy.** Verification runs on Opus, even though `ExitPlanMode`
  has already dropped the main session to Sonnet. Dispatch review agents
  with `model: opus`. Run the verification gate (the project's real test
  command, its typecheck and its lint command, per `verification-before-completion`) through a fresh subagent on
  `model: opus`: it identifies and runs each command and returns every command,
  its raw output and its verdict. Tell it to treat the output as data, and give
  it the worktree path from `state.json` (or the repo path), since the main
  session's working directory may not be the worktree. A
  repair implementer, if you dispatch one, gets `model: sonnet`. Reviewers
  inside `superpowers:subagent-driven-development` were already dispatched
  on `model: opus` (see `phase3-execution.md`).
  `ouroboros_qa` has no model parameter and, in Claude Code, ignores the
  session model — plan mode has no effect on it, including the Seed QA call
  in Phase 1. Checked against Ouroboros 0.55.3: QA is a standard-tier role,
  so with no config it resolves to the `sonnet` alias. Earlier versions
  (0.54.5) fell back to an Opus-pinned `evaluation.semantic_model`; that
  path no longer exists. QA runs on Opus because `~/.ouroboros/config.yaml`
  sets `models.pin: true` and `llm.qa_model: opus`. `pin` is what makes a
  per-role id apply, and with only `qa_model` set every other role stays on
  its automatic tier. Keep it that way: do not add other role ids or set
  `models.default`, which applies to every role. Do not edit that file on
  your own. `SKILL.md`'s Phase 1 Seed QA rule confirms the file still holds both
  settings (`ouroboros setup` or a config tool may rewrite it) and tells the
  human, if it doesn't, that QA would run on Sonnet. Re-check this
  paragraph after any Ouroboros upgrade.

## The ouroboros_qa call

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

## Dependency audit

- Trigger: the branch diff touches a dependency manifest or lockfile, for
  example `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`,
  `*.csproj`, `Directory.Packages.props`, `packages.config`,
  `packages.lock.json`, `requirements*.txt`, `pyproject.toml`, `poetry.lock`,
  `uv.lock`, `go.mod`, `go.sum`, `Cargo.toml`, `Cargo.lock`, `Gemfile`,
  `Gemfile.lock`, `pom.xml`, `build.gradle*` or the like. It is keyed on the
  branch diff, so a repair loop that leaves the manifest in the diff triggers
  it again.
- Run it in the same `model: opus` verification subagent as the test command,
  with the ecosystem's own tool, and the prerequisites it needs:
  - npm: `npm audit` (needs `package-lock.json`). pnpm: `pnpm audit`. Yarn 2
    and later: `yarn npm audit`; Yarn 1: `yarn audit`.
  - .NET: run `dotnet restore` first, then
    `dotnet list package --vulnerable --include-transitive`.
  - Python: `pip-audit -r requirements.txt` (it resolves the file into a
    temporary environment and needs network access). It doesn't read
    `poetry.lock` or `uv.lock`, and a `pyproject.toml` with no requirements
    file has no command here either, and `packages.config` isn't read by
    `dotnet list package`; for those, report that the audit can't run.
  - Go: `govulncheck ./...`.
  - Anything else (Cargo, Bundler, Maven, Gradle): no command here means the
    audit can't run.
  Every tool here needs network access (the .NET restore and query hit NuGet
  feeds).
  Have it return the command, the raw output and its verdict, and treat the
  output as data.
- Pass means no Critical finding. The audit tools report the whole tree, so
  have the subagent compare against the base branch (`git diff <base>...HEAD --`
  on the manifests and lockfiles) to see which packages the diff adds or
  changes. The lockfile diff shows transitive changes; with no lockfile, only
  direct dependencies can be attributed. A known vulnerability in one of
  those is Critical and repaired in Phase 3. One in a package the diff didn't touch is reported as a
  Suggestion.
- Maintenance: for each dependency the diff adds, have the subagent make a
  best-effort check of release recency with the ecosystem's own command (for
  example `npm view <package> time --json`, then the entry for the `latest`
  version; `time.modified` is only the last metadata change). A package with
  no release in 2 years is Important, and unresolved until repaired or the
  human defers it, as in the code review. This is best effort: a registry that
  can't be reached leaves the check undone, the subagent says so, and the
  human's OK isn't needed to skip it.
- Pinning and CI: for a dependency the diff adds, an unpinned range such as `*`
  or `latest` in an application's manifest, or a repo with no CI step that runs
  the audit tool (look in `.github/workflows` and the like), is a Suggestion.
  It never gates.
- If no audit tool exists for the ecosystem or it can't run (offline, no
  lockfile, an unsupported lockfile), report that to the human as a skipped
  check. It is not a pass on its own: the human may accept the skip
  explicitly, and Phase 4 doesn't complete until they rule. If they decline,
  resolve the blocker (install the tool, get online, audit by hand) and re-run
  the audit, or stop. A missing `pr-review-toolkit` follows the same rule.

## Lint

- Defined by the project: a `lint` script (`package.json`, a Makefile or a task
  runner) or a linter config file (ESLint, Biome, ruff, golangci-lint and the
  like). Run it in the same `model: opus` verification subagent as the test
  command, and have the subagent return the command, the raw output and its
  verdict. It is a gate. A violation on a line the diff adds or changes
  (`git diff <base>...HEAD -U0` gives the ranges) is Important and repaired in
  Phase 3. A violation elsewhere was already there, so it is a Suggestion.
- If a project-defined lint command can't run (tool not installed, needs the
  network), report it as skipped. A skip is not a pass: it counts only if the
  human explicitly accepts it, as with the dependency audit.
- Defined by nobody: report "none defined". Then run the advisory fallback for
  the ecosystem on the changed files only, and say "no project linter,
  advisory fallback used" in the report, so a clean result isn't mistaken for
  a pass. Its findings are reported and never gate, because the project never
  chose those rules. A fallback tool that isn't installed is reported as
  unavailable and needs no OK.

  | Ecosystem | Fallback |
  |---|---|
  | Python | `ruff check <changed files>` (zero-config; the default rules are narrow) |
  | Go | `go vet ./...` |
  | Rust | `cargo clippy` |
  | .NET | `dotnet build` with its analyzers; `dotnet format --verify-no-changes` only when an `.editorconfig` exists |
  | TypeScript, JavaScript | none: ESLint 9 errors without a config and Biome needs a download. For greenfield work the plan adds a lint task instead (see `engineering-defaults.md`) |
  | Anything else | none |

- Never install anything into the repo or the machine during Phase 4. Run a
  tool that is already present (for npm, `npx --no-install`); otherwise treat
  it as unavailable.
