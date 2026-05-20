<!--
Planted flaw: Risks & Open Questions raises "compliance scope" as a primary
risk citing only T03 (which is 1/5 — the low-frequency outlier in the
corpus per expected/themes-summary.md). The section treats this as a major
risk for v1 even though the evidence is a single passing mention from one
transcript.

Expected critic finding: EVIDENCE_THIN

Distinct from UNSUPPORTED_ASSUMPTION (which would be zero evidence). Here
there IS evidence — a single citation — but the strength of the claim
("primary risk for v1") is wildly out of proportion to the strength of
the support (1/5, single utterance, no follow-up).

Distinct also from COVERAGE_GAP (which would be: theme is in transcripts
but not in PRD). Here the theme IS in the PRD; it's just over-weighted.
-->

# loopr-onboarding

## Background & Problem
*What problem are we solving, and why is now the right time?*

SMB ops teams report week-one onboarding friction. [T01:00:01:23] [T02] [T05]

## Target Users
*Who is this for, and what do we know about them from the evidence?*

SMB ops managers leading 20-200 person teams. [T01] [T02] [T05]

## Goals & Non-Goals
*What we're solving; what we're explicitly NOT solving in this scope.*

**Goal:** Reduce week-one onboarding drop-off for SMB ops teams.

## User Stories
*Intent expressed as: As a [user], I want [goal] so that [outcome].*

As an SMB ops manager, I want my team's 3 setup milestones complete in week one. [T01] [T02]

## Functional Requirements
*Numbered list of must-have capabilities.*

1. Per-team progress tracker.
2. Bulk-invite flow.

## Non-Functional Requirements
*Performance, security, accessibility, compatibility, reliability.*

## Success Metrics
*How we'll know it worked. Tied back to Goals.*

Week-one milestone completion rate increases from 38% to 60% within Q3. [T01]

## Risks & Open Questions
*What we don't know yet; blockers, dependencies, and unresolved decisions.*

- **Primary risk: SOC2 / HIPAA compliance scope is undefined for v1.** A single customer raised this in passing during discovery. [T03:00:04:11] We cannot ship without resolving whether onboarding events must produce audit trails compliant with both standards — this is the single biggest blocker for the launch.

- Secondary: invite-flow email deliverability under high-volume rollouts. [T02]

## Constraints
*Known limits — technical, regulatory, contractual, organizational, temporal — that bound the solution space.*
