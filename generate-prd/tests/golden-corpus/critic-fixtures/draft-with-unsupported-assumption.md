<!--
Planted flaw: Constraints declares "must integrate with Salesforce" but NO
transcript in the golden corpus mentions Salesforce. The PM did not justify
this in any prior Q&A turn either. This is a claim with zero evidence.

Expected critic finding: UNSUPPORTED_ASSUMPTION

Distinct from CONTRADICTION (which would require the transcripts to ARGUE
AGAINST Salesforce); UNSUPPORTED_ASSUMPTION is the weaker but more common
case — the draft just asserts something the evidence is silent on.
-->

# loopr-onboarding

## Background & Problem
*What problem are we solving, and why is now the right time?*

Customers report week-one onboarding friction across the corpus. [T01:00:01:23] [T02] [T05]

## Target Users
*Who is this for, and what do we know about them from the evidence?*

SMB operations teams of 20–200 people. [T01] [T02] [T05]

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

**Goal:** reduce week-one onboarding drop-off.

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

As an SMB ops lead, I want my team onboarded inside 7 days. [T01] [T02]

## Functional Requirements
*Numbered list of must-have capabilities.*

1. Per-user invite flow with email reminders.
2. Per-team progress tracker.

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*

- Must integrate with Salesforce as the customer system of record.
- Single-sign-on via Okta is mandatory.
- Deployment cannot require customer database changes.
