---
name: review-sdk-changes
description: "Review a change to a published client library or SDK (public symbols, signatures, types, errors, release versioning, packaging) for breaking changes and consumer ergonomics. Use when a PR, branch, or diff touches an SDK or client library and the user asks whether the change breaks consumers, whether the version bump is right, whether the public API is idiomatic, or wants an SDK-focused change review."
allowed-tools: Bash(git:*, gh:*, ghx:*, ~/.agents/scripts/should-post-to-github:*, ~/.agents/scripts/review-progress:*), Read, Write, Glob, Grep
argument-hint: "<pr-number> [repository] | <diff-ref | worktree-dir>"
---

# Review SDK Changes

Reviews a change to a published client library or SDK and reports findings.
It answers one question: **does this change treat the SDK's consumers well?**
Covering breaking changes to the public surface, versioning and release, ergonomics, type safety, error handling, configuration, pagination, packaging, dependencies, and documentation.

An SDK is consumed by code the author cannot change, so every public symbol is a contract.
The review is therefore biased toward compatibility: a change that is correct in isolation can still be a 🔴 MUST if it silently breaks a caller.
It is the change-time companion to [`/review-pr`](../review-pr/SKILL.md), which keeps general code craft, and to [`/review-api-changes`](../review-api-changes/SKILL.md), which reviews the wire contract the SDK wraps.

This review is static: it does not build or run the SDK, so behavior observed by running it is `/verify-pr`'s to prove.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for report location and posting rules).
- Apply the shared evidence standard in [`../sdlc/references/evidence.md`](../sdlc/references/evidence.md).
  Static claims carry `L1 - Cited` or `L2 - Ruled out`; a decisive claim proven by a read-only command can reach `L3 - Executed`.
- The change to review, in one of these forms:
  - a PR number plus repository (`/review-sdk-changes 42 acme/sdk-python`),
  - a git diff ref (for example `origin/main..HEAD`),
  - a worktree directory, or a changeset already in context.
- The public surface at the base revision, so before/after can be compared.
  Read it from the package entry point and its exports rather than from the diff alone.
- The SDK's packaging metadata (manifest, entry points, exports map, type declarations) and current version.
- The generated-code source when the SDK is generated (for example an OpenAPI spec), to check regeneration drift.

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `review-sdk-changes`.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Workflow

