<!--
Planted flaw: Target Users declares exactly ONE persona — "SMB ops manager,
20-200 person team." But the User Stories include a story whose subject is
"enterprise IT admin" — a persona that is NOT declared in Target Users and
has no transcript backing in the SMB-focused golden corpus.

Expected critic finding: PERSONA_STORY_MISMATCH

Distinct from PERSONA invention: the SMB persona IS valid; the story
ALSO names a persona that wasn't introduced. The story doesn't trace to
a declared user.
-->

# loopr-onboarding

## Background & Problem
*What problem are we solving, and why is now the right time?*

Customers report week-one onboarding friction. [T01:00:01:23] [T02] [T05]

## Target Users
*Who is this for, and what do we know about them from the evidence?*

**SMB ops manager** — leads a 20-200 person operations team at a mid-market SaaS company. Owns rollout of new tools end-to-end. Time-poor; first impression of a new tool decides whether the team adopts. [T01] [T02] [T05]

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

**Goal:** Reduce week-one onboarding drop-off for the SMB ops persona.

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

1. As an SMB ops manager, I want my team's 3 setup milestones complete in week one so that we hit our 30-day activation goal. [T01] [T02]

2. As an SMB ops manager, I want to see at a glance which teammates are stuck so that I can unblock them before they churn from the rollout. [T05]

3. As an **enterprise IT admin**, I want SOC2-compliant audit trails of every onboarding action so that I can prove access controls to my security review. [no citation]

4. As an SMB ops manager, I want to invite teammates without sending each one a separate calendar request so that I'm not bottlenecked on coordination. [T02]

## Functional Requirements
*Numbered list of must-have capabilities.*

1. Per-team progress tracker visible to the ops manager.
2. Bulk-invite flow.

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*
