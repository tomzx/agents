---
name: sync-opinions
description: >
  Scan all markdown files in a target directory, extract opinions and the
  statements that support them, then generate or update an OPINIONS.md file.
  Use when the user says /sync-opinions, "sync opinions", "extract opinions",
  or wants to compile opinions from a set of documents.
---

# Sync Opinions

Scan markdown files in a target directory, extract opinions and supporting
evidence, then generate a consolidated OPINIONS.md file.

## When to use

- The user says `/sync-opinions`, "sync opinions", "extract opinions", or wants
  to compile opinions from a set of documents.
- Periodic refresh of an OPINIONS.md file after documents in the target
  directory have changed.
- Initial creation of an OPINIONS.md file for a new directory.

## Prerequisites

- A target directory containing one or more markdown (`.md`) files.
- Read access to all files in the target directory.

## Workflow

### 1. Identify the target directory

The user provides a directory path. If none is provided, prompt for one.

```bash
# Verify the directory exists and list markdown files
find <target-dir> -maxdepth 1 -name '*.md' ! -name 'OPINIONS.md' -type f
```

Exclude any existing `OPINIONS.md` from the scan (it is the output, not input).

### 2. Read all markdown files

Read every `.md` file in the target directory (non-recursive by default,
recursive if the user passes `--recursive`). For each file, load the full
content.

### 3. Extract opinions

For each document, identify **opinions**: statements that express a judgment,
preference, recommendation, belief, or position rather than an objective fact.

An opinion is any statement that:

- Expresses a preference ("X is better than Y", "we should use X").
- Makes a recommendation ("always do X", "avoid Y").
- States a belief about how things should be ("the right approach is X").
- Takes a stance on a trade-off ("simplicity over flexibility").
- Asserts a subjective assessment ("X is overkill for our use case").

Distinguish opinions from:

- **Facts**: verifiable statements ("Python 3.12 was released in October 2023").
- **Descriptions**: neutral explanations ("the function returns a boolean").
- **Questions**: interrogative sentences.
- **Definitions**: "X means Y".

### 4. Group opinions by topic

Cluster extracted opinions into topics based on their subject matter. Use the
headings and structure already present in the source documents as a guide. If
the same topic appears in multiple files, merge the opinions under one heading.

### 5. Attach supporting evidence

For each opinion, include:

- **The opinion statement** itself, paraphrased into a concise claim.
- **Source**: the file it was extracted from.
- **Quote**: the original text (or relevant excerpt) that expresses the opinion.
- **Supporting evidence**: any arguments, examples, data, or reasoning given
  in the same document that backs up the opinion. This includes:
  - Rationale given immediately before or after the opinion.
  - Examples or analogies used to justify it.
  - References to experience, measurements, or outcomes.
  - Contrasting alternatives mentioned and why they were rejected.

If no supporting evidence is present in the source text, note "No supporting
evidence found in source material."

### 6. Generate OPINIONS.md

Write the consolidated output to `<target-dir>/OPINIONS.md` using the format
below. If the file already exists, overwrite it with the updated version.

## Output Format

```markdown
# Opinions

Extracted from documents in `<target-dir>/` on YYYY-MM-DD.

## Sources

| File | Opinions extracted |
|------|-------------------|
| file-a.md | 3 |
| file-b.md | 2 |

---

## <Topic 1>

### <Opinion 1>

> <paraphrased opinion statement>

**Source**: `file-a.md`
**Quote**:
> <original text from the document>

**Supporting evidence**:
- <reason/argument/example/data point from the document>
- <another supporting point>

---

### <Opinion 2>

> <paraphrased opinion statement>

**Source**: `file-b.md`
**Quote**:
> <original text from the document>

**Supporting evidence**:
- <reason/argument/example/data point from the document>

---

## <Topic 2>

### <Opinion 3>

> <paraphrased opinion statement>

**Source**: `file-a.md`
**Quote**:
> <original text from the document>

**Supporting evidence**:
- <reason/argument/example/data point from the document>

---
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `<target-dir>` | Directory containing markdown files to scan (required) | Prompt user |
| `--recursive` | Scan subdirectories recursively | `false` |
| `--output` | Path for the output file | `<target-dir>/OPINIONS.md` |

## Example Usage

**Scenario 1: Basic extraction**
```
/sync-opinions /home/user/notes
```
Scans all `.md` files in `/home/user/notes/`, extracts opinions with supporting
evidence, and writes `/home/user/notes/OPINIONS.md`.

**Scenario 2: Recursive scan**
```
/sync-opinions /home/user/projects/decisions --recursive
```
Scans `.md` files in `/home/user/projects/decisions/` and all subdirectories.

**Scenario 3: Custom output path**
```
/sync-opinions /home/user/notes --output /tmp/opinions.md
```
Writes the output to `/tmp/opinions.md` instead of the default location.

## Useful Commands Reference

| Command | Description |
|---|---|
| `find <dir> -name '*.md' -type f` | List markdown files in directory |
| `find <dir> -name '*.md' ! -name 'OPINIONS.md' -type f` | List markdown files excluding output |
