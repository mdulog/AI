<!--
Planted flaw: Goals & Non-Goals targets "enterprise users with compliance
needs" but the themes (compliance is 1/5 in T03 only; onboarding friction
is 5/5 across SMB customers) contradict this audience choice.

Expected critic finding: CONTRADICTION
-->

# loopr-onboarding

## Background & Problem
*What problem are we solving, and why is now the right time?*

Customers struggle to get their teams onboarded onto Loopr in the first week. [T01:00:01:23] [T02] [T05]

## Target Users
*Who is this for, and what do we know about them from the evidence?*

Mid-market SMB operations teams of 20–200 people. [T01] [T02] [T05]

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

**Goal:** target enterprise users with strict SOC2 / HIPAA compliance workflows; deliver an audit-ready onboarding flow as the primary use case. [T03:00:04:11]

**Non-goal:** SMB onboarding friction (deferred to a later release).

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

As an enterprise compliance officer, I want SOC2-aligned audit trails of onboarding events so that I can demonstrate compliance during quarterly review. [T03]

## Functional Requirements
*Numbered list of must-have capabilities.*

1. Audit log of every onboarding action, retained 7 years.
2. SOC2-aligned access reviews on Day 1 of onboarding.

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

- Compliance scope unclear; transcripts under-cite this need. [T03]

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*