```
Resolve the change ($1: PR / diff-ref / worktree)
          |
          v
Read the base revision's PUBLIC SURFACE
(entry point, exports, signatures, types)
          |
          v
Classify the diff: public-surface hunks
vs internal hunks
          |
          v
Apply the Review Checklist (compat,
versioning, ergonomics, types, errors,
config, pagination, packaging, deps,
docs, tests)
          |
          v
Write review-sdk-changes.<sha>.md
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
Set `BASE_REF="origin/$BASE_BRANCH"` so the base surface can be read in step 2.
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
For a non-PR run, write to `/tmp/sdlc/${REPO:-review}/review-sdk-changes.$SHORT_SHA.md` (create that directory first) and skip posting.
Set `HEAD_TREE=$(git rev-parse "$HEAD_COMMIT^{tree}")` when it is not already set.

### 2. Read the base revision's public surface

The public surface is what a consumer imports and calls, not everything in the repository.
Read it at the base revision before reading the diff:

```bash
git ls-tree -r --name-only "$BASE_REF" | grep -E '(index|exports|__init__|public-api|api\.d\.ts|lib\.(rs|go))' || true
git show "$BASE_REF:src/index.ts"    # or the package entry point
```

Identify how the package marks what is public (an exports map, `__all__`, a public module, a `pub` keyword, a documented API reference), and treat only that as the contract.
Note the current version and how the project bumps it, so the proposed bump can be checked in step 4.

### 3. Classify the diff

Mark a hunk as public-surface when it changes any of:

- an exported symbol: its name, signature, overloads, visibility, or removal;
- a public type, interface, enum, or its members;
- a public method's default parameter value or behavior;
- a public error, exception, or result type;
- the client's constructor, configuration options, or their defaults;
- pagination, streaming, or retry behavior a caller observes;
- shipping metadata: entry points, exports map, type declarations, or package layout.

Internal hunks stay with `/review-pr`.

### 4. Apply the Review Checklist to each surface change

Publish the in-progress marker before walking the checklist when this is a PR run (skip it for a bare diff ref), and remove it before returning (see `sdlc/references/shared.md`, In-progress marker):

```bash
~/.agents/scripts/review-progress start --step review-sdk-changes --repo "$REPO" --pr "$PR_NUMBER" --sha "$HEAD_COMMIT"
```

Walk the categories below for every public-surface change.
Skip a category only when the diff cannot touch it, and say so.

### 5. Report findings

Give each finding:
- a severity: 🔴 MUST, 🟡 SHOULD, or 🟢 MAY;
- the category it maps to;
- an evidence level in the form `L<n> - <Name>` plus a `file:line`;
- a concrete, actionable fix, including the deprecation or migration path where one is needed.

### 6. Write the report and post it

Start the file with the marker so an orchestrator can detect which commit was reviewed:

```markdown
<!-- {"step":"review-sdk-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
```

Replace `HEAD_COMMIT`, `HEAD_TREE`, and `SHORT_SHA` with the resolved values (`SHORT_SHA` is the first 7 characters of `HEAD_COMMIT`).
`MARKER_VERDICT` is `pass` for `approved`, and `fail` for `changes-requested` or `rejected`.
Below the marker, start the report with the traffic-light header from `sdlc/references/shared.md` (Report header (traffic light)): the title, one overall go/no-go line, then one line per checklist category with its own light and a terse note.

Write the report to `$PR_REVIEW_DIR/review-sdk-changes.$SHORT_SHA.md` and point the stable symlink at it:

```bash
ln -sf "review-sdk-changes.$SHORT_SHA.md" "$PR_REVIEW_DIR/review-sdk-changes.report.md"
```

Posting as a PR comment is decided by `should-post-to-github`.
Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`; if it exits 1, skip posting (the report is saved locally).
If it exits 0, set `REPORT` to the report file's contents and `FOOTER` to the attribution footer, then post with the **Posting a review report** recipe in `skills/sdlc/references/shared.md` (`STEP="review-sdk-changes"`).

### 7. Clean up

For a PR run, remove the in-progress marker:

```bash
~/.agents/scripts/review-progress stop --step review-sdk-changes --repo "$REPO" --pr "$PR_NUMBER"
```

If this skill created a worktree (no `$WORKTREE_DIR` was provided), remove it.

## Review Checklist

### Breaking Compatibility

- Is any public symbol removed, renamed, or made non-public?
- Does any public signature change in a way existing callers cannot survive: a new required parameter, a reordered parameter, a narrowed type, or a changed return type?
- Has a public default changed (a timeout, a page size, a retry count, a base URL) in a way callers observe?
- Has an exception or error type changed, so existing `catch` blocks no longer match?
- Has a public type been made stricter (a field now required, an enum member removed, nullability narrowed), rejecting values callers already send?
- Does a removed capability have a deprecation window, a replacement named, and a stated removal version?

### Versioning & Release

- Does the change require a major bump under the project's versioning scheme (SemVer or the language's convention), and does the version in the manifest match the change?
- Is a breaking change documented with a migration note, a changelog entry, and a deprecation warning in code?
- Are deprecations marked in the language's way (`@deprecated`, a runtime warning, a doc annotation) with the removal version named?
- Do lockfiles and generated artifacts match the source, with no stale generated code left behind?
- Is the minimum supported language or runtime version still accurate?

### Public Surface & Ergonomics

