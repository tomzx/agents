---
name: sync-articles
description: Bring a batch of blog articles into conformance with the repository writing rules by dispatching one create-article job per article via opencode run, in parallel, then verifying links, front matter, style, and AI disclosure tags. Use when the user says /sync-articles, "sync articles", "update articles according to the rules", "make this year's articles conform", or wants a bulk style and structure pass over article content.
allowed-tools: Bash(rg:*, git:*, opencode:*, python3:*, chmod:*), Read, Write, Edit, Grep, Glob
argument-hint: "[--year <yyyy>] [--since <yyyy-mm-dd>] [--all] [--path <glob>] [--concurrency <n>] [--dry-run]"
---

TODAY=!`date +%Y-%m-%d`

# Sync Articles

Runs a conformance pass over a set of articles in a blog content repository (one directory per slug, each with an `index.md`).
Each article is revised in place by its own `opencode run` job invoking the `create-article` skill, so every article gets a fresh context and the batch scales without one session accumulating the whole corpus.
After the jobs finish, the orchestrator verifies links, front matter, style rules, and AI disclosure tags across the diff, and reports a per-article summary.

This is the batch counterpart of `create-article`, which owns all per-article editing judgment.
For a single article, invoke `/create-article` directly.
For a report without edits, use `/review-article`.

## Prerequisites

- Working directory is the root of the blog content repository (articles as `<slug>/index.md` with YAML front matter, conventions in its `AGENTS.md`).
- `opencode` available on PATH, with the `create-article` skill installed.
- `rg`, `git`, and `python3` (with `yaml`) available on PATH.
- The runner script next to this skill: `skills/sync-articles/sync-articles`.

## Scope and Modes

Resolve the article set from the arguments:

| Mode | Argument | Selection |
|---|---|---|
| Year (default) | `--year <yyyy>` | `created:` in the given year, defaulting to the current year |
| Since | `--since <yyyy-mm-dd>` | `created:` on or after the date |
| All | `--all` | every article |
| Path filter | `--path <glob>` | restrict any of the above to paths matching the glob |

Notes on `create-article` upstream guidance: it recommends running `research-article` first when sources are not yet gathered.
Skip that recommendation for this skill and say so when reporting: the articles already exist with their sources inline, and the task is conformance revision, not new research.

## Workflow

```
Resolve scope -> build article list (rg over front matter)
        |
        v
Launch runner detached (one opencode run job per article, bounded concurrency)
        |
        v
Poll results file until all jobs finish
        |
        v
Verify: internal links, front matter, style rules, disclosure tags
        |
        v
Report per-article summary (changed files, fixes, failures)
```

## Steps

### 1. Resolve scope and build the list

```bash
rg -l "^created: ${YEAR}-" --glob "**/index.md" | sort > /tmp/opencode/sync-articles/pending.txt
```

Store working files under `/tmp/opencode/sync-articles/`.
Exclude non-article infrastructure files (for example an `agents/log.md`) from the list; they are not articles.

### 2. Preview with --dry-run

Print the list and the count, plus the planned concurrency (default 4).
Confirm with the user before launching when the batch is large (a job takes roughly 2 to 4 minutes, so 80 articles at concurrency 4 is about 75 minutes).

### 3. Launch the runner detached

```bash
mkdir -p /tmp/opencode/sync-articles
rg -l "^created: ${YEAR}-" --glob "**/index.md" | sort > /tmp/opencode/sync-articles/pending.txt
nohup skills/sync-articles/sync-articles /tmp/opencode/sync-articles/pending.txt \
  --repo "$(pwd)" \
  --logdir /tmp/opencode/sync-articles/logs \
  --statusdir /tmp/opencode/sync-articles/status \
  --concurrency 4 \
  > /tmp/opencode/sync-articles/runner.log 2>&1 &
```

Two failure modes are baked into the runner because they silently produced zero work when hit in practice:
- The list file is redirected into `xargs` explicitly (`< "$LIST"`).
  A backgrounded runner inherits `/dev/null` as stdin, and `xargs` with empty stdin runs zero jobs and exits 0.
- The worker function is `export -f`'d so the `bash -c` child processes can call it.

### 4. Monitor progress

Poll the results file in later commands (the runner survives across tool calls because it is detached):

```bash
echo "OK=$(grep -c '^OK' results.txt) FAIL=$(grep -c '^FAIL' results.txt) RUNNING=$(pgrep -fc 'opencode run')"
```

Sleep 5 to 15 minutes between polls for large batches.
If a job fails, read its log under the logdir before retrying; re-run only the failed paths by writing them to a new list file.

### 5. Verify the diff

Run all of these; each must come back clean before reporting success.

