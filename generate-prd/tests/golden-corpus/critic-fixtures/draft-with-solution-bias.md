<!--
Planted flaw: Functional Requirement §3 prescribes the implementation
("one-click onboarding dashboard widget", "REST API endpoints", "GET
/onboarding/state") rather than the capability ("teams can see and
resume their onboarding progress at any time"). This is solution
anchoring — the PRD is the wrong place to choose UI shape or API
verbs.

Expected critic finding: SOLUTION_BIAS
-->

# loopr-onboarding

## Background & Problem
*What problem are we solving, and why is now the right time?*

Customers report onboarding friction in the first week, particularly the inability to see where they are in setup. [T01:00:01:23] [T02] [T05]

## Target Users
*Who is this for, and what do we know about them from the evidence?*

SMB operations teams of 20–200 people. [T01] [T02] [T05]

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

As an SMB ops lead, I want my team to onboard onto Loopr quickly so that we hit our 30-day activation goal. [T01] [T02]

## Functional Requirements
*Numbered list of must-have capabilities.*

1. Email-based invite flow for new users.
2. SSO support (SAML and OIDC).
3. Implement a one-click onboarding dashboard widget with REST API endpoints exposing `GET /onboarding/state` and `POST /onboarding/step/{id}/complete`. The widget must be a React component pulling from a Redis-backed cache so the dashboard renders in <100ms.
4. Email reminders for incomplete onboarding steps.

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*
