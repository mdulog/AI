# Product Behavior Overview

This document describes the externally visible behavior and feature areas of `generate-knowledge-base`. It covers what the tool does from the user's perspective -- execution modes, detection logic, idempotency guarantees, migration behavior, and the audit/correction workflow. For structural and component-level details, see [architecture/overview.md](../architecture/overview.md) and [architecture/components.md](../architecture/components.md).

## Execution Modes

The tool supports three execution modes that control which workflow steps run. The mode is passed as part of `$ARGUMENTS` (e.g., `/generate-knowledge-base docs mode=light`). When no mode is specified, `full` is used.

### Full Mode (default)

Runs the complete workflow:

1. Pre-flight checks (project type detection, agent verification, CLAUDE.md initialization, folder creation)
2. Idempotency pre-flight (git-diff scoping and manual edit detection)
3. Legacy doc migration and consolidation
4. Codebase brainstorm (deep analysis producing a structured report)
5. Architecture doc generation (overview, components, integrations, API reference)
6. Conventions extraction (coding, testing, naming, API conventions)
7. Specs generation (product behavior and feature area documentation)
8. ADR creation (3-5 architectural decision records in MADR format)
9. Audit (all generated docs reviewed against real code; prioritized correction list produced)
10. Correction application (user reviews and confirms corrections before any edits)
11. CLAUDE.md finalization (update references to generated docs)
12. Run summary (persistent artifact written to `summary/latest-run.md` and timestamped copy)

Full mode is appropriate when running for the first time, after significant codebase changes, or when a thorough documentation refresh is needed.

### Light Mode

Runs only essential steps: pre-flight, idempotency check, brainstorm, architecture docs, conventions, specs, and CLAUDE.md finalization. Specifically skipped:

- Legacy doc migration (STEP 0.5)
- Legacy doc consolidation (STEP 0.6)
- ADR creation (STEP 5)
- Audit (STEP 6)
- Correction application (STEP 7)

Light mode is useful for a quick documentation refresh when legacy migration and deep audit are unnecessary. Users can explicitly request any skipped step even in light mode.

### Force Mode

Identical to full mode in terms of which steps execute, but bypasses the STEP 0.4 idempotency pre-flight entirely -- both git-diff scoping and manual edit confirmation are skipped. All steps run unconditionally.

Use force mode when the docs folder is out of sync with git -- for example, when a previous run completed but the output was never committed, or when the git history does not accurately reflect the documentation state.

## Project Type Auto-Detection

At startup (STEP 0), the orchestrator inspects repository files to determine the project type. The detected type influences how subagents adapt their analysis strategy. Detection follows a priority order:

| Detected Type | Trigger Condition |
|---|---|
| `frontend` | `package.json` exists with dependencies including any of: `react`, `next`, `@angular/core`, `@angular/cli`, `vue`, `nuxt`, `astro` |
| `backend-dotnet` | Any `*.csproj` or `*.sln` file exists, or `Program.cs` / `Startup.cs` is found |
| `backend-node` | `package.json` exists with dependencies including: `express`, `fastify`, `koa`, `nestjs`, `hapi` |
| `mixed` | Both frontend and backend indicators are present |

### Mixed Project Handling

When `mixed` is detected and no explicit `OUTPUT_ROOT` was provided via `$ARGUMENTS`, the workflow stops and asks the user to either:

- Re-run the command from within the specific app subdirectory, or
- Pass an explicit output root argument to scope the run (e.g., `/generate-knowledge-base apps/api/docs`)

If `$ARGUMENTS` is set (providing an output root), a `mixed` detection proceeds normally -- the output root provides sufficient scoping.

**Edge case:** If `$ARGUMENTS` contains only a mode flag (e.g., `mode=light`) without an output root, `$ARGUMENTS` is non-empty but no output root is provided. The `mixed` guard may incorrectly proceed in this scenario because it checks only whether `$ARGUMENTS` is set, not whether it contains a valid output root path.

### Detection Reporting

After detection, the orchestrator reports which `PROJECT_TYPE` was chosen and which specific files led to that decision, giving the user visibility into the classification logic.

