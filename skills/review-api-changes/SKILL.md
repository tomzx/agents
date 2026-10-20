---
name: review-api-changes
description: "Review a change to an HTTP or RPC API contract (endpoints, request and response fields, status codes, auth, pagination, versioning) for breaking changes and consumer compatibility. Use when a PR, branch, or diff touches API routes, an OpenAPI or proto schema, or a public interface and the user asks whether the change is breaking, whether it is versioned correctly, or wants an API-focused change review."
allowed-tools: Bash(git:*, gh:*, ghx:*, python:*, python3:*, ~/.agents/scripts/should-post-to-github:*, ~/.agents/scripts/review-progress:*), Read, Write, Glob, Grep
argument-hint: "<pr-number> [repository] | <diff-ref | worktree-dir>"
---

# Review API Changes

Reviews a change to an API contract and reports findings.
It answers one question: **will this change break an existing consumer, and if so is that handled?**
Covering breaking-change detection, additive compatibility, versioning and deprecation, resource and method semantics, status codes and error bodies, pagination, auth and rate limits, idempotency, and schema-to-code drift.

The contract is what a consumer compiles against or calls over the wire.
A field type change, a new required parameter, or a removed enum value is a breaking change even when the handler is correct.
It is the change-time companion to [`/review-pr`](../review-pr/SKILL.md), which keeps general code craft, and to [`/review-sdk-changes`](../review-sdk-changes/SKILL.md), which reviews the client library wrapping the contract.

This review is static: it does not call the API, so behavior observed against a running service is `/verify-pr`'s to prove.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for report location and posting rules).
- Apply the shared evidence standard in [`../sdlc/references/evidence.md`](../sdlc/references/evidence.md).
  Static claims carry `L1 - Cited` or `L2 - Ruled out`; a decisive claim proven by a read-only command (for example diffing two schema files) can reach `L3 - Executed`.
- The change to review, in one of these forms:
  - a PR number plus repository (`/review-api-changes 42 acme/api`),
  - a git diff ref (for example `origin/main..HEAD`),
  - a worktree directory, or a changeset already in context.
- The contract at the base revision, so before/after can be compared: the route definitions, the OpenAPI or proto schema, the serializers, and the validation rules.
- The published schema file when the project keeps one, to check schema-to-code drift.
- `.sdlc/features/N-<slug>/specifications.md` when one exists (optional; used for contract-vs-spec checks).

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `review-api-changes`.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Workflow

```
Resolve the change ($1: PR / diff-ref / worktree)
          |
          v
Read the BASE contract
(routes, schema, serializers, validation)
          |
          v
Classify the diff: contract-surface hunks
vs handler-internal hunks
          |
          v
Apply the Review Checklist (breaking
changes, additive compat, versioning,
semantics, status codes, pagination,
auth, idempotency, drift, docs, tests)
          |
          v
Write review-api-changes.<sha>.md
(marker + verdict)
Post if should-post-to-github allows
          |
          v
Clean up worktree (only if owned)
```

## Steps

### 1. Resolve the change

If a PR number is given, fetch its metadata and diff:

```bash
PR_NUMBER="$1"; REPO="$2"
ghx pr view $PR_NUMBER --repo "$REPO" --comments --refresh
gh pr view $PR_NUMBER --repo "$REPO" --json headRefOid,headRefName,headRepository,baseRefName,files,title,body
gh pr diff $PR_NUMBER --repo "$REPO"
```

Extract `HEAD_COMMIT` (`headRefOid`), `SHORT_SHA` (the first 7 characters of `HEAD_COMMIT`), `HEAD_REPO`, `HEAD_BRANCH`, `BASE_BRANCH`, `PR_AUTHOR`, and `PR_STATE`.
Set `BASE_REF="origin/$BASE_BRANCH"` so the base contract can be read in step 2.
If `PR_STATE` is `CLOSED` or `MERGED`, note it and stop.

Create a worktree on the PR branch so the changed files can be read in full, not only as diff hunks.
If `$WORKTREE_DIR` is already set (for example by an orchestrator), use it directly and skip creation and cleanup.

```bash
_WORKTREE_OWNER=false
if [ -z "${WORKTREE_DIR:-}" ]; then
  git fetch "https://github.com/$HEAD_REPO.git" "$HEAD_BRANCH"
  WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
  mkdir -p /tmp/sdlc/$REPO
  git worktree add "$WORKTREE_DIR" FETCH_HEAD
  _WORKTREE_OWNER=true
fi
cd "$WORKTREE_DIR" || exit 1
```

If worktree creation fails, stop.

If a diff ref or worktree directory is given instead of a PR number, use it directly and derive the commit identity:

