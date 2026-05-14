# Integrations

## Scope

This skill has no databases, queues, message brokers, schedulers, auth providers, third-party SaaS APIs, or storage backends. It is a markdown-only workflow that runs entirely inside the Claude Code runtime against the target project's local filesystem.

The "integrations" relevant to this project are the runtime harness it depends on, the slash commands it relies on (gracefully degraded when absent), the version-control system it uses for idempotency, an optional plugin, and the filesystem layout used for deployment.

## Claude Code Harness (mandatory)

The skill cannot run outside the Claude Code runtime. The harness provides every primitive used by the orchestrator and agents.

**Tools consumed:**

| Tool | Used by | Purpose |
|---|---|---|
| `Read` | all components | Read source files, agent files, existing docs, `CLAUDE.md` |
| `Write` | orchestrator + writer agents | Create or update markdown files under `OUTPUT_ROOT/`; finalize `CLAUDE.md` |
| `Bash` | all components | Project-type detection, `git` operations, `Glob`/`find` fallbacks, folder creation |
| `Glob` | most agents | Enumerate files (notably ADR numbering and audit passes) |
| `Grep` | most agents | Locate patterns across the codebase during analysis |
| `Agent` | orchestrator only | Dispatch subagents — sole entry point for delegated work |

The orchestrator declares `[Read, Write, Bash, Agent]`; subagents declare narrower tool sets per the components doc. The `Agent` tool is intentionally exclusive to the orchestrator: only the supervisor can dispatch subagents.

**Dispatch model.** Each `Agent` invocation passes all needed context inline (PROJECT_TYPE, OUTPUT_ROOT, the brainstorm report, target file list, step-specific instructions). Agents return their result as their final assistant message — there is no shared memory, no inter-agent message bus, and no agent-to-agent direct call path.

**Failure mode.** If a required agent file is missing from `.claude/agents/`, the orchestrator halts immediately and reports the missing path, the step that cannot continue, and the action the user must take. There is no in-context fallback (orchestrator § Hard requirement).

## Slash Commands (harness-provided)

The orchestrator invokes two harness slash commands during normal flow. Both degrade gracefully when unavailable.

### `/effort <level>`

Sets the reasoning effort for subsequent dispatches. The orchestrator's effort schedule:

- `/effort medium` at session start; remains medium for STEPS 0–0.6, 2, 3, 4, 7, 8.
- `/effort high` before STEP 1 (`spec-brainstormer`), STEP 5 (`adr-writer`), and STEP 6 (`spec-auditor`); reverted to `medium` immediately after each.

If `/effort` is unavailable in the harness, the orchestrator continues and behaves as if the requested level were applied (orchestrator § Model and effort policy). The skill never blocks on missing effort control.

### `/init`

Used in STEP 0 only when the target project has no `CLAUDE.md`. The orchestrator runs `/init`, waits for completion, then reviews and improves the generated file before continuing (orchestrator § STEP 0 — Check and migrate CLAUDE.md). When `CLAUDE.md` already exists, `/init` is not invoked — the orchestrator migrates legacy section references in place instead.

## Git (optional)

`git` is used opportunistically for idempotency and ADR safety. The skill degrades when git is unavailable or the project is not a git repo.

**STEP 0.4 — Idempotency pre-flight.**

```bash
git log -1 --format="%H" -- "$OUTPUT_ROOT"/    # find LAST_SHA of last docs commit
git diff "$LAST_SHA" HEAD --name-only          # list paths changed since then
git diff HEAD -- "$OUTPUT_ROOT"/               # list uncommitted edits in docs folder
```

The path-change list is mapped to a step-skip plan (source-only changes → STEPS 1–5 + 8; docs-only changes → STEP 8 only; nothing changed → confirmation prompt). Uncommitted edits in the docs folder trigger a continue/abort prompt before agents run.

**STEP 0.5 — Legacy migration.** Uses `git mv` when inside a git repo so history is preserved; falls back to plain filesystem moves only when necessary. Never overwrites an existing target file; never deletes content without first moving it.

**STEP 5 — Pre-ADR sync.** Runs `git pull` (or equivalent) immediately before dispatching `adr-writer` to ensure the local `OUTPUT_ROOT/architecture/decisions/` folder reflects the latest remote state. This is the project's primary defense against ADR-number collisions when multiple developers run the workflow concurrently.

**Degraded mode.** If `git` is unavailable: STEP 0.4 logs a warning and runs all steps; STEP 0.5 falls back to filesystem moves; STEP 5 proceeds without the sync, accepting the small collision risk.

## Superpowers Plugin (optional)

The orchestrator detects Superpowers via either of:

- `.claude/skills/superpowers` directory existing in the target project, or
- Superpowers skills listed in `.claude/settings.json`.

When present, every subagent invokes skills directly via the `Skill` tool granted in its frontmatter. The orchestrator's § Superpowers usage prescribes one skill per agent and leaves the rest permissive:

- **Prescribed (every writer and auditor)** — `verification-before-completion` before returning step output, to ground claims in code rather than inference. Each agent prompt carries the directive in its § Skills usage (when available) section.
- **Permissive (every agent)** — other Superpowers skills (e.g., `brainstorming`, `writing-plans`) MAY be invoked when an agent identifies one whose description clearly applies to a sub-task. Additional skills are intentionally not hard-named here to avoid coupling to a specific Superpowers version.

