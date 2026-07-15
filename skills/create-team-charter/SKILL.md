---
name: create-team-charter
description: Author a team charter defining the team's purpose, vision, stakeholders, responsibilities, roles, operating norms, decision-making, and success metrics as a single artifact.
argument-hint: "[team name or path]"
---

# Create Team Charter

Produces a team charter as a single artifact. Synthesizes the team's purpose, vision, customers, responsibilities, roles, operating norms, decision-making, and success metrics, so the team and its stakeholders share one clear answer to why the team exists, what it owns, and how it works.

A charter is not a strategy document or a backlog. It is the agreement that makes ownership and boundaries unambiguous. Without one, teams drift into overlapping work, unclear handoffs, and goals no one can prioritize against.

## Prerequisites

- A team name provided as `$1`, or stated in context. If omitted, ask for it before proceeding.
- The parent organization's mission and values, if available, to align with and avoid contradicting them.
- Existing artifacts for this team (a prior charter, an OKR doc, an org chart), if any, to revise rather than replace.
- Adjacent team charters, if any, to keep responsibilities and boundaries non-overlapping.

## Steps

1. Resolve the team name and derive the slug (lowercase, hyphenated, no special characters). Determine or ask for the parent org, the team lead or owner, and where team documents live (default `teams/<team-slug>/`).
2. Write the **Purpose**: one to two sentences on why this team exists and the problem or need it addresses for the organization. Name the organization-level outcome the team is accountable for, not the activities it performs.
3. Write the **Vision**: the future state the team is working toward over its current horizon (for example, the next year). Make it specific enough to guide decisions, not a generic aspiration.
4. Identify **Customers and stakeholders**: who the team serves (internal or external), who depends on its output, and whose goals it must advance. Name concrete groups or teams, not "the company".
5. Define **Responsibilities**: the outcomes and services the team owns outright, phrased as what it is accountable for. Separate core responsibilities from supporting ones.
6. Define **Non-responsibilities**: what the team deliberately does not own, with a pointer to the team that does where known. This section reduces boundary disputes and is as important as Responsibilities.
7. Capture **Roles and membership**: the people on the team and their roles (lead, members, extended or embedded), with a one-line accountability for each. Capture accountabilities, not every task.
8. Define **Operating norms**: how the team works day to day (cadences such as standup and planning, communication channels, core hours or handoffs, working agreements).
9. Define **Decision-making**: how decisions are made and escalated (for example, propose and discuss, then the lead decides; escalate unresolved conflicts to a named owner). State who has authority for what, so decisions do not stall.
10. Define **Success metrics**: how the team knows it is succeeding, framed as outcomes rather than activity. For detailed objectives and key results, link to `/create-goals` instead of duplicating the OKR detail here.
11. Optional: record **Values or guiding principles** the team commits to, especially where they differ from or emphasize the org's values. Omit the section if the team simply inherits the org values.
12. Record **Open questions**: anything unresolved (unclear ownership, a pending reorg, a dependency on another team's decision). A charter that names its open gaps is more useful than one that hides them.
13. Write the output to `teams/<team-slug>/charter.md` (or the path agreed in step 1) using the Output Format below.

## Output Format

Write a Markdown file with YAML frontmatter. Keep to one sentence per line in prose sections.

```markdown
---
team: <team-slug>
name: <Human-readable Team Name>
parent_org: <parent organization or business unit>
lead: <team lead name or handle>
last_reviewed: <ISO date>
status: draft
---

# <Team Name> Charter

## Purpose
{1-2 sentences: why this team exists and the outcome it owns.}

## Vision
{The future state the team is working toward this horizon.}

## Customers and Stakeholders
- {Customer or stakeholder group} - {what they need from the team}

## Responsibilities
- **{Core responsibility}** - {one line on what owning it means}
- **{Supporting responsibility}** - {one line}

## Non-responsibilities
- {What the team does not own} - {owned by <team>, or open}

## Roles and Membership
- {Role} ({name}) - {one-line accountability}

## Operating Norms
- **Cadences:** {standup, planning, retro schedule}
- **Channels:** {primary communication tools and what each is for}
- **Working agreements:** {core hours, handoff rules, on-call}

## Decision-making
{How decisions get made and escalated; who has authority for what.}

## Success Metrics
- {Outcome metric} - {why it indicates success}
- Reference detailed OKRs in {goals doc, e.g. .sdlc/context/goals.md or a linked doc}.

## Values (optional)
- {Principle the team commits to}

## Open Questions
- {Unresolved ownership, dependency, or decision} - {what is needed to resolve it}
```

## Charter Design Guidance

- **Purpose names an outcome, not an activity.** "Own reliable money movement" is a purpose; "write payments code" is an activity. Activities change; outcomes anchor the team.
- **Responsibilities and Non-responsibilities are a pair.** Every ambiguous boundary should appear in one list or the other. If two teams could plausibly own a thing, call it out under Non-responsibilities or Open Questions.
- **Customers are concrete.** "The growth and sales teams" beats "internal stakeholders". Concrete names make handoffs real.
- **Metrics are outcomes, not output.** "Deployment frequency" alone is activity; pair it with outcomes like change failure rate and time to restore, plus a business or reliability outcome.
- **Operating norms describe actual behavior, not aspiration.** If standup rarely happens, do not list it. Document how the team really works, then decide what to change.
- **A charter is ratifiable.** It should be short enough that the whole team can read it in one sitting and agree or disagree in a single review.
- **Inherit org values by default.** Add a Values section only where the team wants to emphasize or extend the org's principles.

## Example Usage

**Scenario 1: New platform team**
Team name: "Platform Infrastructure". Parent org: Engineering. Lead named.
Purpose: own the shared platform that product teams build on (compute, CI, shared libraries).
Responsibilities: platform uptime, deployment pipeline, shared service templates.
Non-responsibilities: product features (owned by stream-aligned teams), business logic.
Customers: the six product engineering teams.
Next step: run `/create-team-api` to formalize the platform's service interface and dependencies.

**Scenario 2: Stream-aligned product team clarifying its scope**
Team name: "Checkout". Existing charter is stale; two teams now touch checkout.
Revise: sharpen Non-responsibilities to name what Payments owns versus what Checkout owns, and add an Open Question about a disputed ownership area pending a lead decision.

**Scenario 3: Small early-stage team**
Team name: "Growth". No OKRs yet, no other teams to coordinate with.
Write a lean charter (Purpose, Customers, Responsibilities, Operating Norms, Open Questions). Note that success metrics are "to be defined" and recommend running `/create-goals` next.

## Next Step

- Run `/create-team-api` to formalize the team's ownership boundaries, services, dependencies, and interaction modes with other teams, especially for engineering teams.
- Share the charter with the team and its stakeholders for ratification, then set a review cadence (for example, revisit each quarter or on a reorg).
- For detailed objectives and key results, run `/create-goals` and link the resulting goals doc from the Success Metrics section.

## Useful Commands Reference

No CLI commands required. This skill operates on context provided in conversation and writes a Markdown file.
