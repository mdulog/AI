# Engineering defaults: Context7 lookups and stack defaults

Loaded from `SKILL.md` (Phase 1 when the human asks about the stack, Phase 2 design, and Phase 3 implementation when a library or stack decision comes up). Section names below refer to sections of `SKILL.md`. Text is moved verbatim from there; the rules in `SKILL.md` still apply.

## Documentation lookups (Context7)

- Always use Context7 (`mcp__plugin_context7_context7__resolve-library-id` +
  `mcp__plugin_context7_context7__query-docs`) during Phase 2
  design or Phase 3 implementation when a library, framework, SDK, API, or
  CLI tool is involved — even well-known ones. Never rely on trained
  knowledge alone; training data may not reflect recent API changes,
  version migrations, or deprecations.
- Use for: API syntax, configuration options, version migration guides,
  setup instructions, CLI usage, library-specific debugging. Not needed for:
  general programming concepts, refactoring, business logic, or code review.

## Language & stack defaults

- Primary language: C# / .NET (latest LTS) for new/greenfield work in
  Phase 3, unless the target project specifies otherwise.
- Frontend: React/TypeScript for new/greenfield UI work. For an existing
  project, match whatever's already there instead (Angular, Vue, etc.) —
  check the repo (`package.json`, `*.csproj`, existing components) before
  assuming greenfield applies.
- Default test framework: TUnit (.NET) and Jest (React) for new/greenfield
  work. An existing project's tests follow whatever test convention that
  project already uses, not this default.
- These are defaults for new/greenfield work only — always defer to what the
  target project's own conventions or existing codebase specifies. If the
  human's own instructions (their `CLAUDE.md`) name a different stack than
  the above, say so during Phase 2 and ask; don't silently pick one. This
  section copies the human's global defaults so the skill stays
  self-contained, which means it drifts when those change. Re-check it
  against their `CLAUDE.md` whenever that file's stack section changes.