## Idempotency via Git-Diff Scoping and Manual Edit Detection

STEP 0.4 runs two checks to determine whether a full re-run is necessary. Both checks are skipped entirely in `force` mode.

### Check 1: Step Scoping via Git Diff

The orchestrator queries git for the most recent commit that touched the output root:

```
git log -1 --format="%H" -- "$OUTPUT_ROOT"/
```

Based on the result:

| Scenario | Behavior |
|---|---|
| **No prior docs commit** (empty result) | First run. All steps proceed. |
| **Prior commit found** | The SHA is captured as `LAST_SHA`. A diff is run against `HEAD` to identify changed paths. |

When a prior commit exists, changed paths are mapped to steps:

| Changed Paths | Steps That Run |
|---|---|
| Source code files changed (outside `OUTPUT_ROOT/`) | STEPS 1-5 + 8 in light mode; STEPS 0.5, 0.6, 1-7, 8 in full mode |
| Only doc files changed (inside `OUTPUT_ROOT/`) | STEP 8 only |
| Nothing changed | User is prompted: "Force re-run? [y/N]". N exits; Y runs all steps. |

The step set from git-diff scoping is intersected with the mode's permitted steps -- a step excluded by either mechanism is skipped. The orchestrator reports which steps will be skipped and why before proceeding.

### Check 2: Manual Edit Detection

The orchestrator checks for uncommitted changes in the docs folder:

```
git diff HEAD -- "$OUTPUT_ROOT"/
```

If uncommitted changes are found, the affected files are listed and the user is warned:

> These files have uncommitted changes (possible manual edits): [list].
> Agents will treat current file contents as canonical and apply incremental updates, but cannot guarantee manual edits in rewritten sections are preserved. Continue? [y/N]

- **N** exits immediately without touching any files.
- **Y** proceeds, using the current file contents (including manual edits) as the baseline for incremental updates.

If no uncommitted changes exist, the workflow proceeds without prompting.

### Degraded Mode (No Git)

When git is unavailable or the project is not a git repository, the orchestrator logs a warning, skips both idempotency checks, and runs all steps unconditionally.

## Legacy Doc Migration and Consolidation

These features handle the transition from older documentation layouts to the current folder taxonomy. Both run only in full mode (unless the user explicitly requests them in light mode).

### STEP 0.5: Safe File Migration

Before any new document generation, the orchestrator checks for legacy file and folder layouts and moves them to the new structure. Migration follows strict safety rules:

- **Never overwrites** an existing file in the new structure.
- **Never deletes** content without first moving or preserving it.
- **Prefers `git mv`** when inside a git repository to preserve history; falls back to filesystem moves when necessary.
- **Reports conflicts** without resolving them when both old and new locations contain different files.

Specific legacy paths detected and migrated:

| Legacy Path | New Path | Condition |
|---|---|---|
| `OUTPUT_ROOT/decisions/` | `OUTPUT_ROOT/architecture/decisions/` | Target is empty or missing |
| `OUTPUT_ROOT/specs/01-architecture.md` | `OUTPUT_ROOT/architecture/overview.md` | Target does not exist |
| `OUTPUT_ROOT/specs/03-api.md` | `OUTPUT_ROOT/reference/api.md` | Target does not exist |

Plans and existing feature specs are left in place -- they are not migrated.

After migration, the orchestrator reports every file or folder moved, every conflict skipped, and every legacy file still in place.

### STEP 0.6: Content Consolidation

After file migration, the `legacy-doc-consolidator` subagent performs an editorial pass over remaining legacy markdown files:

1. **Classification**: Each piece of content is classified as architecture, conventions, spec, plan, reference, or unresolved.
2. **Merging**: Durable knowledge is normalized and summarized into canonical docs in the new structure. Content is not copied verbatim -- it is distilled.
3. **Splitting**: When a legacy file mixes concerns (e.g., architecture knowledge mixed with feature specs), content is split by destination category.
4. **Preservation**: Legacy files are never deleted. They remain as historical context until a human removes them.
5. **Reporting**: A consolidation report lists every file reviewed, every canonical doc updated, and every unresolved item.

