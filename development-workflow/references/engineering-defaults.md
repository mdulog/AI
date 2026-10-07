# Engineering defaults: Context7 lookups and stack defaults

Loaded from `SKILL.md` (Phase 1 when the human asks about the stack, Phase 2 design, and Phase 3 implementation when a library or stack decision comes up). Section names below refer to sections of `SKILL.md`. Most text is moved verbatim from there; the stack section below is expanded from the summary in `SKILL.md`. The rules in `SKILL.md` still apply.

## Documentation lookups (Context7)

- Always use Context7 (`resolve-library-id`, then `query-docs`; find the tools
  with ToolSearch `context7`, since their prefix varies by install) during Phase 2
  design or Phase 3 implementation when a library, framework, SDK, API, or
  CLI tool is involved — even well-known ones. Never rely on trained
  knowledge alone; training data may not reflect recent API changes,
  version migrations, or deprecations.
- Use for: API syntax, configuration options, version migration guides,
  setup instructions, CLI usage, library-specific debugging. Not needed for:
  general programming concepts, refactoring, business logic, or code review.

## Language & stack defaults

- Primary language: TypeScript (strict mode, latest stable version) for
  new/greenfield work in Phase 3, unless the target project specifies
  otherwise. No default framework: pick the lightest one the design
  justifies and say why in the plan.
- Frontend: no default. Check the repo first (`package.json`, existing
  components) and match whatever's already there. Ask which framework only
  when there is nothing to match.
- Default test framework: Vitest for new/greenfield work. Integration tests
  run against real instances (e.g. Testcontainers) rather than mocks;
  Testcontainers needs a Docker-compatible runtime, so keep integration tests
  in a separate Vitest project. An existing project's tests follow whatever
  test convention that project already uses, not this default.
- For greenfield TypeScript, the plan includes a task that sets up ESLint with
  typed linting and `@typescript-eslint/no-floating-promises` (`ignoreVoid:
  false`). `tsc` doesn't catch a floating promise, and once the project defines
  a lint command, Phases 3 and 4 gate on it.
- These are defaults for new/greenfield work only — always defer to what the
  target project's own conventions or existing codebase specifies. If the
  human's own instructions (their `CLAUDE.md`) name a different stack than
  the above, say so during Phase 2 and ask; don't silently pick one. This
  section copies the human's global defaults so the skill stays
  self-contained, which means it drifts when those change. Re-check it
  against their `CLAUDE.md` whenever that file's stack section changes.
