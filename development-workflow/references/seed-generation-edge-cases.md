# Seed generation: refusals, gap questions, client gates

Loaded from `SKILL.md` (Phase 1, before calling `ouroboros_generate_seed` and again if it refuses or asks for more). Section names below refer to sections of `SKILL.md`. Text is moved verbatim from there; the rules in `SKILL.md` still apply.

- Seed generation can refuse or ask for more, and the two paths differ
  (checked against Ouroboros 0.55.3; re-check these after an Ouroboros upgrade):
  - The `session_id` call after an interview can refuse: it enforces an
    ambiguity threshold of 0.2 unless `force` is set, and it can also refuse
    when the interview needs to reopen. If it refuses, show the refusal to the
    human and return to the interview. Set `force` only with the human's
    explicit consent.
  - The direct `session_context` call has no ambiguity refusal and no `force`.
    If the input is incomplete it returns `gap_questions_required`: ask the
    human those questions, merge the answers into `session_context`, and call
    again.
- Ouroboros can require "client gates" on the `session_id` call. With
  `OUROBOROS_REQUIRE_CLIENT_GATES` set to 1, true, yes, or on, that call fails
  unless `client_gates` are passed. This skill and Ouroboros's interview skill
  don't pass them (`ooo auto` does), so leave the variable unset. Even then
  the call may show a "Client Gate Warning" in its output or metadata;
  expect it and ignore it. The direct path has neither the failure nor the warning.