Uncertain or unverifiable content is marked unresolved and left in the legacy file for human review.

## Human-in-the-Loop Audit and Correction Workflow

The audit and correction workflow (STEPS 6-7) is the only part of the pipeline that requires explicit user confirmation before modifying files. It runs only in full mode.

### STEP 6: Audit (Read-Only)

The `spec-auditor` subagent reviews every generated doc against the real codebase. For each file, it checks:

1. Contradictions with real code
2. Assumptions that cannot be verified
3. Missing information that should be present
4. Sections that are vague or overly generic
5. Content that belongs in a different doc category

The audit produces a prioritized correction list with each issue labeled **High**, **Medium**, or **Low**. The auditor never modifies files -- it only reports findings.

### STEP 7: Correction Application

Before applying any correction, the orchestrator:

1. Presents the full list of High and Medium priority corrections to the user.
2. Waits for the user to confirm which corrections to apply.
3. Applies only confirmed corrections.

Correction rules:

- Only High and Medium priority items are applied (Low items are reported but not acted on).
- Documents are not rewritten unnecessarily -- existing content is preserved where possible.
- ADR edits are kept minimal, limited to clear factual or formatting issues.
- After editing, a summary of what changed in each file is provided.

## CLAUDE.md Integration

The workflow enriches the target project's `CLAUDE.md` at two points: during pre-flight (STEP 0) and during finalization (STEP 8).

### Pre-Flight (STEP 0)

If `CLAUDE.md` does not exist, the orchestrator runs `/init` to create one and then improves the generated file. If it already exists, the orchestrator migrates it to the new documentation taxonomy:

- Preserves all project-specific guidance, domain language, and non-documentation rules.
- Detects and updates legacy documentation references (e.g., `OUTPUT_ROOT/decisions/` becomes `OUTPUT_ROOT/architecture/decisions/`; `OUTPUT_ROOT/specs/01-architecture.md` becomes `OUTPUT_ROOT/architecture/overview.md`).
- Updates existing matching sections in place rather than appending duplicate headings.
- Adds missing sections from a standard template covering Architecture, Conventions, Specs, ADR Workflow, and Documentation.

### Finalization (STEP 8)

After all documentation is generated, the orchestrator reconciles `CLAUDE.md` one final time. It ensures these specific sections exist and reference the correct output paths:

- `## Architecture` — referencing `OUTPUT_ROOT/architecture/overview.md`, `components.md`, `integrations.md`
- `## Conventions` — referencing `OUTPUT_ROOT/conventions/`
- `## Specs` — referencing `OUTPUT_ROOT/specs/`
- `## ADR Workflow` — referencing `OUTPUT_ROOT/architecture/decisions/` with MADR naming rules
- `## Documentation` — cross-referencing all of the above

For each section: if a matching heading already exists, it is updated in place. If a section is missing entirely, it is appended from a standard template. Any remaining legacy path references (e.g., `decisions/` instead of `architecture/decisions/`) are rewritten. Unrelated project-specific guidance already in `CLAUDE.md` is preserved.

The net effect is that after a run, Claude Code automatically reads the right documentation context before making changes in the target project, because `CLAUDE.md` directs it to the generated docs.

## Incremental Doc Updates on Re-Runs

The workflow is designed for repeated execution. On subsequent runs:

- **Filenames are kept stable** between runs. The same doc paths are used each time.
- **Existing content is preserved** when it is still accurate. Agents prefer incremental edits over full rewrites.
- **New information is merged** into existing documents rather than overwriting them.
- **Idempotency scoping** (STEP 0.4) avoids redundant work when source code has not changed.
- **Manual edits are respected** as the current baseline -- agents read the existing file contents and apply incremental updates on top of them (though preservation of manual edits in rewritten sections is not guaranteed, which is why the user is warned).

The recommended workflow after each run is to commit the output:

```bash
git add docs/ CLAUDE.md
git commit -m "docs: update knowledge base"
```

This establishes the baseline that STEP 0.4 uses on the next run to determine what changed.

## Run History with Timestamped Summaries

Every run produces two summary artifacts:

