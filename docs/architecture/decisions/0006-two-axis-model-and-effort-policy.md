# 0006. Two-Axis Model and Effort Policy for Token Hygiene

Date: 2026-05-08

## Status

Accepted

## Context and Problem Statement

The skill dispatches an orchestrator and six subagents through a 12-step pipeline. Each dispatch consumes tokens, and the cost/quality trade-off is not uniform across steps: a brainstorm pass that feeds every downstream writer compounds in value if higher-quality, while procedural orchestration and structured generation from a clear input are well-served by a smaller model. The system needed a single, declarative policy for choosing both **which model** runs each agent and **how hard** that model thinks per dispatch — without scattering version pins through the codebase or re-deciding per invocation.

The decision is constrained by four realities:

- The Claude Code harness exposes both a `model:` field in agent/command frontmatter and a `/effort <level>` slash command for per-dispatch reasoning depth.
- Generic aliases (`opus`, `sonnet`, `haiku`, `inherit`) resolve at the harness level to the latest matching model; pinned versions (e.g. `claude-opus-4-6`) silently miss future improvements.
- Only three subagents — `spec-brainstormer`, `adr-writer`, `spec-auditor` — perform open-ended judgment that compounds across the rest of the pipeline. The remaining four agents perform structured generation from an already-distilled input.
- The orchestrator must remain on a low-cost, fast model because it does no analytical work itself; it sequences steps and dispatches subagents.

## Considered Options

- **Single-model defaults**: pick one model (e.g. Sonnet) for everything and ignore reasoning-effort knobs.
- **Per-step model overrides on `Agent` invocations**: let the orchestrator override `model:` per dispatch, alongside `/effort`.
- **Two-axis declarative policy**: model declared once in each agent's frontmatter (the per-agent SoT), effort set per dispatch by the orchestrator via `/effort` (the per-step SoT). Generic aliases only; no version pins.
- **Pinned versions everywhere**: hardcode specific model versions (e.g. `claude-opus-4-6`) to guarantee reproducibility.

## Decision Outcome

Chosen option: **Two-axis declarative policy with two distinct sources of truth**, because it isolates the two orthogonal choices (which model, how hard it thinks) and prevents drift by giving each axis exactly one place to live.

The policy, defined in `CLAUDE.md` § Model and Effort Policy and the orchestrator's § Model and effort policy:

| Agent | Model | Effort | Rationale |
|---|---|---|---|
| (orchestrator) | `sonnet` | `medium` | Procedural coordination, git-diff scoping, dispatch. |
| `spec-brainstormer` | `opus` | `high` | Output feeds every downstream writer; quality compounds. |
| `spec-writer` | `sonnet` | `medium` | Structured generation from a clear report. |
| `conventions-writer` | `sonnet` | `medium` | Bounded judgment with brainstorm in hand. |
| `legacy-doc-consolidator` | `sonnet` | `medium` | Editorial categorization with explicit rules. |
| `adr-writer` | `opus` | `high` | Deduplication and significance judgment; collisions are costly. |
| `spec-auditor` | `opus` | `high` | Contradiction detection gates the corrections step. |

Mechanics:

- **Model SoT** = each agent's frontmatter `model:` field. Verified across all seven files (orchestrator + six agents); each declares a generic alias only.
- **Effort SoT** = the orchestrator's `/effort <level>` calls, dispatched immediately before the matching `Agent` invocation. Default is `medium`; the orchestrator escalates to `high` before STEP 1 (`spec-brainstormer`), STEP 5 (`adr-writer`), and STEP 6 (`spec-auditor`), reverting to `medium` afterward (orchestrator § STEP 1, § STEP 5, § STEP 6).
- **No per-step `model` overrides on `Agent` invocations** — model selection lives in one place.
- **Generic aliases only** — `CLAUDE.md` § Model and Effort Policy: "Never pin a specific version (e.g. `claude-opus-4-6`) — pins miss model improvements."
- **Graceful degradation** — if `/effort` is unavailable in the harness, the orchestrator continues as if the requested level were applied.

The escalation ladder (Sonnet+medium → Sonnet+high → Opus+high → Opus+max) means the cheapest knob is tried first. In the current pipeline no step needs Opus+max or Haiku+low; those rungs exist for future expansion without re-architecting the policy.

### Consequences

- Good: A reader can answer "what model does X run on?" by reading X's frontmatter, and "how hard does X think?" by grepping the orchestrator for `/effort` calls around X. The two questions never collide.
- Good: Generic aliases mean model upgrades roll out automatically when the harness updates its alias resolution. The skill never has to ship a "bump model version" commit.
- Good: Token spend is right-sized per agent. Sonnet/medium covers four agents and the orchestrator; Opus/high is reserved for the three agents whose output quality compounds across downstream steps.
- Good: The two-axis ladder makes future tuning low-friction — escalating effort is one orchestrator edit; promoting an agent's model is one frontmatter edit. Neither requires touching dispatch sites.
- Bad: The policy is enforced only by reviewer discipline. Nothing prevents a future contributor from adding a `model:` override on an `Agent` invocation, pinning a version in frontmatter, or forgetting to revert `/effort` after escalation. CI does not verify the table.
- Bad: The orchestrator must remember to revert `/effort` after each escalation. A missed revert silently raises cost on subsequent steps with no error signal.
- Bad: Generic aliases sacrifice exact reproducibility. Two runs separated by a model upgrade can produce different outputs from identical inputs. Accepted because reproducibility was deemed less valuable than benefiting from model improvements without code changes.
- Neutral: `scripts/smoke_grade.py` pins a specific model ID (`JUDGE_MODEL = "claude-opus-4-7"`). This is the codified dev-tooling exception (see `CLAUDE.md` § Model and Effort Policy and the carve-out comment at the top of the script): the Anthropic SDK does not resolve generic aliases, so dev tooling that calls the SDK directly must use exact model IDs. Bump the pin on model launches.

## Assumptions

- The Claude Code harness resolves generic aliases (`opus`, `sonnet`, `haiku`, `inherit`) to the latest matching model at dispatch time, and the skill never observes the resolved version.
- The compounding-quality argument for Opus on `spec-brainstormer`, `adr-writer`, and `spec-auditor` is qualitative — no benchmark in this repo measures the marginal output quality of Opus vs Sonnet for these specific tasks.
- `/effort` is a stable harness primitive; if it is renamed or removed, the policy degrades to "model-only" without a replacement effort axis.
- A future agent added without a `model:` field will inherit the orchestrator's `sonnet` — treated as a safe default rather than a misconfiguration.
