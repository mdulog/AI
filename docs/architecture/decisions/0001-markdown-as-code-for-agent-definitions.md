# 0001. Markdown as Code for Agent Definitions

Date: 2026-05-07

## Status

Accepted

## Context and Problem Statement

The system needs a format for defining the orchestrator and its six subagents. Each agent requires a declared identity (name, description), a set of permitted tools, an optional model selection, and detailed behavioral instructions. The format must be interpretable by the Claude Code runtime, which discovers commands in `.claude/commands/` and agents in `.claude/agents/`.

## Considered Options

- Markdown files with YAML frontmatter and natural language prompt bodies
- Programmatic agent definitions in a general-purpose language (TypeScript, Python)
- Declarative configuration files (YAML or JSON) with separate prompt templates

## Decision Outcome

Chosen option: **Markdown files with YAML frontmatter and natural language prompt bodies**, because the Claude Code runtime natively interprets this format for commands and agents, eliminating the need for a build step, runtime framework, or custom loader.

Each agent is a single `.md` file. The YAML frontmatter declares structured metadata (`name`, `description`, `tools` or `allowed-tools`, and `model`). The markdown body contains the full behavioral specification as natural language prompts. The orchestrator uses `allowed-tools: [Read, Write, Bash, Agent]` and `model: sonnet` in its frontmatter (per the no-version-pins rule codified in ADR 0006). Subagents use the `tools` key (e.g., `tools: [Read, Bash, Glob, Grep, Skill]`) and each declares a generic model alias.

This approach means the entire system -- orchestrator logic, agent definitions, tool permissions, and behavioral instructions -- is expressed as seven markdown files with no compiled code.

### Consequences

- Good: Zero build step, zero runtime dependencies beyond Claude Code. Agents are human-readable and editable by anyone familiar with markdown. Deployment is a file copy (`cp generate-knowledge-base/Agents/*.md .claude/agents/`).
- Good: Tool permissions are declaratively scoped per agent in frontmatter, enforced by the Claude Code runtime rather than application-level guards.
- Bad: No static analysis, type checking, or compile-time validation of agent behavior. Errors in prompt instructions are only caught at runtime.
- Bad: The behavioral contract between orchestrator and subagent is expressed in natural language, making it possible for instructions to drift or conflict without automated detection.
