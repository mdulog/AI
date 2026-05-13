# API Reference

Not applicable — this skill exposes no programmatic, HTTP, or RPC API.

The only entry point is the Claude Code custom slash command `/generate-knowledge-base`, documented in [`../specs/00-overview.md` § Public Surface](../specs/00-overview.md#public-surface).

For the explicit list of integrations that this project does NOT have (databases, queues, schedulers, auth providers, third-party SaaS, etc.), see [`../architecture/integrations.md` § Things This Project Does Not Integrate With](../architecture/integrations.md#things-this-project-does-not-integrate-with).

This file exists so the `docs/reference/` folder is tracked by git and so a reader who lands here directly via filesystem navigation gets a pointer rather than an empty file. The orchestrator's STEP 2 (architecture docs) intentionally does not regenerate this file because the project has no APIs to document; if APIs are added later, `spec-writer` will populate this file on the next run per the rule in `generate-knowledge-base/Agents/spec-writer.md`.

## Assumptions

- This file remains a stub until the project gains an API surface. If `spec-writer` overwrites it on a future run, that's the expected behavior.
