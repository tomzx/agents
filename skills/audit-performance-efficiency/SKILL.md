---
name: audit-performance-efficiency
description: Audit the codebase for performance efficiency, the ISO/IEC 25010 characteristic covering time behavior, resource utilization, and capacity. Finds N+1 queries, missing indexes, unbounded operations, blocking I/O in hot paths, algorithmic complexity, and missing backpressure. Use when the user says /audit-performance-efficiency, "performance audit", "find slow code", "resource leaks", "capacity issues", "N+1", or runs a 25010 sweep via /audit-sdlc. Read-only; produces a findings report.
argument-hint: "[--severity critical|high|medium|low] [--path <dir>]"
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Performance Efficiency Audit (ISO/IEC 25010)

Audits the codebase for **performance efficiency**: response time, resource utilization, and capacity limits. It finds statically detectable performance antipatterns before they show up under load.

This is the **Performance efficiency** characteristic of the [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010) quality model. Distinct from `observe-production` (runtime latency/error measurement), this is static analysis of code that *will* be slow or wasteful.

## Prerequisites

- Working directory is the root of the repository
- Read `.sdlc/context/architecture.md` if present (to identify hot paths and data stores)
- Language-specific tooling optional (see Useful Commands Reference)

## What This Checks

| Sub-characteristic | What it means | Signals scanned |
|---|---|---|
| Time behavior | response/processing times under load | queries in loops (N+1), O(n²) algorithms, blocking I/O in request handlers, `time.sleep` in hot paths, missing pagination on list endpoints |
| Resource utilization | CPU, memory, file handles, connections | unbounded collections/caches, large allocations in loops, unclosed resources, missing connection pooling, full-table loads (`SELECT *`, `.all()`, `fetchall`) |
| Capacity | limits beyond which performance degrades | hardcoded single-thread assumptions, missing rate limiting, unbounded queues, no backpressure, missing indexes on queried columns |

## Steps

### 1. Identify hot paths and data stores

From `architecture.md` and route/endpoint discovery, identify request handlers, batch jobs, and data-access layers. These are where performance findings are most severe.

```
rg -n "@(app|router|api|blueprint)\.(get|post|put|delete|patch|route)" -g '*.py' .
rg -n "(get|post|put|delete|patch|use|all)\(['\"]" -g '*.{ts,js}' .
```

### 2. Query and data-access antipatterns (time behavior)

N+1 / queries-in-loops:
```
rg -n -B3 "for .+ in .+:" -g '*.py' . | rg "\.(get|filter|find|first|all|execute|query|load)\("
```
Full-table loads without limits:
```
rg -n "\.all\(\)|\.fetchall\(\)|SELECT \*|objects\.all|\.findAll\(" -g '*.{py,ts,js}' .
```
Unbatched writes inside loops:
```
rg -n "(\.save\(|\.insert\(|\.create\(|\.add\(|\.commit\(|db\.)" -g '*.py' .
```

### 3. Blocking operations in hot paths (time behavior)

Synchronous sleeps and blocking I/O inside handlers/tasks:
```
rg -n "time\.sleep|Thread\.sleep|asyncio\.sleep\([0-9]" -g '*.{py,java}' .
rg -n "requests\.(get|post)|urllib\.request|open\(|subprocess\.(run|call|Popen)" -g '*handler*.py' .
```
Synchronous calls inside async contexts:
```
rg -n -B2 "requests\.|urllib|time\.sleep|blocking" -g '*.py' . | rg -A2 "async def"
```

### 4. Algorithmic complexity (time behavior)

Nested loops over the same or growing collections:
```
rg -n "for .+ in" -g '*.py' . | wc -l   # then inspect files with high loop density
```
Recursion without memoization on paths that recompute. Flag recursive functions lacking a cache/decorator.

### 5. Resource utilization