- Does the new API read like the language it is written in (contexts, iterators, builders, async/await) rather than translating another language's style?
- Is a new method consistent with the naming and structure of its siblings on the client?
- Is the common case achievable in one call, without a required builder chain or ceremony?
- Is a new parameter added in a position that lets future optional parameters follow, or is it a one-way door?
- Does the change avoid exposing internals the SDK should own (a raw HTTP response where a typed object belongs, a transport detail, an internal type)?
- Is there one way to do a thing, rather than a second overlapping method added beside an existing one?

### Type Safety

- Does every public symbol have a declared type, with strict mode honored and no `any`, `interface{}`, or untyped dict leaking into the public surface?
- Are nullability and optionality accurate, so a consumer is not told a value is present when it can be absent?
- Are overloads or generics used where they remove casts, not as decoration?
- Do the shipped type declarations match the implementation (no declared type the code does not honor)?

### Error Handling & Resilience

- Are errors typed and catchable, with a distinguishable class per failure kind (validation, auth, rate limit, network, server)?
- Are retries, backoff, and jitter applied to retryable errors only, and never to non-idempotent calls without an idempotency key?
- Are timeouts and cancellation supported and given safe defaults?
- Does the client release resources (connections, streams, file handles) deterministically on error and on close (a context manager, `using`, `defer`, `Close()`)?
- Does an error carry what a caller needs to act (status, request id, the field that failed) without leaking secrets?

### Configuration & Construction

- Are client construction options documented and given defaults that work without configuration?
- Is authentication supplied through a token provider or refreshable credential, rather than a value captured once at construction?
- Is the base URL, region, or endpoint overridable for testing and for self-hosted deployments?
- Is environment-variable or config-file fallback defined, documented, and consistent with the wire client and the CLI?

### Pagination, Streaming & Concurrency

- Does a new list method paginate, and is auto-pagination offered (an iterator) alongside the raw page?
- Is streaming surfaced as a stream or iterator with clear completion and error signaling, not buffered whole?
- Is the client safe to share across threads or tasks, or is that documented and enforced?
- Are concurrent calls bounded, so the SDK cannot open unbounded connections?

### Packaging & Distribution

- Do the entry points, exports map, and package layout expose exactly the public surface, with nothing internal reachable by accident?
- Do type declarations ship with the package and resolve for a consumer of the published artifact?
- Is the module format correct for the ecosystem (ESM/CJS dual, a `main`/`module`/`types` triple, a correct `go.mod` module path, a correct crate name)?
- Has bundle size or install weight grown beyond what the change justifies, and is the new dependency tree-only where it should be?

### Dependencies

- Is each new dependency justified, and is it avoidable by a few lines already in the codebase?
- Is it pinned to a compatible range, and does it conflict with a version consumers may already have?
- Is its license compatible with the SDK's distribution terms?
- Does an upgrade of an existing dependency change runtime behavior for consumers (a changed default, a removed export)?

### Documentation & Tests

- Are new public symbols documented, with docstrings or reference entries, and do the examples compile against the current API?
- Does the README show the changed surface, and is a deprecation or migration note present for a breaking change?
- Is there a test for each new public behavior and each new error path?
- Is there a public-surface snapshot or contract test, so a future accidental break is caught?
- Is there a test that exercises the SDK against a mock or recorded server for the new call, not only a unit test of an internal helper?

## Output Format

