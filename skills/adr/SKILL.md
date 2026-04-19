---
name: adr
description: Create and manage Architecture Decision Records (ADRs) for significant technical decisions made during a session.
argument-hint: "[title of decision]"
---

# Architecture Decision Records (ADR)

Creates and manages Architecture Decision Records for significant technical decisions. ADRs capture the context, decision, and consequences of architectural choices so future developers understand not just what was decided but why.

## Prerequisites

- A git repository
- A `docs/decisions/` directory (created automatically if absent)

## Steps

### 1. Identify the ADR Storage Location

Check for an existing ADR directory in this order:
1. `docs/decisions/`
2. `docs/adr/`
3. `adr/`

If none exists, create `docs/decisions/`.

```bash
ADR_DIR=$(ls -d docs/decisions docs/adr adr 2>/dev/null | head -1)
ADR_DIR=${ADR_DIR:-docs/decisions}
mkdir -p "$ADR_DIR"
```

### 2. Determine the Next ADR Number

Find the highest existing ADR number and increment by 1. Pad to four digits.

```bash
NEXT=$(ls "$ADR_DIR"/*.md 2>/dev/null \
  | grep -oP '^\d+' \
  | sort -n \
  | tail -1)
NEXT=$(printf "%04d" $((${NEXT:-0} + 1)))
```

### 3. Collect Decision Details

If an argument was provided, use it as the title. Otherwise, ask the user:

> "What is the title of this decision? (e.g., 'Use PostgreSQL for the primary datastore')"

Then ask the following questions one at a time, waiting for the user's answer to each before asking the next:

1. **Context** - "What situation or problem led to this decision? What constraints, forces, or requirements were at play?"
2. **Decision** - "What was decided? Describe the choice made and the approach taken."
3. **Consequences** - "What are the outcomes of this decision? What becomes easier, harder, or different as a result? Are there any known trade-offs or risks?"
4. **Status** - "What is the status? (accepted / proposed / deprecated)" - default to `accepted` if the decision was implemented this session.
5. **Alternatives considered** (optional) - "Were any alternatives considered and rejected? If so, briefly note them and why they were not chosen."

### 4. Write the ADR File

Create the file at `$ADR_DIR/$NEXT-<slugified-title>.md`.

Slugify the title: lowercase, replace spaces and special characters with hyphens, collapse multiple hyphens.

```bash
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
ADR_FILE="$ADR_DIR/$NEXT-$SLUG.md"
```

Write the file using this template:

```markdown
# ADR-NNNN: <Title>

Date: YYYY-MM-DD
Status: <accepted | proposed | deprecated | superseded by [ADR-XXXX](./XXXX-title.md)>

## Context

<Context text from step 3.>

## Decision

<Decision text from step 3.>

## Consequences

<Consequences text from step 3.>

## Alternatives Considered

<Alternatives text from step 3, or omit this section if none were provided.>
```

Use today's date for the `Date` field.

### 5. Check for Superseded ADRs

Ask the user:

> "Does this decision supersede or replace any previous ADR? If so, which one(s)?"

If yes:
- Update the `Status` line of the new ADR to `accepted (supersedes ADR-XXXX)`.
- Open the superseded ADR and change its `Status` line to `superseded by [ADR-NNNN](./<NNNN>-<slug>.md)`.

### 6. Commit the ADR

Stage and commit the new (and any updated) ADR files:

```bash
git add "$ADR_DIR/"
git commit -m "docs: add ADR-$NEXT - $TITLE"
```

## Output Format

After completing all steps, print:

```
Created: $ADR_FILE
Title:   ADR-NNNN: <Title>
Status:  <status>
```

Then print the full contents of the created ADR file.

## Example Usage

**Scenario 1: Choosing a database**
User ran `/adr` after deciding to use PostgreSQL. ADR-0001 is created at `docs/decisions/0001-use-postgresql.md` documenting that the team chose PostgreSQL over SQLite due to concurrent write requirements and the need for row-level locking.

**Scenario 2: Superseding a decision**
The team switches from REST to GraphQL. ADR-0012 is created and ADR-0003 (which documented the REST decision) is updated to `superseded by ADR-0012`.

**Scenario 3: Proposed decision**
A decision is still under discussion. Status is set to `proposed` and the ADR captures the current thinking without locking in the choice.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ls docs/decisions/` | List existing ADRs |
| `grep -r "Status:" docs/decisions/` | See status of all ADRs |
| `git log --oneline docs/decisions/` | See ADR history |
