# SDLC Agent Roles

Defines the agent roles involved in the software development lifecycle, their responsibilities, inputs, and outputs.

---

## Requirements Phase

### Requirements Gatherer
Collects raw requirements from stakeholders, issue descriptions, user stories, and existing documentation.

- **Inputs:** Issue trackers, stakeholder notes, existing specs, user feedback
- **Outputs:** Raw requirements list, open questions, stakeholder assumptions
- **Key activities:** Interview simulation, issue analysis, ambiguity flagging

### Requirements Analyst
Transforms raw requirements into structured, testable specifications.

- **Inputs:** Raw requirements from Gatherer
- **Outputs:** Formal spec (functional + non-functional requirements, acceptance criteria, edge cases)
- **Key activities:** Disambiguate language, define measurable criteria, identify constraints

### Requirements Judge
Reviews specs for completeness, consistency, and testability before implementation begins.

- **Inputs:** Formal spec from Analyst
- **Outputs:** Approval or list of deficiencies
- **Key activities:** Check for contradictions, missing edge cases, untestable criteria, scope creep

---

## Design Phase

### Architect
Defines the high-level technical design: system boundaries, component interactions, data models, and technology choices.

- **Inputs:** Approved spec, existing codebase, constraints
- **Outputs:** Design document (architecture diagram, API contracts, data models, ADRs)
- **Key activities:** Evaluate trade-offs, identify integration points, flag reversibility concerns

### Task Decomposer
Breaks the design into a prioritized backlog of discrete, implementable tasks.

- **Inputs:** Design document, approved spec
- **Outputs:** Ordered task list with effort estimates and dependencies
- **Key activities:** Identify parallelizable work, define task acceptance criteria, surface blockers

---

## Implementation Phase

### Implementer
Writes production code to fulfill a task's acceptance criteria.

- **Inputs:** Task description, acceptance criteria, design document, codebase
- **Outputs:** Working code on a feature branch
- **Key activities:** Code to spec, follow project conventions, leave no dead code or TODOs

### Debugger
Investigates failures, reproduces bugs, and applies targeted fixes.

- **Inputs:** Bug report or failing test, codebase
- **Outputs:** Root cause analysis, minimal fix, regression test
- **Key activities:** Reproduce, bisect, fix the cause (not the symptom)

---

## Testing Phase

### Test Writer
Authors tests that exercise the implementation against its acceptance criteria.

- **Inputs:** Acceptance criteria, implemented code
- **Outputs:** Unit, integration, and/or end-to-end tests
- **Key activities:** Cover happy path, edge cases, and failure modes; name tests descriptively

### Verifier
Runs the full test suite and confirms all tests pass in a clean environment.

- **Inputs:** Implementation branch, test suite
- **Outputs:** Pass/fail report with logs for any failures
- **Key activities:** Execute tests, check coverage thresholds, confirm no regressions

---

## Review Phase

### Code Reviewer
Reviews code for correctness, design quality, style, and maintainability.

- **Inputs:** Pull request diff, linked issue, design document
- **Outputs:** Prioritized review comments (MUST / SHOULD / MAY), approval or request for changes
- **Key activities:** Check scope, naming, SOLID principles, test quality, backward compatibility

### Security Reviewer
Audits code specifically for security vulnerabilities.

- **Inputs:** Pull request diff, threat model
- **Outputs:** Security findings with severity ratings
- **Key activities:** OWASP Top 10, input validation, auth/authz, secret handling, data exposure

---

## Validation Phase

### Validator
Confirms the implementation satisfies the original requirements and acceptance criteria end-to-end.

- **Inputs:** Approved spec, acceptance criteria, running build
- **Outputs:** Validation report (each criterion: pass / fail / partial)
- **Key activities:** Trace each requirement to its implementation, run acceptance tests, flag gaps

### QA Tester
Explores the system from a user perspective to find defects not caught by automated tests.

- **Inputs:** Running build, user stories
- **Outputs:** Bug reports with reproduction steps
- **Key activities:** Exploratory testing, regression sweeps, edge-case probing

---

## Release Phase

### Release Manager
Prepares and executes the release: versioning, changelog, artifact publishing, and rollout coordination.

- **Inputs:** Validated build, task list for the release
- **Outputs:** Release notes, tagged artifact, deployment runbook
- **Key activities:** Semantic versioning, changelog generation, coordinate staged rollout

---

## Operations Phase

### Monitor
Watches post-deployment signals (errors, latency, alerts) and surfaces anomalies.

- **Inputs:** Observability data (logs, metrics, traces)
- **Outputs:** Incident reports, regression flags
- **Key activities:** Detect regressions, correlate signals, escalate critical issues

### Triage Agent
First responder for production issues: reproduces, scopes, and routes to the right fix path.

- **Inputs:** Incident report or alert
- **Outputs:** Severity assessment, reproduction case, owner assignment
- **Key activities:** Reproduce issue, determine blast radius, distinguish bug vs. misconfiguration

---

## Role Interaction Map

```
Gatherer --> Analyst --> Judge
                            |
                        Architect --> Decomposer
                                           |
                                      Implementer <--> Debugger
                                           |
                                      Test Writer --> Verifier
                                           |
                              Code Reviewer + Security Reviewer
                                           |
                                   Validator + QA Tester
                                           |
                                    Release Manager
                                           |
                                 Monitor + Triage Agent
```
