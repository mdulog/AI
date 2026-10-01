# Doc-baseline step

Loaded from `SKILL.md` (Phase 2 architectural path, and Phase 5 backstop). Section names below refer to sections of `SKILL.md`. Text is moved verbatim from there; the rules in `SKILL.md` still apply.

- **Doc-baseline check** (architectural path only): if the target is a git
  repo with no doc baseline (no root `README.md` and no `docs/` taxonomy),
  include an explicit "establish doc baseline" step in the plan itself —
  authored as part of `superpowers:writing-plans`, before any implementation
  step. Write the step so that, when it executes in Phase 3, it invokes
  `docs-as-code-baseline` if that skill is present in the registry;
  otherwise it writes the baseline manually — inspecting the repo first and
  producing only evidence-backed content: root `README.md` (purpose,
  prerequisites, verified quick start and dev commands, architecture
  summary, config-variable *names* only, contribution guidance), plus an ADR
  location only when the repo actually justifies one — reuse an existing
  `architecture/decisions/` folder if the repo already has one, otherwise
  create `docs/adr/`, or use `AGENTS.md` if that fits the repo better.
  Authoring this step happens now, in Phase 2; nothing gets written to the
  target repo until Phase 3 executes it — Phases 1–2 write only to the run
  directory (see Phase 1), and Plan Mode blocks target-repo writes
  regardless. Surfacing it here lets the doc scope get reviewed alongside
  the rest of the plan instead of landing unannounced at Phase 5. Skip, and
  ask first, if the project looks intentionally doc-less (private script
  folder, monorepo subpackage, spike/scratch dir). Record a skip as
  `doc_baseline_skipped` in `steps_completed`.

## Phase 5 backstop

- Before step 1, so any newly established baseline gets swept into that
  step's diff-and-commit rather than left uncommitted: on the architectural
  path, if this is the first time a missing doc baseline surfaces, that
  means Phase 2's doc-baseline check was skipped or missed — treat it as a
  process gap worth flagging. On the bounded path, Phase 2 never runs that
  check by design, so surfacing here is the intended path, not a gap.
  Either way, establish the baseline here as the backstop — invoke
  `docs-as-code-baseline` if it's present in the skill registry, otherwise
  write it manually using the same evidence-backed scope (including the
  ADR-location check) as in `references/doc-baseline.md` — unless Phase 2
  recorded a deliberate skip (`doc_baseline_skipped` in `steps_completed`)
  or the target isn't a git repo. On the bounded path, ask first if the
  project looks intentionally doc-less (the same test as Phase 2).