```bash
DIFF_REF="${1:-origin/main..HEAD}"
BASE_REF="${DIFF_REF%%..*}"   # the part before ..
[ -n "${WORKTREE_DIR:-}" ] && cd "$WORKTREE_DIR"
HEAD_COMMIT=$(git rev-parse HEAD)
SHORT_SHA="${HEAD_COMMIT:0:7}"
HEAD_TREE=$(git rev-parse "$HEAD_COMMIT^{tree}")
git diff --name-only "$DIFF_REF"
git diff "$DIFF_REF"
```

Define the report directory once: `PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"`, then `mkdir -p "$PR_REVIEW_DIR"`.
For a non-PR run, write to `/tmp/sdlc/${REPO:-review}/review-api-changes.$SHORT_SHA.md` (create that directory first) and skip posting.
Set `HEAD_TREE=$(git rev-parse "$HEAD_COMMIT^{tree}")` when it is not already set.

### 2. Read the base revision's contract

Compatibility is measured against the previous contract, so read it before the diff:

```bash
# Published schema, if the project keeps one
git ls-tree -r --name-only "$BASE_REF" | grep -Ei '(openapi|swagger|\.proto$|graphql|schema\.(json|ya?ml))' || true
git diff "$BASE_REF"..HEAD -- '*openapi*' '*swagger*' '*.proto' '*.graphql' 2>/dev/null || true
# Routes and serializers
git show "$BASE_REF:src/api/routes.py"
```

When a published schema exists, comparing the two revisions of the schema is a read-only `L3 - Executed` proof of the contract delta:

```bash
git show "$BASE_REF:openapi.json" > /tmp/opencode/api-base.json
git show "HEAD:openapi.json" > /tmp/opencode/api-head.json
python3 -c "import json,sys; a=json.load(open('/tmp/opencode/api-base.json')); b=json.load(open('/tmp/opencode/api-head.json')); print('paths added', sorted(set(b['paths'])-set(a['paths']))); print('paths removed', sorted(set(a['paths'])-set(b['paths'])))"
```

Identify how this project carries the version (path prefix, header, schema field) and what it counts as a breaking change, so step 4 can check the change against that policy.

### 3. Classify the diff

Mark a hunk as contract-surface when it changes any of:

- a route or RPC method: its path, verb, presence, or visibility;
- a request or response field: name, type, required/optional, default, or nesting;
- an enum and its members, or a union member;
- a status code, content type, or redirect for an existing condition;
- a validation rule, so input previously accepted is now rejected;
- pagination, filtering, or sorting parameters and their defaults;
- auth requirements, scopes, or rate limits on an endpoint;
- the error envelope, its fields, or its codes;
- a webhook or event payload.

Handler-internal hunks stay with `/review-pr`.

### 4. Apply the Review Checklist to each surface change

Publish the in-progress marker before walking the checklist when this is a PR run (skip it for a bare diff ref), and remove it before returning (see `sdlc/references/shared.md`, In-progress marker):

```bash
~/.agents/scripts/review-progress start --step review-api-changes --repo "$REPO" --pr "$PR_NUMBER" --sha "$HEAD_COMMIT"
```

Walk the categories below for every contract change.
Skip a category only when the diff cannot touch it, and say so.

### 5. Report findings

Give each finding:
- a severity: 🔴 MUST, 🟡 SHOULD, or 🟢 MAY;
- the category it maps to;
- an evidence level in the form `L<n> - <Name>` plus a `file:line` or schema pointer;
- a concrete, actionable fix, naming the version bump, deprecation, or migration path where one is needed.

### 6. Write the report and post it

Start the file with the marker so an orchestrator can detect which commit was reviewed:

```markdown
<!-- {"step":"review-api-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
```

Replace `HEAD_COMMIT`, `HEAD_TREE`, and `SHORT_SHA` with the resolved values (`SHORT_SHA` is the first 7 characters of `HEAD_COMMIT`).
`MARKER_VERDICT` is `pass` for `approved`, and `fail` for `changes-requested` or `rejected`.

Write the report to `$PR_REVIEW_DIR/review-api-changes.$SHORT_SHA.md` and point the stable symlink at it:

```bash
ln -sf "review-api-changes.$SHORT_SHA.md" "$PR_REVIEW_DIR/review-api-changes.report.md"
```