```markdown
<!-- {"step":"review-sdk-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
# SDK Change Review: #<PR_NUMBER> <title> (or <diff-ref>)

**🔴 / 🟡 / 🟢 <No-go / Caution / Go>** — <one sentence: why, and what unblocks it.>

- 🔴 / 🟡 / 🟢 Breaking Compatibility — <terse note>
- 🔴 / 🟡 / 🟢 Versioning & Release — <terse note>
- 🔴 / 🟡 / 🟢 Public Surface & Ergonomics — <terse note>
- 🔴 / 🟡 / 🟢 Type Safety — <terse note>
- 🔴 / 🟡 / 🟢 Error Handling & Resilience — <terse note>
- 🔴 / 🟡 / 🟢 Configuration & Construction — <terse note>
- 🔴 / 🟡 / 🟢 Pagination, Streaming & Concurrency — <terse note>
- 🔴 / 🟡 / 🟢 Packaging & Distribution — <terse note>
- 🔴 / 🟡 / 🟢 Dependencies — <terse note>
- 🔴 / 🟡 / 🟢 Documentation & Tests — <terse note>

Reviewed commit: `SHORT_SHA`
Base: `<BASE_BRANCH or base ref>` · Version: `<current>` -> `<proposed>`

## Summary

<What the SDK change does, and the headline compatibility or ergonomics risk.>

## Public surface changes

| Public symbol | Before | After | Breaking? | Consumer affected |
|---|---|---|---|---|
| `Client.create_charge` (`src/client.py:88`) | `create_charge(amount)` | `create_charge(amount, currency)` | Yes | every caller |
| `--timeout` default (`src/client.py:30`) | 10s | 30s | Conditional | callers relying on a fast failure |

## Findings

### 🔴 MUST / Breaking Compatibility / <title>

<What breaks, the concrete fix or deprecation path, and the evidence pointer.>

`Evidence: L2 - Ruled out` (`src/client.py:88`; base `<BASE_REF>:src/client.py:84`).

### 🟡 SHOULD / <Category> / <title>

<...>

## Outcome

<One sentence: what must change before the SDK change ships, and whether a major bump is required.>
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | Light | When | Marker verdict |
|---|---|---|---|
| `approved` | 🟢 Go | No blocking findings and no findings at all; the SDK change passes review | `pass` |
| `approved` | 🟡 Caution | No blocking findings, but SHOULD or MAY findings remain | `pass` |
| `changes-requested` | 🔴 No-go | Findings the author must address before it passes | `fail` |
| `rejected` | 🔴 No-go | Fundamental flaw requiring rework or stopping | `fail` |

In the same emission, list the findings file under `artifacts:` (the report path written in step 6).

## Failure Modes

| Mode | Response |
|---|---|
| **Worktree creation fails** | Stop |
| **PR is CLOSED or MERGED** | Note it and stop |
| **No public surface change in the diff** | Say so plainly and stop; the change belongs to `/review-pr` |
| **Base revision unavailable** | Review the surface on its own and mark compatibility findings `unproven`, naming the base comparison that was missing |
| **Generated SDK** | Check the change against its generator input; a hand edit to generated code is itself a finding |
| **`ghx` unavailable** | Fall back to `gh pr view` for PR context |

## Example Usage

**Scenario 1: New required parameter**
```
/review-sdk-changes 42 acme/sdk-python
```
`create_charge(amount)` becomes `create_charge(amount, currency)` on a released minor version.
Report a 🔴 MUST under Breaking Compatibility and Versioning: give `currency` a default and ship a major bump, or add an overload.

**Scenario 2: Error type change**
```
/review-sdk-changes origin/main..HEAD
```
A network failure that used to raise `RequestError` now raises `ConnectionError`, caught nowhere in consumer code.
Report a 🔴 MUST under Breaking Compatibility, with a migration note.

**Scenario 3: Untyped return**
```
/review-sdk-changes 88 acme/sdk-ts
```
A new public method returns `Promise<any>`.
Report a 🟡 SHOULD under Type Safety: declare the concrete response type.

**Scenario 4: Additive, well-packaged change**
```
/review-sdk-changes 55 acme/sdk-go
```
The diff adds an optional page-size option with a safe default, a docstring, an entry in the README, and a contract test.
Report 🟢 approved with no findings.

## Related Skills

| Skill | Relationship |
|---|---|
| `review-api-changes` | Reviews the wire contract the SDK wraps; this skill reviews the client surface consumers call |
| `review-pr` | General code-craft review; this skill is the public-surface specialization and defers internal hunks to it |
| `review-cli-changes` | Sibling surface review for a command-line interface |
| `verify-pr` | Proves criteria by building and running the SDK; this review is static |
| `audit-compatibility` | Repo-wide co-existence and interoperability audit; this skill is diff-focused |