Internal links (CI parity with the repository's `test-links.php`, which may not be installed locally):

```bash
python3 - <<'EOF'
import re
from pathlib import Path
root = Path(".")
pattern = re.compile(r"\[[^\]]+\]\((?!.{0,5}://|#)([^)]+?)(?: \"[^\)]+\")?\)")
broken = 0
for md in sorted(root.rglob("*.md")):
    if ".git" in md.parts:
        continue
    for target in pattern.findall(md.read_text(errors="replace")):
        t = target.split("#")[0]
        if t and not (md.parent / t).resolve().exists():
            print(f"BROKEN {md} -> {t}")
            broken += 1
print(f"Broken: {broken}")
EOF
```

Compare the broken set against the pre-run baseline (capture it before launching, or `git stash` compare).
Only new breakage in changed files blocks the run.

Style on added lines (no em-dashes, no banned terms):

```bash
git diff -U0 -- "*.md" | grep -E "^\+" | grep -P " —|— " && echo "EM-DASH FOUND"
git diff -U0 -- "*.md" | grep -E "^\+" | grep -Pi "\b(shape|honest|load[ -]bearing|substrate|posture)\b" && echo "BANNED TERM FOUND"
```

Front matter parses and required fields survive:

```bash
git diff --name-only | while read -r f; do
  python3 -c "import yaml; yaml.safe_load(open('$f').read().split('---')[1])" || echo "YAML FAIL: $f"
done
```

Confirm no `title:`, `status:`, or `type:` line changed unless it was broken before (normalize `created:` timestamps to `YYYY-MM-DD` is acceptable).

### 6. Enforce AI disclosure tags

Every file modified by the run must carry the disclosure tag of the model that revised it.

```bash
git diff --name-only > changed.txt
for f in $(cat changed.txt); do
  grep -H "^tags:" "$f" | grep -q "llm=${MODEL}" || echo "$f"
done
```

`${MODEL}` is the model the jobs ran with (read it from the job logs' header line).
For each listed file, append `llm=${MODEL}` to its `tags:` array, preserving existing `llm=` tags (multiple are allowed).
Do not skip non-article files the jobs had to touch, such as `agents/log.md`, which its section's rules require agents to append to.

### 7. Report

Emit the output format below.
Leave all changes uncommitted in the working tree.

## Output Format

```markdown
## Sync Articles: <scope description>

| Status | Article | Notes |
|---|---|---|
| ok | <slug>/index.md | <one-line summary of fixes from the job log> |
| unchanged | <slug>/index.md | already conformed |
| fail | <slug>/index.md | <reason; retry command> |

Files changed: N (insertions, deletions)
Verification: links ok, YAML ok, style ok, disclosure tags ok
Not committed.
```

## Failure Modes

| Mode | Response |
|---|---|
| **Runner exits immediately, zero jobs ran** | The list was not redirected into `xargs`, or the function was not exported; both are handled by the shipped runner, so use it rather than re-deriving the loop |
| **Jobs die when the launching tool call ends** | The runner was backgrounded without `nohup` (or `setsid`); relaunch detached with stdout redirected to a file |
| **`opencode run` fails for one article** | Read that job's log, fix or skip, and re-run just that path via a single-path list file |
| **Provider rate limits across parallel jobs** | Lower `--concurrency` (2 is usually safe) and re-run only the remaining paths |
| **New broken internal links appear** | Fix or revert the offending link edits before reporting success; pre-existing breakage in untouched files is out of scope |
| **Modified file missing its `llm=` tag** | Append it per step 6 before reporting success |

## Example Usage

**Scenario 1: This year's articles, default scope**
```
/sync-articles
```
Selects every article with `created:` in the current year, dispatches one `create-article` revision job per article at concurrency 4, verifies the diff, adds missing disclosure tags, and reports the summary table.

**Scenario 2: Everything, two at a time**
```
/sync-articles --all --concurrency 2
```
Whole-corpus pass run gently; expect a long batch and poll at 15 minute intervals.

**Scenario 3: Preview the blast radius**
```
/sync-articles --year 2026 --dry-run
```
Prints the article list, count, and estimated duration without launching any job.

## Notes

- The per-article job prompt is fixed (see the runner script) and deliberately minimal: name the skill, name the path, require in-place revision to the skill rules and the repository `AGENTS.md`, preserve meaning and front matter, and forbid commits.
- The `agents/` section of a blog repo has its own rules that take precedence: jobs append to its log themselves, human edits there must never be reverted, and its articles may legitimately omit `type:`.
- The skill never commits; landing the changes is the user's call.
- Re-running over an already-conformed article is safe: the job finds little to change and the file shows as unchanged or lightly touched in the report.
