# SDLC Agent Roles

Each role in the software development lifecycle is implemented as a skill. Invoke them with `/role-name`.

---

## Requirements Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Requirements Gatherer | [`/requirements-gatherer`](skills/requirements-gatherer/SKILL.md) | Collect raw requirements from issues, user stories, and stakeholder input |
| Requirements Analyst | [`/requirements-analyst`](skills/requirements-analyst/SKILL.md) | Transform raw requirements into a formal, testable specification |
| Requirements Judge | [`/requirements-judge`](skills/requirements-judge/SKILL.md) | Review the spec for completeness, consistency, and testability |

## Design Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Architect | [`/architect`](skills/architect/SKILL.md) | Produce a high-level technical design with ADRs |
| Task Decomposer | [`/task-decomposer`](skills/task-decomposer/SKILL.md) | Break the design into a prioritized, dependency-ordered task backlog |

## Implementation Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Implementer | [`/implementer`](skills/implementer/SKILL.md) | Write production code to satisfy a task's acceptance criteria |
| Debugger | [`/debugger`](skills/debugger/SKILL.md) | Reproduce failures, find root causes, and apply minimal targeted fixes |

## Testing Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Test Writer | [`/test-writer`](skills/test-writer/SKILL.md) | Author tests covering happy path, edge cases, and failure modes |
| Verifier | [`/verifier`](skills/verifier/SKILL.md) | Run the full test suite and confirm no regressions |

## Review Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Code Reviewer | [`/pr-review`](skills/pr-review/SKILL.md) | Review code for correctness, design quality, and maintainability |
| Security Reviewer | [`/security-reviewer`](skills/security-reviewer/SKILL.md) | Audit code for OWASP Top 10 and implementation vulnerabilities |

## Validation Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Validator | [`/validator`](skills/validator/SKILL.md) | Confirm every acceptance criterion is satisfied end-to-end |
| QA Tester | [`/qa-tester`](skills/qa-tester/SKILL.md) | Explore the system from a user perspective to find defects |

## Release Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Release Manager | [`/release-manager`](skills/release-manager/SKILL.md) | Version bump, changelog, tagging, and deployment runbook |

## Operations Phase

| Role | Skill | Responsibility |
|------|-------|----------------|
| Monitor | [`/monitor`](skills/monitor/SKILL.md) | Watch post-deployment signals and surface anomalies |
| Triage Agent | [`/triage-agent`](skills/triage-agent/SKILL.md) | First responder for incidents: reproduce, scope, and route |

---

## Role Interaction Map

```
/requirements-gatherer --> /requirements-analyst --> /requirements-judge
                                                              |
                                                         /architect --> /task-decomposer
                                                                               |
                                                                         /implementer <--> /debugger
                                                                               |
                                                                         /test-writer --> /verifier
                                                                               |
                                                               /pr-review + /security-reviewer
                                                                               |
                                                                  /validator + /qa-tester
                                                                               |
                                                                      /release-manager
                                                                               |
                                                                /monitor + /triage-agent
```
