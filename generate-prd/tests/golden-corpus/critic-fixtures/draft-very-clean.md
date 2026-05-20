<!--
Clean-baseline fixture: a deliberately well-evidenced, well-scoped PRD draft.
Every claim has a citation; every goal has a metric; the persona declared in
Target Users matches every story's subject; the contradiction from the
golden corpus (T01 vs T04 pricing) is acknowledged in Risks rather than
ignored or hidden; no solution-bias language in Functional Requirements.

Expected critic behavior on this draft:
- The critic MAY find one or two small things (e.g., constraint scope could
  be tightened) — this is the realistic shape of PRD quality, not a perfect
  artifact.
- The critic MUST NOT signal closure. No "we're done", "looks complete",
  "ready to finalize", "PRD is in good shape", etc.

This is the artifact for Task 4.6's closure-discipline stress test. The
Phase 1 static test already verifies the critic prompt forbids closure
phrases; this fixture is the input for the future live verification.
-->

# loopr-onboarding

## Background & Problem
*What problem are we solving, and why is now the right time?*

SMB operations teams of 20-200 people consistently report week-one onboarding friction across customer conversations — the highest-frequency theme in the discovery corpus (5/5 transcripts). Onboarding drop-off is the primary blocker to converting paid trials into long-term seats. [T01:00:01:23] [T02] [T03:00:00:45] [T04:00:02:11] [T05]

## Target Users
*Who is this for, and what do we know about them from the evidence?*

**SMB ops manager** — leads a 20-200 person operations team at a mid-market SaaS company. Owns rollout of new tools end-to-end and is time-poor; first impression of a new tool decides whether the team adopts. Currently bottlenecked manually coordinating teammates through setup. [T01] [T02] [T05]

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

**Goal:** Reduce week-one onboarding drop-off for the SMB ops persona, measured as the share of teams completing all 3 setup milestones within 7 days.

**Non-goals:**
- Enterprise compliance flows (SOC2/HIPAA audit trails) — out of scope for v1 given the corpus only surfaces this in 1/5 transcripts. [T03] Revisit in v2 if compliance becomes a recurring theme.
- Onboarding for individual users without a team context — Loopr is a team-first product.
- Mobile-first onboarding — desktop is the primary surface for SMB ops managers per the corpus.

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

1. As an SMB ops manager, I want my team's 3 setup milestones complete in week one so that we hit our 30-day activation goal. [T01] [T02]
2. As an SMB ops manager, I want to see at a glance which teammates are stuck so that I can unblock them before they churn from the rollout. [T05]
3. As an SMB ops manager, I want to invite teammates without sending each one a separate calendar request so that I'm not bottlenecked on coordination. [T02]

## Functional Requirements
*Numbered list of must-have capabilities.*

1. Per-team progress visibility — ops manager can see at any moment which milestones each teammate has completed.
2. Bulk team-member invitation — adding a set of users in one action rather than one-by-one.
3. Inactivity reminders — teammates who haven't progressed in 48 hours receive a nudge.
4. Per-team milestone definition — teams can choose which of the 3 default milestones are required for their rollout.

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

*PM-judgment, deferred to discovery loop. Defaults proposed:*
- Onboarding pages must render in under 2 seconds on broadband connections (no measured baseline yet).
- SSO support (SAML and OIDC) consistent with the rest of Loopr.

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

- **Primary:** Week-one milestone completion rate increases from current 38% baseline to 60% within the first quarter post-launch. [T01]
- **Leading indicator:** Median time-to-first-milestone falls from current 3.2 days to under 1.5 days.
- **Counter-metric:** Support ticket volume tagged "onboarding" stays flat or decreases — we're not just shifting friction off the dashboard into the inbox.

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

- **Pricing model is contested in the corpus:** T01 indicated $50/seat would be acceptable; T04 indicated free is the only acceptable price. Resolving the pricing position is a launch dependency but is out of scope for this onboarding PRD; tracked separately.
- **Compliance scope** raised once (T03) but not weighted; revisit if it surfaces again in post-launch feedback.
- **Email deliverability** under high-volume bulk invitations is unverified; need to confirm we can send 200+ invites in a short window without triggering rate limits or spam classifiers.

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*

- Q3 ship window is fixed by the marketing campaign already in flight.
- The progress tracker must be reachable from the existing Loopr dashboard nav, not a separate URL.
