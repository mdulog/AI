# Walkthrough — a full-mode run on a backend Node.js project

A worked example showing what running `/generate-knowledge-base` actually feels like from start to finish. Names, file content, and timings are illustrative — your real run will look similar.

> **Note:** This is a narrative example written from the spec and the agent definitions. Once you run a real session you may want to replace or supplement this with a captured transcript. The narrative below is what the skill should produce.

---

## The target project

A backend Node.js API — Express, PostgreSQL, a handful of services and controllers. The repo has no `docs/` folder yet. This is the first run.

```bash
$ ls
src/
  controllers/
  services/
  repositories/
  middleware/
  models/
package.json
.env.example
README.md
```

The skill is installed per [`install.md`](install.md). The engineer opens Claude Code at the project root and runs:

```
/generate-knowledge-base
```

---

## STEP 0 — Pre-flight

```
> Detected PROJECT_TYPE: backend-node (Express, PostgreSQL markers found)
> Verified 6 agents present in .claude/agents/
> OUTPUT_ROOT: docs
> Mode: full
> No existing CLAUDE.md — will initialize at STEP 8.
> Creating folder structure:
>   docs/architecture/decisions/
>   docs/conventions/
>   docs/specs/
>   docs/reference/
>   docs/plans/
>   docs/summary/runs/
> STEP 0 complete.
```

The engineer sees folder creation messages but no questions. The workflow is autonomous through STEP 7.

---

## STEP 0.4 — Idempotency pre-flight

No prior docs commit exists, so git-diff scoping has no baseline to compare against. All steps are marked as needing to run.

```
> No prior docs commit found — running all steps.
```

---

## STEP 1 — Brainstorm (~2 minutes)

The `spec-brainstormer` agent (Opus, high effort) fans out across the codebase. It reads every source file, traces the layers, identifies design patterns, and produces a structured analysis report consumed by every downstream step.

```
> STEP 1: dispatching spec-brainstormer (Opus, high effort)...
> ✓ STEP 1 complete — structured analysis report ready.
```

The engineer doesn't see the report directly — it's passed inline to the writer agents in the steps that follow.

---

## STEP 2 — Architecture docs (~60 seconds)

The `spec-writer` agent generates three files from the brainstorm report:

```
> STEP 2: dispatching spec-writer (architecture docs)...
> ✓ docs/architecture/overview.md
> ✓ docs/architecture/components.md
> ✓ docs/architecture/integrations.md
> ✓ docs/reference/api.md (API surface detected — Express routes found)
> STEP 2 complete.
```

The engineer opens `docs/architecture/overview.md` and sees a populated document: system purpose, the three-layer architecture (controllers → services → repositories), the PostgreSQL integration, and the auth middleware pattern. Every claim cites a real file.

---

## STEP 3 — Conventions docs (~45 seconds)

```
> STEP 3: dispatching conventions-writer...
> ✓ docs/conventions/coding.md
> ✓ docs/conventions/testing.md
> ✓ docs/conventions/naming.md
> STEP 3 complete.
```

`docs/conventions/coding.md` captures the async/await pattern used throughout, the error-propagation shape (thrown errors caught at the controller boundary), and the DI style (constructor injection via a service locator).

---

## STEP 4 — Specs (~45 seconds)

```
> STEP 4: dispatching spec-writer (specs)...
> ✓ docs/specs/00-overview.md
> STEP 4 complete.
```

---

## STEP 5 — ADRs (~90 seconds)

The `adr-writer` agent (Opus, high effort) identifies significant architectural decisions evident in the code and writes 3–5 MADR-format decision records.

```
> STEP 5: dispatching adr-writer...
> ✓ docs/architecture/decisions/0001-repository-pattern-for-data-access.md
> ✓ docs/architecture/decisions/0002-express-middleware-chain-for-auth.md
> ✓ docs/architecture/decisions/0003-postgresql-as-primary-datastore.md
> STEP 5 complete.
```

Each ADR has a Title, Status (Accepted), Context and Problem Statement, Considered Options, Decision Outcome, and Consequences — all grounded in code evidence.

---

## STEP 6 — Audit (~90 seconds)

The `spec-auditor` agent (Opus, high effort) reads every generated file and checks claims against the real code.

```
> STEP 6: dispatching spec-auditor...
> ✓ Audit complete.
```

