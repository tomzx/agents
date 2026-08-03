---
name: audit-reliability
description: Audit the codebase for reliability, the ISO/IEC 25010 characteristic covering maturity, availability, fault tolerance, and recoverability. Finds swallowed exceptions, missing timeouts on network calls, missing retries/circuit breakers on external dependencies, non-idempotent operations, missing transaction boundaries, and missing graceful-shutdown and health-check handling. The design-side counterpart to observe-production (runtime) and audit-observability (instrumentation). Use when the user says /audit-reliability, "fault tolerance audit", "error handling audit", "resilience check", or runs a 25010 sweep via /audit-sdlc. Read-only; produces a findings report.
argument-hint: "[--severity critical|high|medium|low] [--path <dir>]"
allowed-tools: Bash, Read, Glob, Grep
---

TODAY=!`date +%Y-%m-%d`

# Reliability Audit (ISO/IEC 25010)

Audits the codebase for **reliability**: how the system behaves when components fail, and how it recovers. It finds statically detectable design weaknesses that cause outages and data loss.

This is the **Reliability** characteristic of the [ISO/IEC 25010](https://en.wikipedia.org/wiki/ISO/IEC_25010) quality model. Distinct from `observe-production` (is it failing right now?) and `audit-observability` (is failure instrumented?), this asks: is the system *designed* to tolerate and recover from failure?

## Prerequisites

- Working directory is the root of the repository
- Read `.sdlc/context/architecture.md` if present (for external dependencies and stateful components)

## What This Checks

| Sub-characteristic | What it means | Signals scanned |
|---|---|---|
| Maturity | frequency of failure from foreseeable causes | known fragile patterns (bare except, swallowed errors); flaky external calls |
| Availability | operational continuity | single points of failure; stateful singletons assumed unique; missing health/readiness endpoints; missing graceful shutdown |
| Fault tolerance | keeps operating despite hardware/software faults | external calls without timeout; missing retry/backoff; missing circuit breaker on shared dependencies; cascading-failure risks |
| Recoverability | can restore lost data and re-establish the desired state | non-idempotent writes; multi-step writes without transaction boundaries; missing rollback; background jobs without at-least-once/at-most-once clarity; state without persistence |

## Steps

### 1. Exception handling (maturity)

Bare/over-broad exception handlers that swallow errors:
```
grep -rEnA2 "except\s*:|except\s+(Exception|BaseException)\s*:" --include="*.py" . | grep -E "pass|continue|\.\.\.|return None|return \[\]"
```
```
grep -rEn "catch\s*\(\s*\)\s*\{|catch\s*\{" --include="*.ts" --include="*.js" --include="*.java" .
```
Logged-but-swallowed errors (caught, logged, then treated as success):
```
grep -rEnB1 -A3 "except" --include="*.py" . | grep -E "logger.*\.(info|debug)|console\.(log|debug)"
```

### 2. Fault tolerance on external calls

Network/external calls without a timeout:
```
grep -rEn "requests\.(get|post|put|delete|patch|head)\(|urlopen|httpx\.(get|post)|fetch\(|axios\.|grpc\.|boto3|psycopg|redis\.|kafka" \
  --include="*.py" --include="*.ts" --include="*.js" . | grep -v "timeout"
```
External calls without retry/backoff (look for absence of `retry`, `tenacity`, `backoff`, `resilience4j`, `polly` around call sites).

External dependencies used directly (no circuit breaker / bulkhead) — flag hot-path dependencies called without any failure isolation.

### 3. Availability

Stateful singletons assumed unique:
```
grep -rEn "^\s*class\s+\w+.*:\s*$" --include="*.py" . | head; grep -rEn "= \w+\(\)\s*$|_instance|__new__|Singleton" --include="*.py" .
```
Health/readiness endpoints:
```
grep -rEn "/healthz|/readyz|/health|/livez|/readiness|actuator/health" --include="*.py" --include="*.ts" --include="*.js" --include="*.java" .
```
If none found and the service is server-side, flag missing health checks.

Graceful shutdown: signal handling and in-flight draining:
```
grep -rEn "signal\.|SIGTERM|SIGINT|atexit|on_shutdown|lifespan|graceful" --include="*.py" --include="*.ts" --include="*.js" .
```
Server-side code with no signal/shutdown handling cannot drain in-flight work on deploy.

### 4. Recoverability: idempotency and transactions

Non-idempotent writes (create-on-each-call without an idempotency key or natural key):
```
grep -rEn "\.create\(|\.insert\(|INSERT INTO|\.save\(|POST" --include="*.py" --include="*.sql" . | grep -v "idempot\|unique\|ON CONFLICT\|upsert"
```
Multi-step writes without a transaction boundary:
```
grep -rEnB3 -A3 "\.save\(|\.commit\(|INSERT|UPDATE|DELETE" --include="*.py" . | grep -v "transaction\|atomic\|begin\|with .*transaction\|@Transactional"
```
Background jobs without a delivery semantic (at-least-once vs at-most-once) — flag queues/jobs without a dedup or ack mechanism.

### 5. Recoverability: data durability

Writes that buffer in memory without persistence (ack before durable write):
```
grep -rEn "append\(|\.put\(|enqueue|publish" --include="*.py" --include="*.ts" --include="*.js" .
```
Cache treated as source of truth (reads from cache with no fallback/repopulate on miss that persists).

### 6. Cascading-failure risks

Synchronous chains across services/deps with no bulkhead; shared thread/connection pools sized for one tenant; in-process caches without bounds (a full cache that OOMs one instance OOMs all). Coordinate with `audit-performance-efficiency` (unbounded growth) and `audit-security` (DoS) to dedup.

### 7. Report

Classify by severity and print. Do not modify files.

## Severity

| Severity | Criteria |
|---|---|
| Critical | Multi-step write without a transaction (data corruption on failure); external call with no timeout on a critical path; swallowed exception hiding data loss |
| High | Missing health/readiness endpoint on a server-side service; missing graceful shutdown; non-idempotent write on a retry-prone path |
| Medium | Missing retry/backoff on a flaky dependency; bare except in a non-critical path; cache-as-source-of-truth |
| Low | Over-broad except with logging; missing circuit breaker on a low-traffic dependency |

## Output Format

```
# Reliability Audit — {TODAY}

## Summary
- Maturity (exception handling) findings: N
- Availability findings: N
- Fault tolerance findings: N critical, N high
- Recoverability findings: N critical, N high

## Exception handling (maturity)
| File:line | Pattern | Severity | Recommendation |
|---|---|---|---|

## Fault tolerance
### External calls without timeout
| File:line | Call | Severity | Recommendation |
|---|---|---|---|

### Missing retry / circuit breaker
| Dependency | Call sites | Severity |
|---|---|---|

## Availability
| File:line | Issue (health/shutdown/SPOF) | Severity |
|---|---|---|

## Recoverability
### Transactions / idempotency
| File:line | Operation | Risk | Severity |
|---|---|---|---|

### Data durability
| File:line | Pattern | Severity |
|---|---|---|
```

## Example Usage

**Scenario 1: 25010 sweep**
```
/audit-sdlc reliability
```

**Scenario 2: Focus on a service boundary**
```
/audit-reliability --path src/payments
```

**Scenario 3: Before going multi-instance**
```
/audit-reliability
```
Surfaces the single-instance assumptions (hardcoded singletons, in-memory state) that break under horizontal scaling.

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| `audit-security`, `audit-functional-suitability`, `audit-performance-efficiency`, `audit-compatibility`, `audit-usability`, `audit-maintainability`, `audit-portability` | The other seven ISO/IEC 25010 characteristics. Compose via `/audit-sdlc`. |
| `audit-sdlc` | Coordinator. |
| `observe-production` | Runtime reliability (is it failing now?). This is design reliability. |
| `audit-observability` | Whether failures are instrumented. This is whether the system tolerates failure. |
| `audit-performance-efficiency` | Overlaps on missing timeouts/retries and unbounded growth; dedup between the two. |
| `create-observability` / `create-service-levels` | Design-time definition of reliability targets. |

## Useful Commands Reference

| Command | Description |
|---|---|
| `grep -rEnA2 "except\s*:\|except Exception:" --include="*.py" . \| grep "pass\|\.\.\."` | Swallowed exceptions |
| `grep -rEn "requests\.(get\|post)\(\|fetch\(" --include="*.py" --include="*.ts" . \| grep -v timeout` | External calls without timeout |
| `grep -rEn "/healthz\|/readyz\|actuator/health" .` | Health endpoints |
| `grep -rEn "atomic\|@Transactional\|with .*transaction\|ON CONFLICT"` | Transaction/idempotency markers |
