# Components

## Component Overview

The system consists of one orchestrator and six subagents. Each is a markdown file with YAML frontmatter that declares its name, description, and permitted tool set. The Claude Code runtime interprets these declarations at invocation time.

```
Orchestrator (generate-knowledge-base.md)
  |
  |-- spec-brainstormer      [STEP 1]     read-only analysis
  |-- spec-writer             [STEP 2, 4]  architecture + spec writing
  |-- conventions-writer      [STEP 3]     convention extraction
  |-- legacy-doc-consolidator [STEP 0.6]   legacy doc merging
  |-- adr-writer              [STEP 5]     decision record creation
  |-- spec-auditor            [STEP 6]     doc-vs-code audit
```

## Orchestrator

**File:** `generate-knowledge-base/generate-knowledge-base.md`

**Frontmatter:**
```yaml
allowed-tools: [Read, Write, Bash, Agent]
model: claude-opus-4-6
```

**Responsibilities:**
- Controls all execution flow through the 11-step pipeline
- Detects `PROJECT_TYPE` from repository markers (frontend, backend-dotnet, backend-node, mixed)
- Resolves `OUTPUT_ROOT` from user arguments (default: `docs`)
- Manages execution mode logic (full, light, force)
- Performs idempotency pre-flight via git-diff scoping
- Handles legacy doc migration (STEP 0.5) directly -- filesystem moves via `git mv`
- Delegates analytical and writing work to subagents via the `Agent` tool
- Passes inter-step context (brainstorm reports) inline in Agent invocations
- Enforces agent boundaries -- hard-stops if any required agent is missing
- Manages human-in-the-loop confirmation for correction application (STEP 7)
- Writes the run summary artifact and finalizes CLAUDE.md

**Boundaries:** The orchestrator does not perform deep codebase analysis or write documentation content for steps where a subagent is designated. STEPS 1, 2, 3, 4, 5, and 6 must be delegated. STEP 0.6 must use the legacy-doc-consolidator agent.

## Subagents

### spec-brainstormer

**File:** `generate-knowledge-base/Agents/spec-brainstormer.md`

**Frontmatter:**
```yaml
name: spec-brainstormer
description: Analyzes the repo and CLAUDE.md to understand purpose, layers, patterns, services, and integration points.
tools: [Read, Bash, Glob, Grep]
```

**Step:** STEP 1

**Role:** Read-only codebase analyzer. Scans the entire repository to build an evidence-based model of the system. Returns a structured report covering system purpose, layers, patterns, external dependencies, service topology, and inconsistencies.

**Inputs:** CLAUDE.md, the project codebase, PROJECT_TYPE and OUTPUT_ROOT from the orchestrator.

**Outputs:** A structured bullet-list report with section headings. Ends with an `## Assumptions` section. This report is not written to a file — it is returned to the orchestrator and passed inline to STEP 2, STEP 3, and STEP 4. This inline-passing design is a consequence of the agent's read-only tool set (no `Write`) and the supervisor-led orchestration pattern.

**Key constraints:**
- Never creates or modifies files
- Adapts analysis strategy to PROJECT_TYPE
- Only includes claims supported by repository evidence
- Internal fan-out is allowed for independent read-only scans across top-level areas, with a mandatory fan-in summary

### spec-writer

**File:** `generate-knowledge-base/Agents/spec-writer.md`

**Frontmatter:**
```yaml
name: spec-writer
description: Generates architecture, reference, and spec documents from the brainstorm report, codebase, and existing docs.
tools: [Read, Write, Bash, Grep]
```

**Steps:** STEP 2 (architecture docs) and STEP 4 (specs)

**Role:** The primary documentation writer. Invoked twice by the orchestrator with different target file sets:
- STEP 2: writes `architecture/overview.md`, `architecture/components.md`, `architecture/integrations.md`, and `reference/api.md` (when relevant)
- STEP 4: writes `specs/00-overview.md` and additional feature/domain specs when supported by the codebase

**Inputs:** The brainstorm report from spec-brainstormer, CLAUDE.md, the project codebase, existing docs under OUTPUT_ROOT, PROJECT_TYPE and OUTPUT_ROOT.

**Key constraints:**
- Uses Bash or Grep to verify codebase facts before writing -- no unconfirmed claims
- Prefers incremental edits over complete rewrites when files already exist
- Every generated file ends with `## Assumptions`
- Architecture docs focus on structure; spec docs focus on product behavior

### conventions-writer

**File:** `generate-knowledge-base/Agents/conventions-writer.md`

**Frontmatter:**
```yaml
name: conventions-writer
description: Extracts stable implementation conventions and project rules from the codebase and existing documentation.
tools: [Read, Write, Bash, Glob, Grep]
```

**Step:** STEP 3

**Role:** Scans the codebase to extract stable, repeatable implementation rules. Distinguishes between required patterns (strongly established) and observed conventions (common but not definitive).

**Outputs:** Convention files: `conventions/coding.md`, `conventions/testing.md`, `conventions/naming.md`, and `conventions/api.md` (when relevant).

**Key constraints:**
- Never documents one-off feature behavior as a convention
- Includes concrete repo examples when useful
- Each convention doc explicitly distinguishes required patterns from observed conventions

### legacy-doc-consolidator

**File:** `generate-knowledge-base/Agents/legacy-doc-consolidator.md`