The audit surfaces a prioritized correction list:

```
## Corrections

### High

1. docs/architecture/integrations.md — Redis is listed as a cache integration but no
   Redis client library is present in package.json and no redis configuration exists
   in .env.example. Remove or mark as planned.

### Medium

2. docs/conventions/coding.md — States "all controllers extend BaseController" but
   src/controllers/health.controller.js does not extend it. Either update the convention
   or note the exception.

3. docs/architecture/overview.md — Background section mentions "microservices"
   but the codebase is a single Express app with no service mesh. Replace with
   "modular monolith" to match the actual structure.

### Low

4. docs/architecture/decisions/0002 — The ADR says auth uses JWT but the middleware
   at src/middleware/auth.js also handles session cookies as a fallback. Worth noting
   as a consequence.
```

---

## STEP 7 — Apply corrections

The orchestrator surfaces the correction list and pauses:

```
> 4 corrections found (1 High, 2 Medium, 1 Low).
> High and Medium issues will be applied. Review the list above.
> Proceed? (y/n)
```

The engineer types `y`.

```
> Applying High corrections...
> ✓ docs/architecture/integrations.md — Redis section removed.
> Applying Medium corrections...
> ✓ docs/conventions/coding.md — BaseController exception noted.
> ✓ docs/architecture/overview.md — "microservices" replaced with "modular monolith".
> Low corrections surfaced for awareness — not applied automatically.
> STEP 7 complete.
```

---

## STEP 8 — Finalize CLAUDE.md

```
> STEP 8: writing CLAUDE.md...
> ✓ CLAUDE.md written.
```

The generated `CLAUDE.md` section looks like:

```markdown
## Architecture
- Read docs/architecture/overview.md before making structural or architectural changes
- Read docs/architecture/components.md and docs/architecture/integrations.md
  when working in unfamiliar areas

## Conventions
- Read the relevant convention files before generating or modifying code
- Treat convention documents as project rules unless the user explicitly overrides them

## ADR Workflow
- ADRs live in docs/architecture/decisions/
- Before any architectural decision, read all existing ADRs
- Name ADR files: NNNN-short-title-in-kebab-case.md
- Use MADR format
```

---

## Run summary

```
> Run complete.
> Summary written to docs/summary/latest-run.md
>
> Files created: 12
>   docs/architecture/overview.md
>   docs/architecture/components.md
>   docs/architecture/integrations.md
>   docs/reference/api.md
>   docs/conventions/coding.md
>   docs/conventions/testing.md
>   docs/conventions/naming.md
>   docs/specs/00-overview.md
>   docs/architecture/decisions/0001-*.md
>   docs/architecture/decisions/0002-*.md
>   docs/architecture/decisions/0003-*.md
>   CLAUDE.md
>
> Total wall-clock time: ~8 minutes
```

The engineer commits the output:

```bash
git add docs/ CLAUDE.md
git commit -m "docs: initial knowledge base"
```

---

## Re-running after a code change

Two weeks later, the team adds a Redis cache layer and refactors the auth middleware. The engineer runs:

```
/generate-knowledge-base docs mode=light
```

STEP 0.4 diffs against the last docs commit and detects changes in `src/middleware/` and the addition of a `redis` dependency in `package.json`. Only the affected steps re-run:

```
> STEP 0.4: changed files since last docs commit:
>   src/middleware/auth.js
>   src/services/cache.service.js
>   package.json
> Steps to re-run: STEP 1, STEP 2, STEP 3
> Skipping: STEP 4 (specs unchanged), STEP 8 (CLAUDE.md current)
```

The integrations doc is updated to include Redis. The auth convention is corrected. The run takes ~3 minutes instead of 8.

---

## What this walkthrough doesn't show

- **`mode=force`** — use when docs have drifted from git and STEP 0.4 scoping produces a false "nothing changed" result.
- **Legacy doc migration** — if you had an older `docs/` structure before the current taxonomy, STEPS 0.5 and 0.6 handle migrating content into the canonical paths.
- **`mode=light` first run** — valid for smaller projects where you want architecture/conventions/specs but don't need ADRs or an audit pass immediately. You can always follow up with `mode=full`.
- **Custom output root** — `/generate-knowledge-base apps/api/docs` scopes the entire run to a subdirectory, useful for monorepos.
