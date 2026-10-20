---
name: review-db-changes
description: "Review a database change (schema migration, index or constraint, data backfill, destructive statement) for lock safety, reversibility, data integrity, and zero-downtime deploy compatibility. Use when a PR, branch, or diff touches migrations, schema files, or data-changing SQL and the user asks whether the migration is safe, whether it locks a table, whether it is reversible, or wants a database-focused change review."
allowed-tools: Bash(git:*, gh:*, ghx:*, rg:*, ~/.agents/scripts/should-post-to-github:*, ~/.agents/scripts/review-progress:*), Read, Write, Glob, Grep
argument-hint: "<pr-number> [repository] | <diff-ref | worktree-dir>"
---

# Review Database Changes

Reviews a database change and reports findings.
It answers one question: **is this migration safe to run against production data?**
Covering lock behavior, reversibility, data-integrity constraints, backwards compatibility during rollout, data-change safety, index coverage, and destructive-statement guards.

A schema change that runs in milliseconds on an empty test database can take an exclusive lock on a large production table and stall every read and write behind it.
Likewise a data change computed from a query can match far more rows than intended.
This review checks for those failure paths before the migration runs.
It is the change-time companion to [`/review-pr`](../review-pr/SKILL.md), which keeps general code craft, and to [`/review-api-changes`](../review-api-changes/SKILL.md), which reviews the contract above the data.

This review is static: it does not run the migration, so behavior observed against a live database is `/verify-pr`'s to prove.
Never run a destructive migration to review it, and never against a database whose contents matter.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for report location and posting rules).
- Apply the shared evidence standard in [`../sdlc/references/evidence.md`](../sdlc/references/evidence.md).
  Static claims carry `L1 - Cited` or `L2 - Ruled out`; a decisive claim proven by a read-only command (for example rendering the migration to SQL) can reach `L3 - Executed`.
- The change to review, in one of these forms:
  - a PR number plus repository (`/review-db-changes 42 acme/api`),
  - a git diff ref (for example `origin/main..HEAD`),
  - a worktree directory, or a changeset already in context.
- The migration files at the base revision, so the applied schema can be compared.
- The database engine and version, and whether the target table is large or hot (from the PR description, an existing migration, or a table-size note).
- The ORM models or schema definition files, so drift between models and migrations can be checked.
- `.sdlc/features/N-<slug>/lifecycle.md` when one exists (optional; used for retention and state checks).

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `review-db-changes`.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Workflow