Posting as a PR comment is decided by `should-post-to-github`.
Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`; if it exits 1, skip posting (the report is saved locally).
If it exits 0, set `REPORT` to the report file's contents and `FOOTER` to the attribution footer, then post with the **Posting a review report** recipe in `skills/sdlc/references/shared.md` (`STEP="review-api-changes"`).

### 7. Clean up

For a PR run, remove the in-progress marker:

```bash
~/.agents/scripts/review-progress stop --step review-api-changes --repo "$REPO" --pr "$PR_NUMBER"
```

If this skill created a worktree (no `$WORKTREE_DIR` was provided), remove it.

## Review Checklist

### Breaking Changes

- Is any endpoint or RPC method removed, renamed, or moved to a different path?
- Is any request or response field removed or renamed?
- Has any field's type changed (int to string, scalar to object, single to array)?
- Has any field become required, or has a new required request parameter been added?
- Has an enum member been removed, or a union member dropped?
- Has the status code or content type for an existing scenario changed?
- Has validation become stricter, rejecting input that used to be accepted?
- Has a default changed that a consumer observes (page size, sort order, time zone, a server-set value)?
- Is each of these handled by a new version, a deprecation window, or an additive alternative?

### Additive Compatibility

- Are new response fields optional and ignored by existing clients, with unknown-field tolerance on both sides?
- Are enums declared open where new members may be added without a version bump, and does each client tolerate an unknown member?
- Are new request parameters optional, with a default that preserves the old behavior?
- Is a new required field avoided, or gated behind a version so old callers keep working?
- Does property order, an opaque identifier format, or message text get relied upon, when it should be declared non-contractual?

### Versioning & Deprecation

- Is a version scheme present and applied consistently (path prefix, header, schema field)?
- Does a breaking change ship under a new version rather than into the current one?
- Is the old version deprecated with a stated sunset date, and does it keep serving until then?
- Are deprecation and sunset communicated in the standard way (RFC 9745 `Deprecation` and RFC 8594 `Sunset` headers, plus a changelog entry)?
- Is the number of concurrently served versions bounded, so maintenance does not accumulate?
- Is a removed version's removal announced, with a migration path and a contact for stragglers?

### Resource & Method Semantics

- Does each new endpoint use the right HTTP method for its semantics (GET safe and idempotent, PUT replace, PATCH partial, DELETE idempotent)?
- Are action endpoints that cannot be modeled as a resource documented as such, rather than smuggled into a GET?
- Are collection and item routes consistent with the rest of the surface (plural nouns, nesting depth, no verbs in paths)?
- Is a batch or bulk operation defined with per-item success and failure reporting, not all-or-nothing opacity?

### Status Codes & Errors

- Is a correct status code returned for success and for each failure (201 for create, 404 for missing, 409 for conflict, 422 for validation)?
- Is the error body consistent across endpoints: a stable code, a human message, and the offending field?
- Is a failure ever returned as `200` with an error field, or as `500` for a client error?
- Are `Retry-After` and rate-limit headers sent where the client needs them?
- Does the error body avoid leaking internals (stack traces, SQL, secrets) while still naming what to fix?

### Pagination, Filtering & Sorting

- Do new list endpoints paginate, with a bounded maximum page size?
- Is the page order stable and documented, so paging cannot skip or duplicate rows?
- Is cursor pagination used where the data changes under the cursor, and offset only for small or stable sets?
- Are filters and sorts validated against an allowlist, rather than passed through to the query?
- Is an unknown filter or sort key rejected with a clear error, not silently ignored?

### Auth, Limits & Safety

- Does every new endpoint apply authentication and authorization, with the right scope or role?
- Can a caller reach another tenant's or another user's data through, for example, an object id parameter (an insecure direct object reference)?
- Is input validated and parameterized, with no injection path through a filter, sort, or identifier?
- Is a rate limit or quota applied to an expensive or abusable new endpoint?
- Is sensitive data kept out of responses, URLs (which are logged), and error bodies (no PII, no tokens, no card data)?
- Is a mass-assignment path closed, so a client cannot set a server-owned field?

### Idempotency & Retries

- Is a non-idempotent create protected by an idempotency key, so a retry does not double-apply?
- Does a retried request produce the same result, or a clearly reported conflict?
- Is a long-running operation surfaced as a job with a pollable status, rather than a request that times out mid-work?

### Compatibility with Callers in Flight

- Can the previous API version still serve while clients migrate (old clients plus a new deployment)?
- Can new clients against the previous deployment tolerate the added fields and behavior?
- Is the deploy order safe when the contract change and the client change ship separately?

### Schema Drift & Documentation

- Does the published schema (OpenAPI, proto, GraphQL SDL) match the implemented routes and fields, with no drift in either direction?
- Is the schema change itself reviewed, not only the handler diff?
- Are examples in the schema valid against the new contract?
- Is the changelog updated, and is a breaking change called out with its version and migration steps?

### Tests

- Is there a contract test that asserts the request and response field layout for each changed endpoint?
- Is there a schema snapshot or compatibility test that fails when a documented field is removed or retyped?
- Are the new error paths and validation rules tested, not only the happy path?
- Is an old-version request tested against the new code, to prove the version split holds?

## Output Format

```markdown
<!-- {"step":"review-api-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
# API Change Review: #<PR_NUMBER> <title> (or <diff-ref>)

🔴 / 🟢 <Overall assessment in one sentence.>

Reviewed commit: `SHORT_SHA`
Base: `<BASE_BRANCH or base ref>` · Version scheme: `<path | header | none>`

## Summary

<What the API change does, and the headline compatibility risk.>

## Contract changes

| Surface | Before | After | Breaking? | Consumer affected |
|---|---|---|---|---|
| `POST /payments` request (`openapi.json:210`) | `amount` only | adds required `currency` | Yes | every client |
| `GET /users` page size default (`src/api/routes.py:44`) | 50 | 20 | Conditional | clients relying on a full page |

## Findings

### 🔴 MUST / Breaking Changes / <title>

<What breaks, the concrete fix (new version, optional parameter, deprecation), and the evidence pointer.>

`Evidence: L3 - Executed` (`/tmp/opencode/api-base.json` vs `HEAD:openapi.json`; `currency` now in `required`).

### 🟡 SHOULD / <Category> / <title>

<...>

## Checklist

| Category | Status | Notes |
|---|---|---|
| Breaking Changes | 🔴 / 🟡 / 🟢 | <terse note> |
| Additive Compatibility | 🟢 | <terse note> |
| Versioning & Deprecation | 🟢 | <terse note> |
| Resource & Method Semantics | 🟢 | <terse note> |
| Status Codes & Errors | 🟢 | <terse note> |
| Pagination, Filtering & Sorting | 🟢 | <terse note> |
| Auth, Limits & Safety | 🟢 | <terse note> |
| Idempotency & Retries | 🟢 | <terse note> |
| Compatibility with Callers in Flight | 🟢 | <terse note> |
| Schema Drift & Documentation | 🟢 | <terse note> |
| Tests | 🟢 | <terse note> |

## Outcome

<One sentence: what must change before the API change ships, and whether a version bump is required.>
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When | Marker verdict |
|---|---|---|
| `approved` | No blocking findings; the API change passes review | `pass` |
| `changes-requested` | Findings the author must address before it passes | `fail` |
| `rejected` | Fundamental flaw requiring rework or stopping | `fail` |

In the same emission, list the findings file under `artifacts:` (the report path written in step 6).

## Failure Modes

| Mode | Response |
|---|---|
| **Worktree creation fails** | Stop |
| **PR is CLOSED or MERGED** | Note it and stop |
| **No contract change in the diff** | Say so plainly and stop; the change belongs to `/review-pr` |
| **No published schema** | Reconstruct the contract from routes, serializers, and validation, and note that drift checks were limited |
| **Base revision unavailable** | Review the contract on its own and mark compatibility findings `unproven`, naming the base comparison that was missing |
| **`ghx` unavailable** | Fall back to `gh pr view` for PR context |

## Example Usage

**Scenario 1: New required field**
```
/review-api-changes 42 acme/api
```
`POST /payments` gains a required `currency` field with no version bump.
Report a 🔴 MUST under Breaking Changes and Versioning: make it optional with a default, or ship it under `/v2`.

**Scenario 2: Enum member removed**
```
/review-api-changes origin/main..HEAD
```
`Status` loses the `PENDING` member clients may receive.
Report a 🔴 MUST under Breaking Changes: keep the member, or add a version and a migration note.

**Scenario 3: Unvalidated sort parameter**
```
/review-api-changes 88 acme/api
```
A new `?sort=` parameter is passed straight to the query builder.
Report a 🔴 MUST under Auth, Limits & Safety (injection), and a 🟡 under Pagination for the missing allowlist.

**Scenario 4: Clean additive change**
```
/review-api-changes 55 acme/api
```
The diff adds an optional `?include_deleted=` filter defaulting to today's behavior, documented in the schema, with a contract test.
Report 🟢 approved with no findings.

## Related Skills

| Skill | Relationship |
|---|---|
| `review-sdk-changes` | Reviews the client library that wraps this contract; this skill reviews the wire contract itself |
| `review-pr` | General code-craft review; this skill is the contract specialization and defers handler-internal hunks to it |
| `review-specifications` | Reviews the specification artifact; this skill reviews the implemented contract change |
| `verify-pr` | Proves criteria by calling the API; this review is static |
| `audit-compatibility` | Repo-wide interoperability and API-versioning audit; this skill is diff-focused |