Constraints carried over: Superpowers usage must respect this orchestrator's safety rules — no blind overwrites, no deletion of legacy files, no inventing facts not supported by the codebase. Superpowers is never required; the workflow runs identically without it, and agents apply the same disciplines manually in that case. The `verification-before-completion` prescription is soft (prompt-level) enforcement; STEP 6 (the auditor) is the structural defense against unverified claims in `mode=full` runs.

## Target-Project Filesystem

The skill is fundamentally a filesystem rewriter. It reads project source as input and writes markdown as output.

**Reads:**

- `CLAUDE.md` (target project root) — domain rules and existing taxonomy references.
- Project source — language-specific config (`package.json`, `*.csproj`, `*.sln`, `Program.cs`, `Startup.cs`, etc.) is detected for `PROJECT_TYPE`.
- Existing files under `OUTPUT_ROOT/` — preserved and incrementally updated.
- Legacy doc layouts (when they exist) — `OUTPUT_ROOT/decisions/`, `OUTPUT_ROOT/specs/01-architecture.md`, etc.
- `.claude/skills/superpowers` and `.claude/settings.json` — optional plugin detection.

**Writes:**

- `CLAUDE.md` — updated in place; legacy section headings preserved when present, new sections appended only when missing.
- `OUTPUT_ROOT/architecture/{overview,components,integrations}.md`
- `OUTPUT_ROOT/architecture/decisions/NNNN-*.md` (MADR-format ADRs)
- `OUTPUT_ROOT/conventions/{coding,testing,naming,api}.md`
- `OUTPUT_ROOT/specs/00-overview.md` (plus optional feature specs)
- `OUTPUT_ROOT/reference/api.md` (only when the codebase has an API surface — HTTP routes, GraphQL schemas, gRPC services, public library exports, or consumed-API clients; not created as a stub otherwise)
- `OUTPUT_ROOT/summary/latest-run.md`
- `OUTPUT_ROOT/summary/runs/YYYYMMDD-HHMMSS.md`

**Folders the orchestrator creates with `.gitkeep` placeholders** (STEP 0): all of the above directories plus `OUTPUT_ROOT/plans/`. The `plans/` folder is preserved across runs but never auto-managed — implementation plans are user-authored, not generated.

## Deployment Path (filesystem copy)

Installation into a target project is a pure filesystem copy — no package manager, no build step, no service registration:

```bash
# From the target project root:
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
# Then invoke:
/generate-knowledge-base [output-root-folder] [mode=full|light|force]
```

After deployment, Claude Code in the target project loads `.claude/commands/generate-knowledge-base.md` as a custom slash command and resolves subagents from `.claude/agents/` by their frontmatter `name:` field.

This repository's own `.claude/` directory is local dev-time configuration for working on the skill itself; it is not part of the deployable surface.

## Things This Project Does Not Integrate With

To preempt audit confusion: this project has no integration with any of the following.

- HTTP frameworks, REST or GraphQL clients/servers — there is no network surface.
- Databases (relational or otherwise), ORMs, migration tools.
- Message brokers, queues, event buses (Kafka, RabbitMQ, SQS, NATS, etc.).
- Schedulers, cron, background-job runners.
- Auth providers (OAuth, OIDC, SAML, etc.) — the slash command runs under whatever identity Claude Code itself authenticates as.
- Third-party SaaS APIs at runtime.
- Cloud storage (S3, GCS, blob storage) or CDNs.
- Containerization runtimes — there is nothing to containerize.

This is why no `OUTPUT_ROOT/reference/api.md` exists in this repository: there are no APIs to document, so the file is not created (not even as a stub). The folder exists (tracked by `.gitkeep` from STEP 0) but remains empty by design — the absence of `api.md` is the correct shape per `spec-writer.md` § API-presence rule.

## Dev Tooling (not part of the skill)

`scripts/smoke_grade.py` is an ad-hoc LLM-judge regression grader that uses the Anthropic Python SDK and Pydantic. It is invoked manually outside the Claude Code workflow and is not consumed by the orchestrator or any subagent at runtime. It is not part of the deployable skill — it is excluded from the `.claude/agents/` and `.claude/commands/` copy step. The script pins a specific model ID (`JUDGE_MODEL = "claude-opus-4-7"`) under the dev-tooling carve-out codified in `CLAUDE.md` § Model and Effort Policy: the Anthropic SDK does not resolve generic aliases like `opus`, so dev tooling that calls the SDK directly must use exact model IDs. The pin is bumped on model launches, not removed.

## Assumptions

- Claude Code's `Agent` dispatch is synchronous from the orchestrator's perspective — the orchestrator waits for each agent's final message before continuing. The skill's phase-based ordering relies on this.
- `/effort` and `/init` are stable harness slash commands; if either is renamed or removed by the harness, the orchestrator's "graceful degradation" path is the documented fallback but has not been canary-tested in this repo.
- Superpowers plugin detection by directory or settings entry is sufficient; the orchestrator does not call any Superpowers introspection API to confirm capability before delegating.
- `git` operations assume a standard CLI git binary on `$PATH`; alternative VCS (Mercurial, Jujutsu, Fossil) is not supported and would put the workflow in degraded mode.
- The deployment copy is one-way and idempotent; updating the skill in a target project means re-running the same `cp` commands from a refreshed source checkout.
