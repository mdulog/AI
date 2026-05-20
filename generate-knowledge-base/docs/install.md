# Install & troubleshooting — generate-knowledge-base

This is the detailed deployment guide. The 30-second version is in the [README](../README.md#quick-start). Use this doc if you have a non-default project layout, want to verify the install, or hit something unexpected.

---

## What you're installing

The skill is two file groups plus zero runtime dependencies:

```
generate-knowledge-base/
├── generate-knowledge-base.md   # The orchestrator skill (→ .claude/commands/)
└── Agents/
    ├── spec-brainstormer.md
    ├── spec-writer.md
    ├── conventions-writer.md
    ├── legacy-doc-consolidator.md
    ├── adr-writer.md
    └── spec-auditor.md          # All 6 → .claude/agents/
```

The orchestrator and the 6 agents are the only files Claude Code needs. There are no prompt files, schemas, or test suites to worry about — the agents are self-contained.

---

## Standard install

In the target project root (where your codebase lives and where `docs/` will be created):

```bash
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

Verify the file count:

```bash
ls .claude/commands/   # expect: generate-knowledge-base.md
ls .claude/agents/     # expect: 6 .md files
```

Restart Claude Code (or reload skills/agents) so the new files are picked up.

---

## Verify the install (sanity check)

Run this in any project after installing:

```
/generate-knowledge-base
```

**Expected:** STEP 0 runs, detects the project type from your repo markers, confirms all 6 agents are present, and proceeds to brainstorm. If you see agent activity within a few seconds, the skill is wired up correctly.

If instead you see `Unknown command: /generate-knowledge-base`, the orchestrator file isn't in `.claude/commands/` or has the wrong name. Re-check the `cp` step.

If you see `"Agent X is missing"`, the agent files aren't in `.claude/agents/`. The orchestrator names exactly the 6 it requires and hard-stops with the missing path.

---

## Non-default output directories

By default, docs are written to `docs/` at the project root. Pass a custom path as the first argument:

```bash
/generate-knowledge-base my-docs
/generate-knowledge-base apps/api/docs
```

The path is resolved relative to the project root. The orchestrator creates any missing intermediate directories at STEP 0.

---

## Execution modes

| Mode | What runs | When to use |
|---|---|---|
| `mode=full` (default) | Complete workflow: pre-flight, brainstorm, all docs, legacy migration, ADRs, audit, corrections, CLAUDE.md | First run or full refresh |
| `mode=light` | Essential steps only: pre-flight, brainstorm, architecture docs, conventions, specs, CLAUDE.md | Quick refresh, no ADRs needed |
| `mode=force` | Same as `full` but skips git-diff scoping and edit confirmation | Docs folder drifted from git |

```bash
/generate-knowledge-base docs mode=light
/generate-knowledge-base docs mode=force
```

**When to use `mode=light`:** After a small code change when you don't need a full audit pass. Runs in roughly half the time of `mode=full`.

**When to use `mode=force`:** If a previous run completed but you never committed the output, the workflow's git-diff scoping will think nothing changed. `mode=force` bypasses this check and regenerates everything.

---

## Supported project types

The workflow auto-detects your stack from repository files at STEP 0:

| Detected type | Trigger files |
|---|---|
| `frontend` | `package.json` with React, Next, Angular, Vue, Nuxt, or Astro |
| `backend-dotnet` | `*.csproj`, `*.sln`, `Program.cs`, or `Startup.cs` |
| `backend-node` | `package.json` with Express, Fastify, Koa, NestJS, or Hapi |
| `mixed` | Both frontend and backend indicators present |

**For `mixed` projects:** Run from within the specific app subdirectory, or pass an explicit output root scoped to one app:

```bash
# Run from apps/api
cd apps/api && /generate-knowledge-base docs

# Or from project root with explicit path
/generate-knowledge-base apps/api/docs
```

---

## Troubleshooting

### `Unknown command: /generate-knowledge-base`

The orchestrator file isn't in `.claude/commands/`. Check:

```bash
ls .claude/commands/generate-knowledge-base.md
```

If the file is missing, re-run the install `cp` step. If it exists, restart Claude Code so it picks up the new command.

### `"Agent X is missing"` at startup

The orchestrator checks for all 6 agents by exact filename at STEP 0 and stops with the missing path. Re-run:

```bash
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

Then restart Claude Code.

### `"PROJECT_TYPE = mixed"` and the run seems off

With both frontend and backend indicators at the root, the workflow runs in mixed mode which may produce broader docs than you need. Either run from within the specific app directory or pass an explicit scoped output root (see [Supported project types](#supported-project-types) above).

### `reference/api.md` wasn't generated

Only created when the project exposes or consumes meaningful APIs. For projects with no API layer (pure libraries, frontends that only consume external APIs, CLIs), this is expected and correct. The `docs/reference/` folder will exist but contain only a `.gitkeep`.

### ADRs describe decisions I don't agree with

The `adr-writer` agent only records decisions clearly evident in the code — it doesn't invent rationale. If an ADR seems off, the underlying code pattern is likely inconsistent. The ADR is surfacing a real signal worth investigating, not hallucinating a pattern that isn't there.

### The audit flagged too many issues

The `spec-auditor` in `mode=full` reviews every generated file against the real code. High and Medium findings are applied at STEP 7 after you review the correction list. Low findings are surfaced for your awareness but not automatically applied. If the volume feels excessive, consider `mode=light` for incremental runs after the initial full pass.

### The docs look stale after a code change

If you've committed code changes but the docs haven't updated, run with `mode=force` to bypass git-diff scoping:

```bash
/generate-knowledge-base docs mode=force
```

---

## Updating the skill

When a new version of `generate-knowledge-base` ships, re-run the install:

```bash
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

Restart Claude Code after updating. There is no state or version file to migrate — the orchestrator is stateless between runs.

---

## Uninstall

```bash
rm .claude/commands/generate-knowledge-base.md
rm .claude/agents/spec-brainstormer.md \
   .claude/agents/spec-writer.md \
   .claude/agents/conventions-writer.md \
   .claude/agents/legacy-doc-consolidator.md \
   .claude/agents/adr-writer.md \
   .claude/agents/spec-auditor.md
```

Your `docs/` directory and `CLAUDE.md` are untouched. Delete or revert those manually if you want a full clean.
