# Agents

Six specialised subagents that do the analytical and writing work for the `generate-knowledge-base` workflow. The orchestrator delegates to them — they never run standalone.

## Deployment

Before running the workflow, copy these files into `.claude/agents/` inside your **target project**:

```bash
cp /path/to/generate-knowledge-base/Agents/*.md .claude/agents/
```

The orchestrator verifies all six files exist at startup and hard-stops with a specific error if any are missing.

## Agent overview

| Agent | Step | Role | Writes files? |
|---|---|---|---|
| `spec-brainstormer` | STEP 1 | Analyses the codebase and produces a structured report | No |
| `spec-writer` | STEP 2 + STEP 4 | Writes architecture docs (STEP 2) and specs (STEP 4) | Yes |
| `conventions-writer` | STEP 3 | Extracts coding, testing, naming, and API conventions | Yes |
| `legacy-doc-consolidator` | STEP 0.6 | Classifies and merges legacy docs into the new taxonomy | Yes |
| `adr-writer` | STEP 5 | Identifies architectural decisions and writes MADR-format ADRs | Yes |
| `spec-auditor` | STEP 6 | Reviews all generated docs against real code, proposes corrections | No |

---

## spec-brainstormer

**What it does:** Reads `CLAUDE.md` and scans the full repository to build an evidence-based mental model of the system. Returns a structured report — it never creates or modifies files.

**Input:** `CLAUDE.md`, the codebase, `PROJECT_TYPE` and `OUTPUT_ROOT` from the orchestrator.

**Output:** A structured report covering system purpose, layers, patterns, external dependencies, API/service topology, and anything unclear or inconsistent. Ends with an `## Assumptions` section.

**Key behaviour:**
- Adapts its analysis strategy to `PROJECT_TYPE` (frontend scans differ from backend-dotnet scans)
- Only makes claims supported by repository evidence — no inferences presented as facts
- Internal fan-out is allowed for independent read-only scans across separate top-level areas, provided the result is merged into one report before returning

**Tools:** `Read`, `Bash`, `Glob`, `Grep`

---

## spec-writer

**What it does:** The primary documentation writer. Invoked twice by the orchestrator with different target file sets.

- **STEP 2 (architecture):** writes `architecture/overview.md`, `architecture/components.md`, `architecture/integrations.md`, and `reference/api.md` when relevant
- **STEP 4 (specs):** writes `specs/00-overview.md` and additional feature specs when clearly supported by the codebase

**Input:** The brainstorm report from `spec-brainstormer`, `CLAUDE.md`, the codebase, existing docs under `OUTPUT_ROOT`, and `PROJECT_TYPE`/`OUTPUT_ROOT` from the orchestrator.

**Key behaviour:**
- Uses `Bash` or `Grep` to verify codebase facts before writing — no unconfirmed claims
- Prefers incremental updates over full rewrites when files already exist
- Every generated file ends with `## Assumptions`
- Architecture docs focus on structure; spec docs focus on product behaviour — these concerns are kept separate

**Tools:** `Read`, `Write`, `Bash`, `Grep`

---

## conventions-writer

**What it does:** Scans the codebase to extract stable, repeatable implementation rules and writes them as convention documents.

**Output files:**
- `conventions/coding.md` — layering, DI, error handling, async patterns, state management
- `conventions/testing.md` — frameworks, test placement, fixture patterns, integration vs unit
- `conventions/naming.md` — namespaces, DTOs, components, hooks, services, interfaces
- `conventions/api.md` — route style, versioning, auth, error payloads (when relevant)

**Key behaviour:**
- Distinguishes **required patterns** (strongly established in the codebase) from **observed conventions** (common but not certain enough to state as rules) — every convention doc makes this distinction explicit
- Never documents one-off feature behaviour as a convention
- Includes concrete examples from the repo when useful

**Tools:** `Read`, `Write`, `Bash`, `Glob`, `Grep`

---

