---
name: task-decomposer
description: Break a design document into a prioritized, dependency-ordered backlog of implementable tasks.
---

# Task Decomposer

Reads a design document and approved specification, then produces an ordered task list where each task is small enough to implement independently, has clear acceptance criteria, and explicit dependencies.

## Prerequisites

- Design document available in context or as a file path
- Approved specification available in context or as a file path

## Steps

1. Read the design document and specification.
2. Identify all implementation work implied by the design.
3. Split work into tasks, each completable in one focused session.
4. For each task: define a title, description, acceptance criteria, and dependencies.
5. Identify which tasks can be parallelized.
6. Estimate relative effort (S / M / L).
7. Order tasks so blockers come first.

## Output Format

```markdown
## Task List

### T-1: <Task Title> [S|M|L]
**Description:** What must be built.
**Acceptance Criteria:** Specific, verifiable conditions for done.
**Dependencies:** T-X, T-Y (or "none")
**Parallelizable with:** T-Z (or "none")

(repeat for each task)

## Dependency Graph

```
T-1 --> T-2 --> T-4
T-1 --> T-3 --> T-4
```

## Blockers

External dependencies or decisions that must be resolved before any task can begin.
```

## Example Usage

**Scenario 1: Export feature**
Design has: DB query, file serialization, download endpoint, background job.
Output: T-1 DB query layer (S, no deps), T-2 CSV serializer (S, no deps), T-3 JSON serializer (S, no deps), T-4 background job (M, depends T-1/T-2/T-3), T-5 download endpoint (S, depends T-4).

**Scenario 2: Dashboard**
Design has: WebSocket server, Redis pub/sub, frontend widget.
Output: T-1 Redis setup (S), T-2 WebSocket server (M, depends T-1), T-3 event publisher (S, depends T-1), T-4 frontend widget (M, depends T-2). T-2 and T-3 are parallelizable.