**Frontmatter:**
```yaml
name: legacy-doc-consolidator
description: Reviews legacy markdown docs and consolidates durable content into the new documentation taxonomy without deleting history.
tools: [Read, Write, Bash, Glob, Grep]
```

**Step:** STEP 0.6

**Role:** After STEP 0.5 moves legacy files to new paths, this agent performs an editorial pass: reading remaining legacy markdown, classifying content into categories (architecture, conventions, spec, plan, reference, unresolved), and merging durable knowledge into canonical docs.

**Key constraints:**
- Consolidation is editorial, not mechanical -- content is normalized and summarized, not copied verbatim
- When a legacy file mixes concerns, content is split by destination category
- Never deletes legacy files -- they remain as historical context until human review
- Uncertain content is marked unresolved and flagged for human review
- Returns a consolidation report listing files reviewed, docs updated, and unresolved items

### adr-writer

**File:** `generate-knowledge-base/Agents/adr-writer.md`

**Frontmatter:**
```yaml
name: adr-writer
description: Identifies significant architectural decisions from the codebase and creates MADR-format ADR files in the architecture/decisions/ folder.
tools: [Read, Write, Bash, Glob]
```

**Step:** STEP 5

**Role:** Identifies 3-5 significant architectural decisions evident in the codebase and writes one MADR-format ADR per decision.

**Key constraints:**
- Never invents decisions not supported by the code or existing docs
- Runs a deduplication procedure before numbering: reads all existing ADRs, extracts normalized topics, and checks each candidate against the existing topic list
- Assigns all ADR numbers in a single coordinated pass before writing any file -- prevents numbering collisions
- If a new ADR supersedes an existing one, updates the old ADR's status to `Superseded by NNNN`

### spec-auditor

**File:** `generate-knowledge-base/Agents/spec-auditor.md`

**Frontmatter:**
```yaml
name: spec-auditor
description: Audits generated architecture, conventions, specs, reference docs, and ADRs against the codebase and proposes corrections.
tools: [Read, Bash, Glob, Grep]
```

**Step:** STEP 6

**Role:** Read-only reviewer. Audits every generated doc against the real codebase and produces a prioritized correction list.

**Audit scope:** All files under `architecture/`, `conventions/`, `specs/`, `reference/`, and `architecture/decisions/`.

**Checks per file:**
1. Contradictions with real code
2. Assumptions that cannot be verified
3. Missing important information
4. Vague or overly generic sections
5. Content that belongs in a different doc category

**Output:** A structured audit report with issues labeled High, Medium, or Low priority.

**Key constraints:**
- Never modifies files
- References concrete code locations where possible
- Internal fan-out is allowed for independent per-file audits with a mandatory fan-in summary

## Dependency Flow

All dependency flows are unidirectional from the orchestrator to subagents. Subagents never invoke other subagents and never communicate with each other directly.

```
Orchestrator
  --> legacy-doc-consolidator   (STEP 0.6, full mode only — classifies and merges legacy docs before new content is written)
  --> spec-brainstormer         (returns brainstorm report)
  --> spec-writer               (receives brainstorm report, writes architecture docs)
  --> conventions-writer        (receives brainstorm report, writes convention docs)
  --> spec-writer               (receives brainstorm report, writes spec docs)
  --> adr-writer                (reads architecture docs written by spec-writer)
  --> spec-auditor              (reads all docs written by previous agents)
```

The adr-writer reads the architecture docs produced by spec-writer in STEP 2. The spec-auditor reads all docs produced by all prior writing agents. These are file-level dependencies, not direct agent-to-agent communication -- the orchestrator ensures steps run in the correct order.

## Tool Permissions by Component

| Component | Read | Write | Bash | Agent | Glob | Grep |
|---|---|---|---|---|---|---|
| Orchestrator | Yes | Yes | Yes | Yes | -- | -- |
| spec-brainstormer | Yes | -- | Yes | -- | Yes | Yes |
| spec-writer | Yes | Yes | Yes | -- | -- | Yes |
| conventions-writer | Yes | Yes | Yes | -- | Yes | Yes |
| legacy-doc-consolidator | Yes | Yes | Yes | -- | Yes | Yes |
| adr-writer | Yes | Yes | Yes | -- | Yes | -- |
| spec-auditor | Yes | -- | Yes | -- | Yes | Yes |

Read-only agents (spec-brainstormer, spec-auditor) lack the `Write` tool. Only the orchestrator has the `Agent` tool, enforcing the supervisor-led pattern. The orchestrator also lacks `Glob` and `Grep` — it uses `Bash` for all file-discovery operations, which is an intentional constraint of the command frontmatter. The `spec-writer` is the only write agent without `Glob`; it uses `Bash` and `Grep` for targeted file discovery, consistent with its verify-before-writing mandate.

## Assumptions

- Subagents inherit the model from the orchestrator's `model: claude-opus-4-6` declaration or follow Claude Code's default model selection. The subagent frontmatter does not declare a model independently.
- The `tools` key in subagent frontmatter and the `allowed-tools` key in the orchestrator frontmatter serve the same purpose (declaring permitted Claude Code tools) but use different key names. This is assumed to be a Claude Code convention where commands use `allowed-tools` and agents use `tools`.
- The orchestrator's `Agent` tool is the sole mechanism for invoking subagents. There is no code-level invocation, HTTP call, or message queue.
- Fan-out parallelism within a step is an optimization hint to the Claude Code runtime, not a guaranteed parallel execution -- the runtime may serialize agent work regardless.
