# Testing Conventions

## Overview

This repository contains two skills with different testing postures.

**`generate-knowledge-base`** has no automated test suite. It is a pure-markdown Claude Code skill — YAML frontmatter and structured prompt definitions. Quality assurance is achieved through three mechanisms: **the in-workflow audit** (STEP 6 + STEP 7), **the LLM-judge smoke grader** (`scripts/smoke_grade.py`), and **dogfooding plus manual review**. None of these is a substitute for an automated test suite — they are what this skill actually has.

**`generate-prd`** ships a 94-test static pytest suite (`generate-prd/tests/`) that runs with no API key required. See [`generate-prd` Testing](#generate-prd-testing) below.

## Validation Mechanisms

### Required: In-Workflow Audit (STEP 6 + STEP 7)

The `spec-auditor` subagent is the project's primary validation mechanism. In `mode=full`, it reviews every generated document against the real codebase and produces a prioritized correction list.

For each file under `OUTPUT_ROOT/architecture/`, `conventions/`, `specs/`, `reference/`, and `architecture/decisions/`, the auditor checks:

1. Contradictions with the real code.
2. Assumptions that cannot be verified.
3. Missing information that should be present.
4. Sections that are vague or overly generic.
5. Content that belongs in a different doc category.

Issues are categorized as **High**, **Medium**, or **Low** priority. The auditor never modifies files — its tool set is `[Read, Bash, Glob, Grep, Skill]` (no `Write`), and the harness denies any write attempt at the tool level. `Skill` enables optional Superpowers skill invocation but cannot bypass the missing `Write` grant.

### Required: Human-in-the-Loop Correction (STEP 7)

After the audit, the orchestrator presents all High and Medium priority corrections to the user for review. **No corrections are applied until the user explicitly confirms which ones to proceed with.** This is the only step in the workflow that gates on user approval before modifying files. STEP 7 is intentionally orchestrator-direct — there is no separate "corrections-writer" agent.

`mode=light` skips both STEP 6 and STEP 7, so light-mode runs receive **no automated validation** beyond manual review of the output.

### Observed: LLM-Judge Smoke Grader (`scripts/smoke_grade.py`)

The repository ships an ad-hoc LLM-judge regression grader at `scripts/smoke_grade.py` (283 lines). It is **dev tooling**, not part of the deployable skill surface, and is not invoked at runtime by the orchestrator or any agent.

What it does:

- Compares two versions of a generated artifact produced under different `model + effort` combinations (see the script's module docstring).
- Submits both versions to a judge model (the `JUDGE_MODEL` constant, currently `"claude-opus-4-7"`) for blind grading.
- Returns a structured Pydantic-validated grading result.

Constraints to respect:

- The judge model is **pinned to a specific version** (`claude-opus-4-7`). This is an intentional deviation from the project's "generic aliases only" policy because reproducible grade comparisons require a stable judge. See `coding.md` § Generic Aliases Only — No Version Pins for the open question (formal carve-out vs. switch to alias).
- The script is not referenced anywhere else in the repository — no README mention, no `CLAUDE.md` entry, hardcoded artifact paths. Treat it as a personal-use tool until that documentation gap is closed.

### Observed: Dogfooding (Self-Hosting)

The repository's own `docs/` tree is the prior run's output of the skill applied to itself. Re-running `/generate-knowledge-base` against this repo serves as an end-to-end smoke test:

- If the skill cannot regenerate consistent docs over its own source, that is a regression signal.
- The audit step (when `mode=full`) provides automatic feedback during dogfooding.

This is the closest thing the project has to integration testing, and it is informal — there is no recorded baseline to diff against.

## Manual Validation Procedures

### Recommended: Deploy-and-Run for Prompt Changes

When modifying agent prompt files, validate changes by deploying the modified files into a real target project and exercising the affected step:

1. **Deploy** modified files using the standard `cp` invocation:
   ```bash
   cp generate-knowledge-base/generate-knowledge-base.md /path/to/target/.claude/commands/
   cp generate-knowledge-base/Agents/*.md /path/to/target/.claude/agents/
   ```
2. **Exercise the relevant step** by running `/generate-knowledge-base` in the target project. Use `mode=light` for quick feedback on STEPS 1–4 and 8; use `mode=full` to also test STEPS 0.5, 0.6, 5, 6, and 7.
3. **Test scenario pairs** that exercise distinct code paths in the orchestrator:
   - First run (empty `docs/`) vs. re-run (populated `docs/`) — verifies incremental update behavior.
   - With `git` available vs. without — verifies degraded-mode behavior in STEP 0.4 and STEP 0.5.
   - `mode=full` vs. `mode=light` vs. `mode=force` — verifies step-skipping logic and git-diff bypass.
4. **Observable outputs per agent** (use these as informal acceptance criteria):
   - `spec-brainstormer`: returns a structured report in conversation context; creates no files.
   - `spec-writer`: creates or updates markdown files under `docs/architecture/`, `docs/specs/`, and (conditionally) `docs/reference/api.md`.
   - `conventions-writer`: creates or updates markdown files under `docs/conventions/`.
   - `adr-writer`: creates numbered MADR files under `docs/architecture/decisions/`.
   - `spec-auditor`: returns a prioritized issue list in conversation context; creates no files.
   - `legacy-doc-consolidator`: updates canonical docs, returns a consolidation report, preserves all legacy files.

### Recommended: Audit Re-Run After Edits

After any non-trivial edit to the orchestrator or an agent, run the workflow in `mode=full` against a real project and read the audit output. The audit's High/Medium list is the most concrete acceptance signal available.

## Why No Automated Tests

The "code" in this project is natural-language prompts interpreted by an LLM at runtime. Traditional unit and integration tests do not apply because:

- There are no functions to call or return values to assert against.
- Prompt behavior is non-deterministic at the LLM level.
- The output is prose (markdown documents), not structured data with fixed schemas.

The `spec-auditor` agent is the project's functional equivalent of a test suite — it performs evidence-based validation of generated output against the source-of-truth code. The smoke grader complements this with a grade-comparison harness for prompt-engineering experiments, but neither produces a pass/fail signal in the conventional CI sense.

## What is Explicitly *Not* a Convention for `generate-knowledge-base`

The `generate-knowledge-base` skill contains none of the following — do not infer their existence:

- No `tests/`, `test/`, `__tests__/`, `spec/`, or `Tests/` directory.
- No `*.test.*`, `*.spec.*`, `_test.go`, `*Tests.cs`, or equivalent files.
- No fixtures, factories, mocks, or stubs.
- No coverage thresholds, no lint config that gates CI.

If `generate-knowledge-base` later grows code (e.g. a CLI wrapper), a conventional test suite must be introduced at that point.

---

## `generate-prd` Testing

`generate-prd` ships a static pytest suite under `generate-prd/tests/`. All 94 tests run with no API key or network access required — they are structural assertions against prompt files, schema files, and fixture JSON.

### Layout

```
generate-prd/tests/
  validators/          # Per-prompt and per-schema static tests (9 files)
  e2e/                 # Deployment smoke test — orchestrator + agents + golden corpus shape
  durability/          # Checkpoint ordering, state fixtures, stuck-loop, schema migration
  golden-corpus/       # 5 synthetic transcripts + glossary + expected themes + critic fixtures
  fixtures/            # State JSON fixtures (valid and invalid) for schema tests
```

### Running the suite

```bash
cd /path/to/repo
source .venv/bin/activate   # requires: pip install -r generate-prd/requirements-dev.txt
pytest generate-prd/tests/  # expect 94 tests, 0 failures, no API calls
```

### What the tests cover

| Layer | Files | What is checked |
|---|---|---|
| Prompt contracts | `tests/validators/test_*.py` | Required template variables, output format specs, forbidden phrases, no-closure clause, finding-type vocabulary distinctness |
| Schema validity | `tests/validators/test_state_schema.py`, `test_prd_template.py` | JSON Schema validates, PRD template has 9 sections with italic intent lines |
| Deployment shape | `tests/e2e/test_deployment_smoke.py` | All 6 agents have valid frontmatter, orchestrator references all 6 agents, all 7 prompts exist |
| Durability | `tests/durability/test_*.py` | Checkpoint-before-API-call ordering, state fixtures validate against schema, stuck-loop detection, schema migration contract |
| Fixtures | `tests/golden-corpus/critic-fixtures/` | 8 planted-flaw drafts (one per finding type + one clean baseline) with declared expected findings |

### What the tests do NOT cover

- Behavioral correctness of the critic, drafter, or any other agent — that requires live model calls. The holistic critic accuracy playbook at `tests/durability/test_critic_holistic.md` is the gate for behavioral validation.
- Live API calls — `tests/validators/run_prompt.py` exists as a harness but is never invoked by pytest.

## Assumptions

- The `spec-auditor` agent's effectiveness depends on the underlying model and the specificity of its audit prompts. There is no metric for audit coverage or run-to-run consistency.
- `scripts/smoke_grade.py` is a one-off dev tool maintained at the author's discretion; nothing in the deployable skill surface depends on it. If it is removed, the testing story degrades to "audit + dogfooding + manual review" only.
- `mode=light` skips the audit entirely. Light-mode runs have no automated validation beyond a human reading the output — this is by design (speed over rigor) and is not a defect.
- The hardcoded `JUDGE_MODEL = "claude-opus-4-7"` in `smoke_grade.py` is treated as a deliberate exception to the project's no-version-pin rule; the policy carve-out is unresolved.
