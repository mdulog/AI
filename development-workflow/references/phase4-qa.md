# Phase 4: model policy and the ouroboros_qa call

Loaded from `SKILL.md` (Phase 4, before calling `ouroboros_qa`, and before Phase 1's Seed QA). Section names below refer to sections of `SKILL.md`. Text is moved verbatim from there; the rules in `SKILL.md` still apply.

- **Model policy.** Dispatch review agents with `model: opus`, even though
  `ExitPlanMode` has already dropped the session to Sonnet. The main-session
  verification gate below (reading test output) runs on the session model.
  Reviewers dispatched inside `superpowers:subagent-driven-development`
  choose their own model under that skill's guidance.
  `ouroboros_qa` has no model parameter and, in Claude Code, ignores the
  session model — plan mode has no effect on it, including the Seed QA call
  in Phase 1. Checked against Ouroboros 0.55.3: QA is a standard-tier role,
  so with no config it resolves to the `sonnet` alias. Earlier versions
  (0.54.5) fell back to an Opus-pinned `evaluation.semantic_model`; that
  path no longer exists. QA runs on Opus because `~/.ouroboros/config.yaml`
  sets `models.pin: true` and `llm.qa_model: opus`. `pin` is what makes a
  per-role id apply, and with only `qa_model` set every other role stays on
  its automatic tier. Keep it that way: do not add other role ids or set
  `models.default`, which applies to every role. Do not edit that file on
  your own. Before Phase 1's Seed QA, confirm the file still holds both
  settings (`ouroboros setup` or a config tool may rewrite it), and if it
  doesn't, tell the human that QA would run on Sonnet. Re-check this
  paragraph after any Ouroboros upgrade.

## The ouroboros_qa call

- **Additionally** — Phase 1's invariant guarantees a Seed always exists for
  any in-scope task — invoke `ouroboros_qa`: `artifact` = the complete,
  unelided diff plus the real test output and any CLI or behavior transcript
  the acceptance criteria refer to, pasted inline (there is no file
  parameter, and `ouroboros_qa` runs nothing itself, so missing evidence shows
  up as a finding), `seed_content` = the current Seed, `quality_bar` = a
  restatement of the Seed's acceptance criteria that the code diff can
  satisfy. Leave out criteria about documentation: Phase 5's doc-sync check
  owns those. Say so inside `quality_bar`
  ("documentation criteria, including any README requirement in the Seed's
  goal or criteria, are out of scope for this artifact and are checked in a
  later phase"), because `seed_content` still contains them and QA otherwise
  lists the missing README as its top difference. Also add the criteria that
  `design.md` resolved from the Seed QA differences: the Seed isn't edited,
  so QA would otherwise never check them. Do NOT use
  `ouroboros_evaluate`/`ouroboros_start_evaluate` for this — those tools
  hard-require a `session_id`, and sessions in Ouroboros only exist for work
  Ouroboros itself executed (`execute_seed`/`start_execute_seed`), which this
  pipeline never does. `ouroboros_qa` requires no session at all and is built
  for exactly this "grade an externally-produced artifact against a spec"
  case.