```
Resolve the change ($1: PR / diff-ref / worktree)
          |
          v
Identify the engine, version, and
whether the target table is large/hot
          |
          v
Read the migration at BASE and HEAD
(schema before, schema after)
          |
          v
Classify the diff: schema, data,
and destructive changes
          |
          v
Apply the Review Checklist (locks,
reversibility, backfill, constraints,
indexes, deploy order, destructive
guards, tests, backups)
          |
          v
Write review-db-changes.<sha>.md
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
Set `BASE_REF="origin/$BASE_BRANCH"` so the base schema can be read in step 3.
If `PR_STATE` is `CLOSED` or `MERGED`, note it and stop.

Create a worktree on the PR branch so the migration and model files can be read in full, not only as diff hunks.
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
For a non-PR run, write to `/tmp/sdlc/${REPO:-review}/review-db-changes.$SHORT_SHA.md` (create that directory first) and skip posting.
Set `HEAD_TREE=$(git rev-parse "$HEAD_COMMIT^{tree}")` when it is not already set.

### 2. Identify the engine, version, and target size

Lock behavior and safe patterns differ by engine (PostgreSQL, MySQL, SQLite, SQL Server) and version.
Determine the engine and version from the migration framework, connection config, or CI, and state them in the report; a pattern that is safe on one engine is a lock on another.

Establish whether each affected table is large or hot.
A migration that is fine on a small table can be a production incident on a large one; when size is unknown, treat the table as large and mark the lock claim `unproven`.

```bash
rg -n "postgres|mysql|sqlite|mssql|alembic|knex|flyway|golang-migrate|sequelize|django" -g '*.{py,ts,js,go,rs,rb,sql,toml,ya?ml}' .
```

### 3. Read the migration at base and head

Reconstruct the schema before and after, and read the migration as the engine would execute it:

```bash
git diff "$BASE_REF"..HEAD -- '*/migrations/*' '*.sql' '**/schema*'
```

When the framework can render SQL without applying it (read-only), that render is an `L3 - Executed` artifact:

```bash
alembic upgrade head --sql          # or: sqlmigrate, migrate --dry-run, django sqlmigrate
```

Never run `upgrade` in earnest, and never against a database whose contents matter.

### 4. Classify the diff

Mark a hunk as a schema change, a data change, or a destructive change, because each has its own checks:

- **Schema change**: create or drop table or column, alter type, add or drop a constraint, add or drop an index, rename a column or table.
- **Data change**: an `UPDATE`, `INSERT ... SELECT`, backfill, or a migration that reads rows to compute new values.
- **Destructive change**: `DROP`, `TRUNCATE`, `DELETE`, a column drop, or an irreversible type narrowing.

### 5. Apply the Review Checklist to each change

Publish the in-progress marker before walking the checklist when this is a PR run (skip it for a bare diff ref), and remove it before returning (see `sdlc/references/shared.md`, In-progress marker):

```bash
~/.agents/scripts/review-progress start --step review-db-changes --repo "$REPO" --pr "$PR_NUMBER" --sha "$HEAD_COMMIT"
```

Walk the categories below for every change.
Skip a category only when the diff cannot touch it, and say so.

### 6. Report findings

Give each finding:
- a severity: 🔴 MUST, 🟡 SHOULD, or 🟢 MAY;
- the category it maps to;
- an evidence level in the form `L<n> - <Name>` plus a `file:line`;
- a concrete, actionable fix, naming the safe pattern for the engine.

### 7. Write the report and post it

Start the file with the marker so an orchestrator can detect which commit was reviewed:

```markdown
<!-- {"step":"review-db-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
```

Replace `HEAD_COMMIT`, `HEAD_TREE`, and `SHORT_SHA` with the resolved values (`SHORT_SHA` is the first 7 characters of `HEAD_COMMIT`).
`MARKER_VERDICT` is `pass` for `approved`, and `fail` for `changes-requested` or `rejected`.

Write the report to `$PR_REVIEW_DIR/review-db-changes.$SHORT_SHA.md` and point the stable symlink at it:

```bash
ln -sf "review-db-changes.$SHORT_SHA.md" "$PR_REVIEW_DIR/review-db-changes.report.md"
```

Posting as a PR comment is decided by `should-post-to-github`.
Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`; if it exits 1, skip posting (the report is saved locally).
If it exits 0, set `REPORT` to the report file's contents and `FOOTER` to the attribution footer, then post with the **Posting a review report** recipe in `skills/sdlc/references/shared.md` (`STEP="review-db-changes"`).

### 8. Clean up

For a PR run, remove the in-progress marker:

```bash
~/.agents/scripts/review-progress stop --step review-db-changes --repo "$REPO" --pr "$PR_NUMBER"
```

If this skill created a worktree (no `$WORKTREE_DIR` was provided), remove it.

## Review Checklist

### Lock Safety

- Is an index created or dropped concurrently (for example PostgreSQL `CREATE INDEX CONCURRENTLY` inside an autocommit block), rather than under a table lock?
- Does a unique constraint get added as a concurrent unique index first, then attached with an existing index, instead of locking the table for a full scan?
- Is a foreign key added as `NOT VALID` first and validated in a separate step, so neither table is locked during validation?
- Is a `CHECK` constraint added `NOT VALID` first and validated separately?
- Does a column type change avoid a full table rewrite, or is it done multi-step (add a new column, backfill, swap) when a rewrite would lock the table?
- Is a `NOT NULL` column added with a safe default on the engine version in use, rather than one that rewrites the table?
- Does a column addition carry a volatile default, or a default that forces a rewrite?
- Are `lock_timeout` and `statement_timeout` set, so a migration that cannot take its lock fails fast instead of blocking traffic indefinitely?
- Is a destructive or long step split into its own migration, so a failure mid-step does not leave a transaction holding locks?

### Reversibility

- Does each migration have a `downgrade()` (or down script) that actually reverses the change?
- Is a data-losing downgrade flagged, with its data loss named, rather than silently dropping the new data?
- Is a one-way door (a dropped column, a narrowed type, a data transform) called out explicitly with its rollback path?
- Is the rollback path documented and tested, not assumed, and does it account for rows written since the upgrade?
- Is the migration reversible without a downtime window, or does the rollback itself require one?

### Data Changes & Backfill

- Is the backfill idempotent, so re-running it after a partial failure is safe?
- Is a large backfill batched, rather than one statement that updates every row in a single transaction?
- Is the backfill separated from the schema change, so a failed backfill does not roll back the schema?
- For a backfill that computes a cutoff (a timestamp, an id, a filter), is the cutoff proven non-empty?
  A cutoff computed from a query can come back empty, and a predicate such as `where ts >= ''` then matches every row; assert the cutoff is non-empty and the affected row count is what was intended, before running the statement.
- Is the affected row count confirmed against an expectation before the change is committed, so an over-broad `DELETE` or `UPDATE` is caught before it runs?
- Does a release-sensitive migration avoid depending on application code that is changing in the same deploy?

### Constraints & Integrity

- Are new `NOT NULL`, `UNIQUE`, `CHECK`, and foreign-key constraints added, and do existing rows satisfy them (is the data clean, and is the validation step present)?
- Is a foreign key's `ON DELETE` behavior chosen deliberately (restrict, cascade, set null), rather than left at a default that orphans or over-deletes?
- Is a uniqueness constraint enforced in the database, not only in application code that races?
- Does an enum or type change keep existing values valid, and does it avoid removing a value still present in data?
- Is a nullable column added where a value may legitimately be absent, rather than a placeholder default that hides missing data?

### Indexes & Performance

- Does every new query pattern introduced by the change have a supporting index (a new `WHERE`, `JOIN`, or `ORDER BY` column)?
- Is a composite index's column order chosen for the query (equality columns before range columns), rather than in table order?
- Is a new index redundant with an existing one that already covers the query (an index on `(a)` covered by `(a, b)`)?
- Is a non-unique index kept to a small column count, so it is not a wide, write-amplifying index?
- Is a created index `CONCURRENTLY` and a dropped index likewise, so writes are not blocked?
- Does a new index on a large table account for the disk and write cost it adds?
- Is an index that is no longer used dropped, alongside the query change that made it redundant?

### Deploy Order & Zero-Downtime

- Does the expand-contract pattern hold: schema expanded first, code deployed, old schema contracted later?
- Can the previous application version run against the new schema (old code plus new columns, old code plus new nullable constraints)?
- Can the new application version run against the previous schema during a rolling deploy (new code plus columns that do not exist yet)?
- Is a column rename done via a new column plus dual-write plus a later drop, rather than a rename that breaks old code mid-deploy?
- Is a column drop deferred until no deployed version reads it, with that condition stated?

### Destructive-Change Guards

- Is a `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, or `DELETE` guarded by a confirmation, a backup, or a documented point of no return?
- Does a `DELETE` carry a `WHERE` clause that cannot match everything, with the non-empty cutoff and row count checked before running?
- Is the file copied before rows are deleted from a local or non-regenerable database (`cp db db.bak`), since the database has no other copy and `DELETE` overwrites the row pages?
- Is a column drop preceded by a period where the column is unused, so a stale reader is not broken?
- Is the affected data recoverable if the statement runs against the wrong database, and is the target environment explicit in the migration or its runbook?

### Testing

- Is there a migration test that applies the migration to a representative schema and dataset, including the up-and-down path?
- Is the data backfill tested on data with the edge cases (nulls, already-migrated rows, a large batch boundary)?
- Does CI apply migrations from scratch and on top of an existing schema, so both the fresh and the upgrade path are exercised?
- Is the destructive or over-broad statement covered by a test that asserts the affected row count?
- Are tests run against the same engine and version as production, so a lock or syntax difference is caught?

### Model Drift & Documentation

- Do the ORM models or schema definition files match the migration, with no drift in either direction?
- Is each migration a single logical change, named and ordered so the intent is clear from the filename?
- Is a migration added for a model change, rather than relying on an auto-create that will not run in production?
- Is the downtime or lock impact noted for operators, with the expected duration on the current table size?

## Output Format

```markdown
<!-- {"step":"review-db-changes","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"MARKER_VERDICT"} -->
# Database Change Review: #<PR_NUMBER> <title> (or <diff-ref>)

🔴 / 🟢 <Overall assessment in one sentence.>

Reviewed commit: `SHORT_SHA`
Base: `<BASE_BRANCH or base ref>` · Engine: `<engine version>` · Tables: `<name, estimated size>`

## Summary

<What the migration does, and the headline lock, data-safety, or reversibility risk.>

## Changes

| Change | Table / object | Type | Reversible? | Risk |
|---|---|---|---|---|
| `CREATE INDEX` (`migrations/003_add_idx.py:12`) | `users` | schema | Yes | full table scan, blocks writes |
| `UPDATE ... WHERE` (`migrations/003_add_idx.py:30`) | `users` | data | Partial | cutoff may match all rows |

## Findings

### 🔴 MUST / Lock Safety / <title>

<The lock or data risk, the safe pattern for this engine, and the evidence pointer.>

`Evidence: L1 - Cited` (`migrations/003_add_idx.py:12`; no `postgresql_concurrently`).

### 🟡 SHOULD / <Category> / <title>

<...>

## Checklist

| Category | Status | Notes |
|---|---|---|
| Lock Safety | 🔴 / 🟡 / 🟢 | <terse note> |
| Reversibility | 🟢 | <terse note> |
| Data Changes & Backfill | 🟢 | <terse note> |
| Constraints & Integrity | 🟢 | <terse note> |
| Indexes & Performance | 🟢 | <terse note> |
| Deploy Order & Zero-Downtime | 🟢 | <terse note> |
| Destructive-Change Guards | 🟢 | <terse note> |
| Testing | 🟢 | <terse note> |
| Model Drift & Documentation | 🟢 | <terse note> |

## Outcome

<One sentence: what must change before the migration runs, and whether a backup or downtime window is required.>
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When | Marker verdict |
|---|---|---|
| `approved` | No blocking findings; the migration passes review | `pass` |
| `changes-requested` | Findings the author must address before it passes | `fail` |
| `rejected` | Fundamental flaw requiring rework or stopping | `fail` |

In the same emission, list the findings file under `artifacts:` (the report path written in step 7).

## Failure Modes

| Mode | Response |
|---|---|
| **Worktree creation fails** | Stop |
| **PR is CLOSED or MERGED** | Note it and stop |
| **No database change in the diff** | Say so plainly and stop; the change belongs to `/review-pr` |
| **Engine or version unknown** | Assume the strictest behavior, mark lock claims `unproven`, and name the engine detail needed |
| **Table size unknown** | Treat the table as large, mark the lock claim `unproven`, and ask for the size |
| **Migration cannot be rendered to SQL read-only** | Reason from the migration source and mark the rendered-SQL claims `unproven` |
| **`ghx` unavailable** | Fall back to `gh pr view` for PR context |

## Example Usage

**Scenario 1: Blocking index creation**
```
/review-db-changes 42 acme/api
```
The migration calls `create_index('idx_users_email', 'users', ['email'])` on PostgreSQL with no `postgresql_concurrently=True`.
Report a 🔴 MUST under Lock Safety: create the index concurrently inside an autocommit block, and add a `lock_timeout`.

**Scenario 2: Over-broad delete**
```
/review-db-changes origin/main..HEAD
```
The migration deletes rows with `where created_at < :cutoff`, and the cutoff is computed from a query that can return empty.
Report a 🔴 MUST under Data Changes & Backfill and Destructive-Change Guards: assert the cutoff is non-empty, confirm the affected row count, and copy the database before deleting.

**Scenario 3: Foreign key without a split**
```
/review-db-changes 88 acme/api
```
A foreign key is added in one step on a large table.
Report a 🟡 SHOULD under Lock Safety: add it `NOT VALID` and validate in a separate migration.

**Scenario 4: Reversible additive migration**
```
/review-db-changes 55 acme/api
```
The diff adds a nullable column, an index created concurrently, a matching `downgrade()`, and a migration test.
Report 🟢 approved with no findings.

## Related Skills

| Skill | Relationship |
|---|---|
| `review-pr` | General code-craft review; this skill is the migration specialization and defers non-database hunks to it |
| `review-api-changes` | Reviews the contract above the data; this skill reviews the storage change beneath it |
| `create-lifecycle` / `review-lifecycle` | Document a resource's states and retention; this skill reviews the migration that implements the storage |
| `audit-performance-efficiency` | Repo-wide query and index analysis; this skill is diff-focused |
| `verify-pr` | Proves criteria by running the migration; this review is static and never runs a destructive migration |
