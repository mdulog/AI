# Global Claude Code Preferences

Shared, tool-agnostic preferences live in `AGENTS.md` (loaded via the import below). This file adds Claude Code-specific rules.

@AGENTS.md

---

## 🤖 Claude Code Workflow Preferences

### 🗂️ Memory

- Don't save PR lists or activity summaries; ask what was surprising or non-obvious and save that instead.

### 📁 Project-Level Overrides

- Project-specific context belongs in `./CLAUDE.md` or `./CLAUDE.local.md` at the repo root
- Reserve the global files for universal preferences: tool-agnostic rules go in `AGENTS.md`, Claude Code-specific rules here. Avoid adding project-specific rules to either
- For per-machine overrides (local tool paths, machine-specific config) add a file under `~/.claude/rules/` (e.g. `~/.claude/rules/local.md`) — it's loaded like this file but not shared across machines

### ⚡ Skills (Superpowers)

- A **superpowers skill system** is active — check for an applicable skill before ANY response, including clarifying questions
- Skills override default behavior but are subordinate to explicit user instructions
- Use the `Skill` tool to invoke skills; never rationalize skipping one if there's even a 1% chance it applies
- Check the full skill registry via the Skill tool — never assume a skill doesn't exist because it's not listed here
- Skill categories include: workflow (brainstorming → planning → execution), debugging, TDD, code review, git isolation, parallel agents, and task completion — always check the live registry rather than relying on any remembered list

### 📐 When to Use Plan Mode

- Before any multi-file refactor or new feature spanning more than 2 files
- When requirements are ambiguous — clarify and align before touching code
- For infrastructure changes: CI/CD, migrations, dependency upgrades
- Always check SOLID and Security sections during plan phase before writing a line of code
- Whenever `superpowers:brainstorming` is invoked, call `EnterPlanMode` immediately, before the first question. Brainstorming's own approval gate stays in force regardless; Plan Mode is a harness-level backstop on top of it, not a substitute.
- Plan mode is the autonomy axis the Advisor stance in `AGENTS.md` defers to: the stance shapes what a reply says, while auto vs. plan mode decides whether I act without asking.
- Once the design is approved and implementation starts, call `ExitPlanMode`. This returns to the prior permission mode (normally `auto`).

### ✅ Verification Gate

- Commit Cadence in `AGENTS.md` defines a quick local "green" check (build, typecheck, that step's tests) for per-step commits. That check is not this gate.
- In Claude Code, the formal gate that runs when work is claimed complete is `superpowers:verification-before-completion`. Per-step commits don't trigger it.

### 🔄 Development Workflow (Ouroboros → Superpowers)

A full pipeline run belongs to the `development-workflow` skill (`~/.claude/skills/development-workflow/SKILL.md`). It's opt-in — invoke it explicitly for a full run on a piece of engineering work. It owns everything from classification to the push gate (pushing stays manual), including model routing, plan-mode entry and exit, and the pre-push doc-sync check.

Outside an explicit invocation, ordinary work relies on the auto-triggering superpowers skills plus 📐 Plan Mode above and ⏹️ Stop and Ask, 🔁 Commit Cadence and 🛠️ Language & Stack Defaults in `AGENTS.md`. The pre-push doc-sync check isn't enforced there.

### 🕵️ Auditing Generated Instructional Documents

- Applies to any file whose purpose is to tell a human or agent what to do: runbooks, checklists, ADRs, deployment/setup guides, CLAUDE.md/AGENTS.md edits, skill files, and any plan or spec written to a file. Does not apply to ordinary code, comments, one-off chat responses, or a plan that exists only in the conversation. Exception: inside a `development-workflow` run, the skill's design and plan audit (mode C, in `~/.claude/skills/development-workflow/references/reviewer-brief.md`) audits that run's `design.md` and `plan.md` instead.
- Before presenting the document as final, launch a separate `spec-auditor` agent to audit it against the current codebase and system state — verify referenced file paths, commands, function/service names, and factual claims are still accurate, not stale or hallucinated.
- The audit agent reports findings back; it does not edit the file itself. I decide which findings to act on.
- This runs in addition to the verification and doc-sync steps of any pipeline run (see 🔄 Development Workflow).


---

## 🔀 PR & Code Review Preferences (Claude Code additions)

Blocking criteria, review findings format, and commit/PR message rules are in `AGENTS.md`.

### 👁️ Code Review Stance — additions

- When reviewing: run all relevant code review plugins before approving (see plugin invocations below)
- When receiving: if feedback is unclear or technically questionable, invoke `superpowers:receiving-code-review` before implementing — don't perform agreement

### 🔌 Code Review Plugin Invocations

- **Reviewing someone else's PR**: I run `/code-review:code-review` myself — don't substitute `/pr-review-toolkit:review-pr`, which ends with `code-simplifier` and can edit the reviewed code
- **Verifying my own implementation (full review)**: invoke `/pr-review-toolkit:review-pr`, never with `all` or `simplify` — `code-simplifier` would edit code after tests and QA have run
- **Security**: `security-guidance` runs automatically via hooks — nothing to invoke; address its findings before finishing
- **After writing/modifying code (spot-check)**: spawn `pr-review-toolkit:code-reviewer`
- **When PR touches tests or adds features**: spawn `pr-review-toolkit:pr-test-analyzer`
- **When new types are introduced**: spawn `pr-review-toolkit:type-design-analyzer`
- **When error handling or catch blocks are modified**: spawn `pr-review-toolkit:silent-failure-hunter`
- **After generating large doc comments**: spawn `pr-review-toolkit:comment-analyzer`
- **After writing or modifying a logical chunk of code**: spawn `pr-review-toolkit:code-simplifier` (not the same-named agent from the `code-simplifier` plugin) alongside `pr-review-toolkit:code-reviewer` above for a dedicated smell/simplification pass — narrower than code-reviewer's own duplication/naming checks, and different in kind from every other agent on this list since it **applies** edits directly instead of reporting findings for me to decide on. Its React patterns and style opinions (function declarations, import extensions, explicit return types) may conflict with the project's framework, ESLint config or tsconfig — confirm which case applies before accepting its edits
- For reviewing code, use the `pr-review-toolkit` variants above. `superpowers:requesting-code-review` orchestrates a review and `superpowers:receiving-code-review` covers handling feedback; the `pr-review-toolkit` agents do the checks themselves.
- Inside a `development-workflow` run the per-chunk spot-checks above don't run. The skill's reviews replace them (SDD's per-task and final reviews where SDD runs, and the Phase 4 branch review whenever SDD's final review wasn't clean or SDD didn't run, always after a repair loop), and `code-simplifier` never runs, because it would edit code after it was tested and reviewed.
