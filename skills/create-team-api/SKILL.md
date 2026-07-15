---
name: create-team-api
description: Define a team's Team API (Team Topologies), covering team type, ownership boundaries, services, inputs, outputs, dependencies, and interaction modes with other teams.
argument-hint: "[team name]"
---

# Create Team API

Defines a team's "Team API": the explicit interface other teams consume to work with it. Frames the team using Team Topologies (Skelton and Pais), capturing its team type, ownership boundaries, the services it provides, its inputs and outputs, its dependencies, and the interaction modes it uses with adjacent teams.

Where a charter says why a team exists and how it works internally, the Team API says how the rest of the organization interacts with it. Making the interface explicit lets other teams consume the team's work through stable contracts instead of ad hoc asks, which is the precondition for fast, independent flow.

## Prerequisites

- A team name provided as `$1`, or stated in context. If omitted, ask for it.
- The team's charter, ideally produced by `/create-team-charter`, for purpose and responsibilities. If absent, derive purpose and responsibilities from context and flag the gap.
- Awareness of adjacent teams (their charters or APIs, if available) to map dependencies and interaction modes accurately.
- For engineering teams: the services, repositories, and systems the team owns.

## Steps

1. Resolve the team name and slug, and confirm the output path (default `teams/<team-slug>/team-api.md`).
2. Classify the **Team type** per Team Topologies: stream-aligned, platform, enabling, or complicated-subsystem. If unsure, choose the closest and justify it in a sentence. A team's type can change as the organization evolves.
3. State the team's **Purpose** in one sentence, the reason its API exists. Reuse the charter's purpose verbatim when one exists.
4. Define **Ownership boundaries**: what the team owns outright (services, repositories, domains, data, infrastructure, on-call) and what it does not own. Ownership means the team is the approver of changes and the responder for incidents for that thing.
5. Define **Services provided**: the capabilities the team offers to the rest of the organization, each framed as a consumable service with a one-line description (for example, "Hosted CI pipeline", "User identity API", "Onboarding enablement engagement").
6. Define **Inputs**: what the team needs from others and in what form (for example, feature requests via an intake form, dependency upgrades via tickets, decisions via named owners). An input without a stated form invites unstructured interruptions.
7. Define **Outputs**: what the team produces and how others receive it (deployed services with an API contract, versioned libraries, documentation, an SLA). Outputs should have a stable, discoverable form.
8. Map **Dependencies**: upstream teams this team depends on, and downstream teams that depend on it, with the nature of each dependency.
9. Assign **Interaction modes** to each dependency per Team Topologies:
   - **x-as-a-service** (default for steady state): another team consumes a stable, versioned interface with low communication overhead.
   - **collaboration** (high-bandwidth, temporary): used during exploration or when a boundary is unclear; narrow in scope and time-boxed so it does not become a permanent merger.
   - **facilitating** (an enabling team helping this team learn a capability): time-boxed, and it ends when the capability is transferred.
   Default to x-as-a-service wherever possible; reserve collaboration for genuine uncertainty.
10. Define the **Request and communication interface**: the single intake path for work requests, the expected response time or SLA, the primary channel, and how breaking changes to the team's outputs are announced and versioned.
11. Record **Evolution**: expected changes as the team or org matures (for example, a platform team moving a service from collaboration to x-as-a-service once the API stabilizes, or a stream-aligned team splitting as scope grows).
12. Record **Open questions**: unresolved ownership, missing dependencies, interfaces still being negotiated.
13. Write the output to `teams/<team-slug>/team-api.md` using the Output Format below.

## Output Format

```markdown
---
team: <team-slug>
name: <Human-readable Team Name>
team_type: <stream-aligned | platform | enabling | complicated-subsystem>
last_reviewed: <ISO date>
status: draft
---

# <Team Name> Team API

## Purpose
{One sentence: why this team's interface exists.}

## Team Type
{stream-aligned | platform | enabling | complicated-subsystem} - {one-line justification}

## Ownership Boundaries
**Owns:**
- {service / repo / domain / data / infra} - {what ownership means here}

**Does not own:**
- {thing} - owned by <team>

## Services Provided
- **{Service name}** - {one-line description; how to consume}

## Inputs
- {What the team needs} - {form: ticket / API / doc / named owner}

## Outputs
- {What the team produces} - {form: versioned API / library / doc / SLA}

## Dependencies
**Upstream (we depend on):**
- <team> - {nature of dependency}

**Downstream (depend on us):**
- <team> - {nature of dependency}

## Interaction Modes
| Partner team | Mode | Notes |
|---|---|---|
| <team> | x-as-a-service | consumes our {service} via stable API |
| <team> | collaboration | time-boxed, exploring {X}, until {date or condition} |

## Request and Communication Interface
- **Intake:** {single path for requests}
- **Response SLA:** {expected response time}
- **Primary channel:** {tool}
- **Breaking changes:** {how announced and versioned}

## Evolution
- {Expected change} - {trigger or condition}

## Open Questions
- {Unresolved interface, ownership, or dependency} - {what is needed to resolve it}
```

## Team API Design Guidance

- **Default to x-as-a-service.** It is the only interaction mode that scales. Collaboration and facilitating modes are valuable but temporary; convert them to x-as-a-service as soon as an interface can stabilize.
- **Ownership is about authority, not proximity.** Owning a service means approving its changes and owning its incidents. If the team cannot approve a change to something, it does not own it, even if it works on it daily.
- **Every input has a form.** "Stakeholder feedback" is not an input; "a weekly prioritization meeting with the growth lead" is. Unformed inputs become interruptions.
- **Every output is discoverable and versioned.** An undocumented service is not part of the API. If consumers cannot find it and rely on a version, it does not count.
- **Dependencies should point at other team APIs.** Where a dependency is on another team, reference its Team API rather than describing it informally, so contracts stay consistent across the organization.
- **Match the team type to the work.** A platform team that is mostly doing stream-aligned feature work is mislabeled; surface that as an Open Question or an Evolution item.

## Example Usage

**Scenario 1: Platform team**
Team type: platform.
Services: shared CI pipeline, base container images, deployment templates.
Interaction modes: x-as-a-service with all six product teams (they consume the pipeline); collaboration with one product team that is piloting a new deploy model, time-boxed to one quarter, then converts to x-as-a-service.
Evolution: move the pilot to a stable, self-service pipeline by quarter end.

**Scenario 2: Enabling team**
Team type: enabling (for example, an observability enablement team).
Services: observability onboarding engagement, instrumentation guidance, tooling clinics.
Interaction modes: facilitating with each product team (time-boxed engagements that end when the team can self-serve); x-as-a-service for the shared metrics platform it maintains.
Evolution: as product teams mature, shift from facilitating to maintaining the self-service platform only.

**Scenario 3: Stream-aligned team with a fuzzy boundary**
Team type: stream-aligned (for example, Checkout).
A neighboring Payments team also changes checkout-adjacent code.
Document the disputed ownership under Open Questions and use collaboration mode with Payments until a boundary is agreed, then move to x-as-a-service with a clear ownership line.

## Next Step

- Pair this with `/create-team-charter` if the charter does not yet exist; the charter holds the why and the internal norms, and the Team API holds the external interface.
- Review the Team API with every dependent team named in the Dependencies section, since a Team API is a contract that both sides must agree to.
- Revisit when the team type, a major service, or a key interaction mode changes.

## Useful Commands Reference

No CLI commands required. This skill operates on context provided in conversation and writes a Markdown file.