Unbounded growth:
```
rg -n "global |_cache|_buffer|_history|_queue = \[\]| = \{\}" -g '*.py' . | rg -v "clear|maxlen|maxsize"
```
Unclosed resources:
```
rg -n "open\(|connect\(|cursor\(|Client\(" -g '*.py' . | rg -v "with |contextlib|__enter__"
```
Large allocations in loops:
```
rg -n -B1 "\[\]|list\(|dict\(|\.append" -g '*.py' . | rg -B1 "for .+ in"
```

### 6. Capacity and backpressure

Missing pagination on list endpoints (endpoints returning collections with no `limit`/`offset`/`page`):
```
rg -n "(list|all|search|index)" -g '*.{py,ts}' . | rg -iv "limit|offset|page|paginate|cursor"
```
Missing rate limiting on public endpoints; unbounded queues (`queue.Queue()` / channels without a bound); hardcoded worker counts.

### 7. Missing indexes (capacity)

Cross-reference query filters against schema/migrations. Columns used in `.filter()`, `WHERE`, or join conditions that lack an index are capacity findings.

```
rg -n "\.filter\(|WHERE |\.where\(" -g '*.{py,sql}' .
rg -n "create_index|Index\(|indexed=True|db_index" -g '*.{py,sql}' .
```

### 8. Existing benchmarks

If a benchmark/load-test suite exists (`bench/`, `benchmarks/`, `locustfile.py`, `k6`, `jest-bench`), note whether it covers the identified hot paths. Missing coverage of a hot path is a finding.

### 9. Report

Classify by severity and print. Do not modify files.

## Severity

| Severity | Criteria |
|---|---|
| Critical | N+1 on a request handler; full-table load on a large table in a hot path; unbounded memory growth in a long-running process |
| High | Blocking I/O in an async handler; missing pagination on a list endpoint; missing index on a filtered large table |
| Medium | O(n²) over modest inputs; unbatched writes; unclosed resource in a short-lived path |
| Low | Micro-optimizations; missing benchmark coverage |

## Output Format

```
# Performance Efficiency Audit — {TODAY}

## Summary
- Hot paths identified: N
- Time behavior findings: N critical, N high
- Resource utilization findings: N
- Capacity findings: N
- Benchmark coverage: <present on N hot paths | absent>

## Time behavior
| File:line | Pattern | Path | Severity | Recommendation |
|---|---|---|---|---|

## Resource utilization
| File:line | Pattern | Resource | Severity | Recommendation |
|---|---|---|---|---|

## Capacity
| File:line | Pattern | Limit | Severity | Recommendation |
|---|---|---|---|---|

## Index gaps
| Table | Queried columns | Indexed columns | Severity |
|---|---|---|---|
```

## Example Usage

**Scenario 1: 25010 sweep**
```
/audit-sdlc performance-efficiency
```

**Scenario 2: Focus on the API layer**
```
/audit-performance-efficiency --path src/api
```

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-security`, `audit-functional-suitability`, `audit-compatibility`, `audit-usability`, `audit-reliability`, `audit-maintainability`, `audit-portability` | The other seven ISO/IEC 25010 characteristics. Compose via `/audit-sdlc`. |
| `audit-sdlc` | Coordinator. |
| `observe-production` | Runtime counterpart: measures actual latency/throughput. This finds the code that *will* be slow. |
| `audit-reliability` | Closely related: missing timeouts and retries are both reliability and performance findings. Coordinate to dedup. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `rg -n -B3 "for .+ in" -g '*.py' . \| rg "\.(get\|filter\|find)\("` | N+1 query detection |
| `rg -n "\.all\(\)\|SELECT \*\|fetchall\(\)" -g '*.py' .` | Full-table loads |
| `rg -n "time\.sleep\|Thread\.sleep" -g '*.{py,java}' .` | Blocking sleeps |
| `rg -n "open\(\|connect\(" -g '*.py' . \| rg -v "with "` | Unclosed resources |
