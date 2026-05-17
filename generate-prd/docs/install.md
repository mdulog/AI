# Install & troubleshooting — generate-prd

This is the detailed deployment guide. The 30-second version is in the [README](../README.md#install). Use this doc if you have a non-default project layout, want to verify the install, or hit something unexpected.

---

## What you're installing

The skill is two file groups plus zero runtime dependencies:

```
generate-prd/
├── generate-prd.md          # The orchestrator skill (→ .claude/commands/)
├── Agents/
│   ├── transcript-normalizer.md
│   ├── transcript-distiller.md
│   ├── theme-clusterer.md
│   ├── prd-drafter.md
│   ├── prd-critic.md
│   └── prd-finalizer.md     # All 6 → .claude/agents/
├── prompts/                 # 7 markdown prompts; read at runtime by the agents (NOT deployed)
├── schema/                  # State schema, PRD template, transcript format spec
└── tests/                   # Phase 1-4 test suite + golden corpus
```

The orchestrator and the 6 agents are the only files Claude Code needs to know about. The prompts, schemas, and tests live in the source repo and are read at runtime via relative paths from the agents.

---

## Standard install

In the target project root (where you'll keep `transcripts/` and `prd/`):

```bash
mkdir -p .claude/commands .claude/agents
cp /path/to/generate-prd/generate-prd.md .claude/commands/
cp /path/to/generate-prd/Agents/*.md .claude/agents/
```

Verify the file count:

```bash
ls .claude/commands/   # expect: generate-prd.md
ls .claude/agents/     # expect: 6 .md files
```

Restart Claude Code (or reload skills/agents) so the new files are picked up.

---

## Verify the install (sanity check)

Run this in a workspace that has NO transcripts yet:

```
/generate-prd
```

**Expected:** The orchestrator's STEP 0 checks for a transcripts directory, doesn't find one (or finds it empty), and bails out with a clear error pointing at the expected path. If you see this error, the skill is wired up correctly — Claude Code found the command, loaded all 6 agents, and is enforcing the input contract.

If instead you see "Unknown command: /generate-prd", the orchestrator file isn't in `.claude/commands/` or has the wrong name. Re-check the `cp` step.

If you see "Missing required agents: ...", the agent files aren't in `.claude/agents/`. The orchestrator names exactly the 6 it requires.

---

## Non-default project layouts

The skill assumes:
- Transcripts at `./transcripts/`
- Output PRD at `./prd/<feature_name>.md`
- State at `./prd/.state.json`

If you need a different transcripts directory, pass it via `$ARGUMENTS` to the skill (this is supported by the harness; the orchestrator picks it up in STEP 0). The PRD output path is derived from `feature_name` and is harder to relocate — if you genuinely need to, the cleanest move is to run the skill from inside a sub-directory of your project so the relative `prd/` is where you want it.

---

## Glossary file (optional)

If your transcripts contain consistent transcription errors (`Looper` instead of `Loopr`, `Sales Force` instead of `Salesforce`, etc.), drop a `glossary.md` at the project root. Format:

```markdown
# Glossary

# Lines starting with # are comments.
# Format: <original>: <canonical>
# Case-insensitive matching.

Looper: Loopr
Sales Force: Salesforce
```

Glossary substitutions are applied **deterministically by Python regex** before the normalizer's LLM call — they're not done by the model. This means glossary fixes are predictable and free.

Example: [`schema/glossary.md.example`](../schema/glossary.md.example).

---

## Custom PRD template (optional)

The default template lives at [`schema/prd-template.md`](../schema/prd-template.md). It has 9 sections, each with an italic intent line. The drafter and critic both read these intent lines as a contract.

To override, drop a `prd-template.md` at the project root. **Constraints:**

- Each section heading must be `## <Name>` (h2).
- Each section must have an italic intent line on the second line after the heading: `*<intent>*`.
- The skill maps known section names to the evidence-anchored / PM-judgment split documented in spec § 7.5. Unknown section names default to PM-driven in the loop.

If you replace the template, your PRD will follow your section names, but the critic still pivots on the spec's 7 finding types — those are template-agnostic.

---

## Troubleshooting

### "Found an unfinished discovery session" — but I never ran the skill before

The orchestrator found a `prd/.state.json` file. If you didn't create it, something else did — possibly an earlier interrupted run, or a stale file copied from another project. Inspect `prd/.state.json` and either resume (if it's yours), archive (if you want a clean slate), or delete the file entirely (if it's stale).

### Agents are "missing" but the files exist

Most often: the agent files are in the wrong directory (`agents/` vs `.claude/agents/`), or Claude Code hasn't picked up new agent files. Try restarting Claude Code. As a last resort, `/reload-plugins` or whatever your harness uses.

### The normalizer is rejecting my transcripts

The normalizer accepts `.vtt`, `.srt`, `.md`, and `.txt`. If you have `.docx`, convert it to markdown or plain text first — the normalizer is built to handle Word *paste* (markdown that came from Word) but not the binary `.docx` format.

### The critic isn't catching obvious issues

Run the holistic playbook at [`tests/durability/test_critic_holistic.md`](../tests/durability/test_critic_holistic.md) on the golden corpus. If the critic does worse than the acceptance thresholds there, that's a critic-prompt issue, not your transcripts. Iterating on `prompts/critic-pass.md` is the fix; re-run all of `pytest generate-prd/tests/` after to catch regressions in the static contract checks.

### The skill seems "stuck" — every iteration returns the same findings

This is the stuck-loop fault. After 5 byte-identical critic outputs in a row, the orchestrator writes `status: faulted` and surfaces three choices. If you keep `/skip`-ing the same finding instead of engaging it, that's the most common cause.

### Where's the cost?

`/status` returns a `cost_estimate_usd` field. It's a rough estimate based on cumulative token counts and known model rates. Treat it as informational, not as a process budget — the skill never uses it to decide anything.

---

## Updating the skill

When a new version of `generate-prd` ships, re-run the install:

```bash
cp /path/to/generate-prd/generate-prd.md .claude/commands/
cp /path/to/generate-prd/Agents/*.md .claude/agents/
```

If the schema version bumped (e.g. v1 → v2), the orchestrator's STEP 0 will detect a version mismatch on your existing `prd/.state.json`, look for a migration script at `generate-prd/schema/migrations/v<from>-to-v<to>.py`, and run it before continuing. See [`schema/migrations/README.md`](../schema/migrations/README.md) for the contract.

---

## What ISN'T installed

- The `prompts/`, `schema/`, and `tests/` directories stay in the source repo. The agents reference them via relative paths.
- No Python runtime is required for the skill itself. Python is only needed to run the test suite during development (`pytest generate-prd/tests/`).
- No API key is required for the skill's static tests. A `$ANTHROPIC_API_KEY` is required only if you opt into live validation via the test harness at `tests/validators/run_prompt.py`.

---

## Uninstall

```bash
rm .claude/commands/generate-prd.md
rm .claude/agents/transcript-normalizer.md .claude/agents/transcript-distiller.md \
   .claude/agents/theme-clusterer.md .claude/agents/prd-drafter.md \
   .claude/agents/prd-critic.md .claude/agents/prd-finalizer.md
```

Your `prd/` directory, transcripts, and any work-in-progress state files are untouched. Delete those manually if you want a full clean.