| Path | Purpose |
|---|---|
| `OUTPUT_ROOT/summary/latest-run.md` | Always overwritten with the most recent run's summary |
| `OUTPUT_ROOT/summary/runs/YYYYMMDD-HHMMSS.md` | Timestamped historical copy; never overwritten |

Each run summary includes:

- Execution mode used
- Detected `PROJECT_TYPE`
- Agents invoked
- All files created, modified, moved, or intentionally skipped (with paths)
- Migration actions taken
- Conflicts or unresolved items
- Remaining assumptions or known gaps
- Recommended next steps for human review

The timestamped naming scheme (`YYYYMMDD-HHMMSS`) uses the format year-month-day-hour-minute-second, producing a naturally sortable history of all runs.

A console summary is also displayed at the end of each run. It covers the same fields as the file artifact, plus two additional items not written to the file: a confirmation that `summary/latest-run.md` and the timestamped copy were written, and a suggested git commit command for capturing the documentation baseline in history.

## Deployment Model

`generate-knowledge-base` is not a standalone application. It is a Claude Code skill that is deployed into a target project by copying files:

### Required Files

```
Source (this repo)                           Target project
generate-knowledge-base.md             -->   .claude/commands/generate-knowledge-base.md
Agents/spec-brainstormer.md            -->   .claude/agents/spec-brainstormer.md
Agents/spec-writer.md                  -->   .claude/agents/spec-writer.md
Agents/conventions-writer.md           -->   .claude/agents/conventions-writer.md
Agents/legacy-doc-consolidator.md      -->   .claude/agents/legacy-doc-consolidator.md
Agents/adr-writer.md                   -->   .claude/agents/adr-writer.md
Agents/spec-auditor.md                 -->   .claude/agents/spec-auditor.md
```

The orchestrator goes into `.claude/commands/` (making it available as `/generate-knowledge-base`). The six subagent files go into `.claude/agents/`.

### Agent Verification at Startup

At the beginning of every run (STEP 0), the orchestrator verifies that all six agent files exist in `.claude/agents/`. If any are missing, the workflow hard-stops immediately with:

- Which agent file is missing
- Which file path was expected
- Which step cannot continue
- What the user needs to create or fix

The workflow never silently falls back to performing agent work in the orchestrator context.

### Deployment Commands

```bash
# From the target project root
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

### Runtime Requirements

- **Claude Code** as the execution environment
- **Opus 4.6 model** (declared in the orchestrator's frontmatter)
- **Git** (optional; enables idempotency scoping and history-preserving migration)

## Assumptions

- The `$ARGUMENTS` string supports both a positional output-root value and a `mode=` key-value pair (e.g., `my-docs mode=light`). Parsing is handled by natural-language pattern matching at runtime, not a formal argument parser — the orchestrator checks for the `mode=` prefix to extract the mode, and uses the remaining portion as `OUTPUT_ROOT`.
- The `YYYYMMDD-HHMMSS` timestamp in run history filenames uses the local timezone of the machine where Claude Code is running. The orchestrator does not specify UTC or a fixed timezone.
- When the orchestrator detects `PROJECT_TYPE`, the dependency check for frontend frameworks scans both `dependencies` and `devDependencies` in `package.json`. The orchestrator's wording ("dependencies or devDependencies") confirms both are checked.
- The `tooling` project type assigned by the orchestrator for this project (generate-knowledge-base itself) is not one of the four auto-detected types (frontend, backend-dotnet, backend-node, mixed). This suggests that when no detection rule matches, the orchestrator either falls through without setting a type or uses a context-specific override.
- Light mode's skippable steps can be individually overridden by explicit user request. The orchestrator's language ("unless the user explicitly requests") applies to STEP 0.5, STEP 0.6, STEP 5, STEP 6, and STEP 7.
- The audit workflow (STEPS 6-7) is the only human-in-the-loop gate. All other steps run to completion without user confirmation (aside from the STEP 0.4 prompts for uncommitted changes or no-changes-detected scenarios).
- The Superpowers plugin integration mentioned in the orchestrator is optional and does not change any externally visible behavior. It is not covered in this spec because it has no user-facing behavioral impact.
