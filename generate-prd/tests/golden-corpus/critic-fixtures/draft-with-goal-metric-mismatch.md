<!--
Planted flaw: Goals declares a specific quantitative target ("reduce
onboarding time by 50%") but Success Metrics is empty — the heading + intent
line only. A measurable goal without a measurement is a goal that can never
be confirmed achieved.

Expected critic finding: GOAL_METRIC_MISMATCH

The symmetric case (a metric without a goal it ties to) is also valid
GOAL_METRIC_MISMATCH territory, but this fixture covers the more common
direction.
-->

# loopr-onboarding

## Background & Problem
*What problem are we solving, and why is now the right time?*

Customers report week-one onboarding friction. [T01:00:01:23] [T02] [T05]

## Target Users
*Who is this for, and what do we know about them from the evidence?*

SMB operations teams of 20–200 people. [T01] [T02] [T05]

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

**Goal:** Reduce average team onboarding time by 50% in the first quarter post-launch (from ~14 days to ~7 days).

**Non-goal:** Enterprise compliance onboarding flows — out of scope for v1.

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

As an SMB ops lead, I want my team onboarded inside 7 days. [T01] [T02]

## Functional Requirements
*Numbered list of must-have capabilities.*

1. Per-user invite flow.
2. Per-team progress tracker.

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*