## legacy-doc-consolidator

**What it does:** After STEP 0.5 moves legacy files to their new locations, this agent reads what remains, classifies the content, and merges durable knowledge into the canonical docs. It preserves legacy files — it never deletes them.

**Input:** Legacy markdown files after migration, existing canonical docs, and the codebase for validation.

**Classification categories:**

| Category | Destination |
|---|---|
| architecture | `OUTPUT_ROOT/architecture/` |
| conventions | `OUTPUT_ROOT/conventions/` |
| spec | `OUTPUT_ROOT/specs/` |
| plan | `OUTPUT_ROOT/plans/` |
| reference | `OUTPUT_ROOT/reference/` |
| unresolved | Left in legacy file, flagged for human review |

**Key behaviour:**
- Consolidation is an editorial pass, not a mechanical move — content is normalised and summarised, not copied verbatim
- When a legacy file mixes concerns, its content is split by destination category
- Uncertain or unverifiable content is marked unresolved and left for human review
- Returns a consolidation report listing every file reviewed, every canonical doc updated, and every unresolved item

**Tools:** `Read`, `Write`, `Bash`, `Glob`, `Grep`

---

## adr-writer

**What it does:** Identifies 3–5 significant architectural decisions clearly evident in the codebase and writes one MADR-format ADR file per decision.

**Output:** ADR files at `OUTPUT_ROOT/architecture/decisions/NNNN-short-title-in-kebab-case.md`

**Key behaviour:**
- Never invents decisions not supported by the code or existing docs
- Assigns all ADR numbers in a single coordinated pass before writing any file — this prevents numbering collisions
- If an ADR already exists for the same decision, updates it rather than creating a duplicate
- If a new ADR supersedes an existing one, updates the old ADR's `Status` field to `Superseded by NNNN`
- Before running, the orchestrator performs a `git pull` to ensure the local decisions folder is current (prevents concurrent-run collisions)

**MADR format:**
```markdown
# NNNN. Short Title in Title Case

Date: YYYY-MM-DD

## Status
Accepted

## Context and Problem Statement
[What forced this decision?]

## Considered Options
- Option A
- Option B

## Decision Outcome
Chosen option: **Option A**, because [rationale tied to codebase evidence].

### Consequences
- Good: [benefit]
- Bad: [trade-off]
```

**Tools:** `Read`, `Write`, `Bash`, `Glob`

---

## spec-auditor

**What it does:** Reviews every generated doc against the real codebase and produces a prioritised list of corrections. It **never modifies files** — it only reports.

**Reviews all files in:**
- `OUTPUT_ROOT/architecture/`
- `OUTPUT_ROOT/conventions/`
- `OUTPUT_ROOT/specs/`
- `OUTPUT_ROOT/reference/`
- `OUTPUT_ROOT/architecture/decisions/`

**For each file, it checks:**
1. Contradictions with the real code
2. Assumptions that cannot be verified
3. Missing information that should be present
4. Sections that are vague or overly generic
5. Content that belongs in a different doc category

**Output:** A structured audit report, one section per file, with issues labelled `High`, `Medium`, or `Low`. Corrections are applied in STEP 7 after the user reviews and confirms the list.

**Key behaviour:**
- References concrete code locations where possible — not vague observations
- Internal fan-out is allowed for independent per-file audits, provided the result is merged into one prioritised list before returning

**Tools:** `Read`, `Bash`, `Glob`, `Grep`

---

## Extending the workflow

To add a new agent:

1. Create a new `.md` file in this directory following the frontmatter format:
   ```yaml
   ---
   name: your-agent-name
   description: One-line description used by the orchestrator to identify this agent.
   tools: [Read, Write, Bash, Glob, Grep]
   ---
   ```
2. Add a deployment step and invocation in `generate-knowledge-base.md`
3. Add the new agent path to the pre-flight check list in STEP 0
4. Update the `cp` command in the main README to include the new file
