# Claude Code Skills

A collection of multi-agent Claude Code skills. `generate-knowledge-base` and `generate-prd` are markdown orchestrators + subagents deployed into a target project via `.claude/commands/` and `.claude/agents/`. `development-workflow` is a single skill installed at user level.

| Skill | Command | What it does |
|---|---|---|
| [`generate-knowledge-base`](#generate-knowledge-base) | `/generate-knowledge-base` | Generates architecture docs, conventions, specs, ADRs, and API reference for any codebase |
| [`generate-prd`](#generate-prd) | `/generate-prd` | Turns customer conversation transcripts into a PRD via a typed-critic discovery loop |
| [`development-workflow`](#development-workflow) | `/development-workflow` | Runs an engineering task through the Ouroboros → Superpowers pipeline with human gates and resumable state |

---

# generate-knowledge-base

Generate a living knowledge base for any software project in a single Claude Code command.

## What it does

When you join a new codebase, you spend days building a mental model that experienced team members carry in their heads — what the system does, how the layers fit together, what patterns are followed, and why key decisions were made. That knowledge is rarely written down, and when it is, it drifts out of sync with the code.

`generate-knowledge-base` runs a structured, multi-agent analysis of your codebase and produces a complete, evidence-based knowledge base: architecture docs, coding conventions, product specs, architectural decision records, and an API reference. Re-run it as the codebase evolves — it updates docs in place rather than rewriting from scratch.

## Quick start

```bash
# 1. Deploy the orchestrator to your project
mkdir -p .claude/commands
cp /path/to/generate-knowledge-base/generate-knowledge-base.md .claude/commands/

# 2. Deploy the agents
mkdir -p .claude/agents
cp /path/to/generate-knowledge-base/Agents/[a-z]*-*.md .claude/agents/

# 3. Run from your project root in Claude Code
/generate-knowledge-base
```

Docs are written to `docs/` by default. Pass a custom folder as the first argument:

```bash
/generate-knowledge-base my-docs
```

## What gets generated

| Output | Path | Purpose |
|---|---|---|
| Architecture overview | `docs/architecture/overview.md` | System purpose, layers, major flows |
| Components | `docs/architecture/components.md` | Modules, responsibilities, dependency flow |
| Integrations | `docs/architecture/integrations.md` | Databases, queues, external APIs, services |
| API reference | `docs/reference/api.md` | Routes, auth, request/response patterns (when applicable) |
| Coding conventions | `docs/conventions/coding.md` | Layering, error handling, async patterns |
| Testing conventions | `docs/conventions/testing.md` | Frameworks, test placement, fixture patterns |
| Naming conventions | `docs/conventions/naming.md` | Namespaces, DTOs, components, interfaces |
| Specs overview | `docs/specs/00-overview.md` | Product behavior and feature areas |
| ADRs | `docs/architecture/decisions/NNNN-*.md` | MADR-format architectural decision records |

## Execution modes

| Mode | What runs |
|---|---|
| `mode=full` (default) | Complete workflow: brainstorm, all doc generation, legacy migration, ADRs, audit, corrections, CLAUDE.md finalization |
| `mode=light` | Essential steps only: brainstorm, architecture docs, conventions, specs, CLAUDE.md finalization |
| `mode=force` | Same as `full` but skips git-diff scoping and uncommitted-change confirmation |

```bash
/generate-knowledge-base docs mode=light
/generate-knowledge-base docs mode=force
```

Use `mode=light` for a quick refresh. Use `mode=force` when the docs folder is out of sync with git.

## Supported project types

The workflow auto-detects your stack:

| Type | Detected from |
|---|---|
| `frontend` | `package.json` with React, Next, Angular, Vue, Nuxt, or Astro |
| `backend-dotnet` | `*.csproj`, `*.sln`, `Program.cs`, or `Startup.cs` |
| `backend-node` | `package.json` with Express, Fastify, Koa, NestJS, or Hapi |
| `mixed` | Both frontend and backend indicators present |

For `mixed` projects, pass an explicit output root or run from within the specific app subdirectory.

## How it works

The orchestrator runs a 12-step pipeline, delegating analytical and writing work to six specialized subagents. Steps execute strictly sequentially — no overlapping writes.

```
STEP 0    Pre-flight: detect project type, verify agents, init CLAUDE.md, create folders
STEP 0.4  Idempotency: git-diff scoping + manual edit detection
STEP 0.5  Migrate legacy doc layouts to new taxonomy (full mode only)
STEP 0.6  Consolidate legacy content into canonical docs (full mode only)
STEP 1    Brainstorm: deep codebase analysis via spec-brainstormer (read-only)
STEP 2    Architecture docs via spec-writer
STEP 3    Conventions docs via conventions-writer
STEP 4    Specs via spec-writer (second invocation)
STEP 5    ADRs via adr-writer (full mode only)
STEP 6    Audit all docs via spec-auditor (full mode only, read-only)
STEP 7    Apply corrections after user review (full mode only)
STEP 8    Finalize CLAUDE.md
```

Each agent is a markdown file with YAML frontmatter — no compiled code. See [`generate-knowledge-base/Agents/README.md`](generate-knowledge-base/Agents/README.md) for what each agent does.

## CLAUDE.md integration

After a run, your project's `CLAUDE.md` is updated so Claude Code automatically loads the right context before making changes:

```markdown
## Architecture
- Read docs/architecture/overview.md before making structural changes

## Conventions
- Read docs/conventions/ before generating or modifying code

## ADR Workflow
- ADRs live in docs/architecture/decisions/
- Name files: NNNN-short-title-in-kebab-case.md
```

## Re-running

On subsequent runs the workflow uses `git log`/`git diff` to detect what changed since the last docs commit and skips unchanged steps. Commit the output after each run to establish the baseline:

```bash
git add docs/ CLAUDE.md
git commit -m "docs: update knowledge base"
```

## Repository structure

```
generate-knowledge-base/
  generate-knowledge-base.md   Orchestrator (deploy to .claude/commands/)
  Agents/
    spec-brainstormer.md       Read-only codebase analyzer (STEP 1)
    spec-writer.md             Architecture + spec writer (STEPS 2, 4)
    conventions-writer.md      Convention extractor (STEP 3)
    legacy-doc-consolidator.md Legacy doc merger (STEP 0.6)
    adr-writer.md              ADR writer with deduplication (STEP 5)
    spec-auditor.md            Read-only doc auditor (STEP 6)
    README.md                  Agent documentation
  docs/
    install.md                 Detailed install, verification, troubleshooting
    walkthrough.md             Worked example: full-mode run end to end
  README.md                    Detailed usage and troubleshooting
docs/                          Generated knowledge base (this repo documents itself)
```

Full docs: [`generate-knowledge-base/README.md`](generate-knowledge-base/README.md) · [Install guide](generate-knowledge-base/docs/install.md) · [Walkthrough](generate-knowledge-base/docs/walkthrough.md)

---

# generate-prd


Turn customer conversation transcripts into a PRD via an unbounded discovery loop with a typed critic.

## What it does

Drop conversation transcripts (Zoom/Teams VTT, Granola export, Word paste, hand-typed notes) into `transcripts/` and run `/generate-prd`. The skill:

1. **Normalizes** every transcript to a canonical speaker-turn format, applying a glossary for transcription-error fixes.
2. **Distills** each transcript independently into problems, jobs-to-be-done, pains, personas, and customer-proposed solutions — with `[T<id>:<timestamp>]` citations.
3. **Clusters** distillations into cross-transcript themes with frequency counts and contradictions surfaced.
4. **Drafts** a PRD where evidence-anchored sections are populated from themes and PM-judgment sections are deliberately left empty.
5. **Enters a discovery loop** with you. Every iteration: a read-only critic surfaces typed findings; you discuss; the drafter refines. **No iteration cap. Closure is yours alone — type `/done` when you decide.**
6. **Finalizes** with a completeness/citations/recommendations report.

The skill never reads the host codebase — all discovery is grounded in the transcripts and your judgment.

## Quick start

```bash
# 1. Deploy the orchestrator and agents
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-prd/generate-prd.md .claude/commands/
cp /path/to/generate-prd/Agents/*.md .claude/agents/

# 2. Put transcripts in your project root
mkdir transcripts/
# copy .vtt, .srt, .md, or .txt transcript files here

# 3. Run in Claude Code
/generate-prd
```

## The 7 critic finding types

| Type | What it surfaces |
|---|---|
| `CONTRADICTION` | The draft disagrees with what the transcripts actually said |
| `COVERAGE_GAP` | A high-frequency theme is missing from the PRD |
| `UNSUPPORTED_ASSUMPTION` | A claim has no transcript backing and no PM justification |
| `SOLUTION_BIAS` | A section anchors on implementation rather than capability |
| `GOAL_METRIC_MISMATCH` | A goal has no matching metric, or vice versa |
| `PERSONA_STORY_MISMATCH` | A user story names a persona not declared in Target Users |
| `EVIDENCE_THIN` | A claim cites very few transcripts relative to the weight it carries |

## Loop commands

| Command | Effect |
|---|---|
| Enter | Discuss the recommended finding |
| `/refine` | Apply the discussion's resolution to the PRD, then continue |
| `/skip` | Skip the iteration without changing the draft |
| `/pause` | Save state and exit cleanly |
| `/done` | Exit the loop and finalize |
| `/status` | Show iterations, Q&A count, cost estimate, and finding density |

## Repository structure

```
generate-prd/
  generate-prd.md        Orchestrator (deploy to .claude/commands/)
  Agents/                6 subagents (deploy to .claude/agents/)
  prompts/               7 prompt files (read at runtime, not deployed)
  schema/                State schema, PRD template, transcript format, migrations
  tests/                 94-test static suite + golden corpus + durability playbooks
  docs/                  README, install guide, walkthrough
```

Full docs: [`generate-prd/README.md`](generate-prd/README.md) · [Install guide](generate-prd/docs/install.md) · [Walkthrough](generate-prd/docs/walkthrough.md)

---

# development-workflow

Run a piece of engineering work through a six-phase pipeline that combines Ouroboros (requirements and evaluation) with Superpowers (planning and execution).

## What it does

The skill is a `SKILL.md` plus on-demand `references/` that acts as a resumable state machine. See the [`development-workflow` README](development-workflow/README.md) for the details. It stops at every human gate the pipeline requires and writes its own artifacts to disk, so a new session can pick a run back up. It is opt-in: it only runs when you explicitly ask for the dev workflow or full pipeline, and it never blocks direct use of `superpowers:brainstorming` or the Ouroboros tools.

| Phase | What happens |
|---|---|
| 0. Classify and preflight | Decides whether the work is in scope (multi-file change, ambiguous requirements, or infrastructure). It also checks that the model setting is `opusplan` and that the Ouroboros tools can be loaded, before creating anything. Out-of-scope work, such as a typo fix, gets your call: the skill explains how it classified the request and offers to run the pipeline anyway, or makes the change directly. Nothing is created unless you opt in. |
| 1. Requirements → Seed | Interviews you if goal, constraints, and success criteria aren't all stated, then generates a Seed spec and asks you to approve it before Phase 2. Runs in plan mode. |
| 2. Design review & plan | Runs `superpowers:brainstorming` with the Seed as context and follows its classification. Bounded work gets a short in-chat design and no plan. Architectural work gets a written plan. A spike gets an answer and no code to keep. Before you see the design or plan, a separate reviewer subagent audits the Seed, design and plan against each other and the repo (every acceptance criterion needs a design element and something that proves it). If the design touches auth or a public network surface, a separate reviewer subagent checks it for security risks before you see it. |
| 3. Isolate & execute | Creates a git worktree for the branch (skipped outside a git repo), then implements with TDD on Sonnet. Multi-task architectural plans run through `superpowers:subagent-driven-development`, and bounded changes run inline. |
| 4. Evaluate | Runs the project's real test command and typecheck (and its lint command, if it defines one), grades the diff against the Seed with `ouroboros_qa`, and dispatches a separate reviewer subagent to run `pr-review-toolkit:review-pr` on the branch diff, unless `subagent-driven-development`'s final review already came back clean (a review always runs after a repair loop). Runs a dependency audit when the diff changes a manifest or lockfile; a check that can't run (the audit, or a missing `pr-review-toolkit`) needs your explicit OK to skip. A REVISE or FAIL verdict is reported to you, never auto-retried. |
| 5. Finish & push | Checks docs are in sync (and, if your instructions require it, audits every instructional file the branch changes and waits for your ruling on findings), verifies, then finishes the branch. |

## Requirements

- The [Ouroboros](https://github.com/Q00/ouroboros) plugin (the `ouroboros_*` MCP tools)
- The `superpowers` and `pr-review-toolkit` plugins
- `"model": "opusplan"` in `~/.claude/settings.json`, so planning runs on Opus and implementation on Sonnet. Keep `/fast` off during Phase 3, since it forces the main session onto Opus. Implementers are dispatched on Sonnet. Reviewers and auditors are dispatched on Opus, and the test gate in Phases 4 and 5 runs in an Opus subagent because the main session is on Sonnet by then. Phase 0 checks the setting, including a project-level override.
- For `ouroboros_qa` to run on Opus, `~/.ouroboros/config.yaml` sets `models.pin: true` and `llm.qa_model: opus`. Without it QA runs on Sonnet, and the skill tells you so before the Seed check.

The skill carries its own model policy, commit rules, and review order, so it doesn't depend on this repo's [`CLAUDE.md`](CLAUDE.md). Its greenfield stack defaults (TypeScript in strict mode with Vitest; no default framework) copy the ones in the author's global `~/.claude/CLAUDE.md`. If your own `CLAUDE.md` names a different stack, the skill asks which to use.

## Quick start

```bash
# Install as a user-level skill
mkdir -p ~/.claude/skills/development-workflow
cp -r development-workflow/SKILL.md development-workflow/references ~/.claude/skills/development-workflow/
```

`SKILL.md` points to files under `references/`, so copy the directory along with it. The installed copy is a plain copy, not a link: after editing the repo, run the same command again.

Then ask for it by name in Claude Code:

```
/development-workflow add rate limiting to the upload endpoint
```

## Where artifacts go

Seed, design, and plan files are never written into the target repo. Each run gets its own directory at `~/.claude/dev-workflow-runs/<repo-slug>/<YYYY-MM-DD>-<task-slug>/`, alongside a `state.json` that records status and completed steps for resuming.

## Repository structure

```
development-workflow/
  README.md     User-facing overview of the skill
  SKILL.md      The skill (deploy to ~/.claude/skills/development-workflow/)
  references/   Detail that SKILL.md loads at the phase that needs it: seed generation
                edge cases, Seed QA, doc baseline, Phase 3 execution, Phase 4 QA,
                the reviewer subagent brief, run lifecycle details, and Context7
                and stack defaults
  evals/        evals.json (38 test prompts with expectations) and files/
                build-fixtures.sh for the sandboxes they run in
  DESIGN.md     Design rationale, audit history, and later changes
```

---

## License

GPL-3.0
