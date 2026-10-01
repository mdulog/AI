# Seed QA and the opt-in refinement pass

Loaded from `SKILL.md` (Phase 1→2 transition). Section names below refer to sections of `SKILL.md`. Text is moved verbatim from there; the rules in `SKILL.md` still apply.

- **Seed QA sub-rule** (fires at the Phase 1→2 transition): run `ouroboros_qa`
  on the generated Seed — `artifact` = the Seed YAML, `artifact_type` =
  `document`, `quality_bar` = whether the goal, constraints, and acceptance
  criteria are specific, measurable, and consistent with each other,
  `pass_threshold` = 0.90 (the bar Ouroboros's own seed skill uses). Report the
  verdict as advisory and never gate on the score. Branch on the returned
  verdict label, not on your own score comparison. If it is REVISE or FAIL,
  keep the returned QA session id (shown on the `Session:` line) for the
  pass's re-check, list the top two or three suggestions, carry every listed
  difference into Phase 2 as an open question for brainstorming to resolve
  explicitly and cite, and offer the human one opt-in
  refinement pass. To run it, read only the "Wonder → Reflect → Refine →
  Restate" section of Ouroboros's `seed` skill (`skills/seed/SKILL.md` in the
  plugin) and follow that section alone. Skip the rest of that skill: its
  generation step, its "After Seed Generation" section, and its closing
  breadcrumb, which include a GitHub-star prompt and setup steps that don't
  belong in this pipeline. Never run the pass, or chain another, without an
  explicit yes, and never hand-edit the Seed YAML outside that opted-in pass.
  After the pass, re-persist `seed.yaml`; its hash changes, so apply the Seed
  versioning rule in `SKILL.md`, and the refined Seed goes through the Seed
  approval gate before Phase 2. The pass may load tools this skill otherwise doesn't
  branch into (see Non-goals). That is Ouroboros's own opt-in behavior, not
  this skill's.
