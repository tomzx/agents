---
name: assess-pr-risk
description: Estimate how risky a GitHub pull request is and how confident that estimate is, then recommend the next action for a human reviewer. Consumes existing validate-pr, verify-pr, and review-pr reports as evidence when present. Use when the user asks "how risky is this PR", "assess PR risk", "risk and confidence for this PR", "should I review this deeply", or wants to decide what to do next with a PR.
allowed-tools: Bash(gh:*, ghx:*, git:*, ~/.agents/scripts/should-post-to-github:*), Read, Write, Glob, Grep
argument-hint: "<pr-number> [repository]"
---

# Assess PR Risk

Estimates how risky a pull request is and how confident that estimate is, then recommends the next action for a human reviewer.
Two axes: **risk** is a judgment about the change (how much damage if it is wrong, how hard to undo), and **confidence** is a judgment about the evidence base (what could and could not be verified).
The routing table turns the two scores into one next action, so the reviewer can decide at a glance.
This skill judges neither code craft (that is `/review-pr`), conformance (`/verify-pr`), nor product fit (`/validate-pr`); it consumes their reports as evidence when present and never re-litigates their verdicts.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md` (PR Review Reports for report location and posting rules).
- If no argument is provided, target the pull request from `$PR_NUMBER` (and `$REPO`).
- `gh` CLI authenticated with read access to the target repository
- `git worktree` available
- Optional but confidence-raising: prior `validate-pr`, `verify-pr`, or `review-pr` reports for this PR under `$PR_REVIEW_DIR`
- Orchestrators (`review-pr-full`, `review-requested-prs`) dispatch this skill concurrently with the analyze-test-coverage -> validate -> verify -> review chain and provide `WORKTREE_DIR`; sibling reports may still be missing at run time, which the confidence rubric reflects honestly. Re-running the skill after the chain completes raises confidence, which is why it is listed first in the dispatch order.

### Skill attribution (GitHub)

Before posting to GitHub, read `../github-post-attribution/SKILL.md` and append the footer for `SKILL_DIR` = `assess-pr-risk`.

## Workflow

```
Fetch PR metadata + diff ($1)
          |
          v
CLOSED or MERGED? --> note and stop
          |
          v
Create git worktree on PR branch
          |
          v
Gather evidence
(sibling reports: coverage / validate / verify / review;
 diff, codebase, churn of touched files)
          |
          v
Score risk factors (7, each Low/Medium/High)
          |
          v
Score confidence (evidence-based rubric)
          |
          v
Route the next action (risk x confidence matrix)
          |
          v
Write assess-pr-risk.<sha>.md
Post if should-post-to-github allows
          |
          v
Clean up worktree
```

## Steps

### 1. Fetch PR metadata and diff

```bash
ghx pr view $PR_NUMBER --repo "$REPO" --comments --refresh
gh pr diff $PR_NUMBER --repo "$REPO"
```

Extract:
- `HEAD_COMMIT`: the `headRefOid` (latest commit SHA, full)
- `SHORT_SHA`: first 7 characters of `HEAD_COMMIT`
- `PR_AUTHOR`: the `author.login`
- `HEAD_REPO`: the `headRepository.nameWithOwner`
- `HEAD_BRANCH`: the `headRefName`
- `HEAD_TREE`: content snapshot of the head commit: `git fetch "https://github.com/$HEAD_REPO.git" "$HEAD_BRANCH" >/dev/null 2>&1 || true; git rev-parse "$HEAD_COMMIT^{tree}"`
- `ISSUE_NUMBER`: the first linked issue number from `closingIssuesReferences` (or empty)
- `PR_STATE`: `OPEN`, `CLOSED`, or `MERGED`
- List of changed files and diff stats (additions, deletions, changed files count)

If `PR_STATE` is `CLOSED` or `MERGED`, note it and stop; risk assessment is for open PRs.

Define the report directory once: `PR_REVIEW_DIR="$HOME/.sdlc/$REPO/pull-requests/$PR_NUMBER"` (see `sdlc/references/shared.md`, PR Review Reports).

### 2. Create a git worktree on the PR branch

If `$WORKTREE_DIR` is already set (e.g. by an orchestrator), use that directory directly and skip creation and cleanup.

```bash
_WORKTREE_OWNER=false
if [ -z "${WORKTREE_DIR:-}" ]; then
  git fetch "https://github.com/$HEAD_REPO.git" $HEAD_BRANCH
  WORKTREE_DIR=/tmp/sdlc/$REPO/${ISSUE_NUMBER:-pr-$PR_NUMBER}
  mkdir -p /tmp/sdlc/$REPO
  git worktree add $WORKTREE_DIR FETCH_HEAD
  _WORKTREE_OWNER=true
fi
```

All code reading, caller search, and churn analysis happen inside the worktree directory.

If worktree creation fails, stop.

### 3. Gather evidence

Three evidence sources, in order:

**Sibling reports.** Read `analyze-test-coverage.report.md`, `validate-pr.report.md`, `verify-pr.report.md`, and `review-pr.report.md` from `$PR_REVIEW_DIR` when present.
A report is **current** when its marker `sha` equals `HEAD_COMMIT`; if its `sha` is an ancestor of `HEAD_COMMIT`, treat it as current and note the delta in the report.
From each current report, extract what it contributes: the validate verdict (Right / Partially right / Wrong / Inconclusive), the verify statuses (which Must criteria conform at runtime, which are static-only or unverified), and the review findings (severity counts, coverage tables, reversibility and compatibility notes).
Missing reports are recorded as missing evidence; never infer their content.

**Diff and codebase.** From the worktree, identify what the change touches and who depends on it:
- Search for callers of every changed or removed exported symbol (Grep for the symbol name, check sibling modules and package boundaries).
- Note shared state, cross-package imports, and persistence or wire formats the change alters.
- Note security-sensitive surfaces touched: authentication, authorization, cryptography, secrets handling, input validation, PII.

**Churn.** Measure how often the touched files change, a proxy for fragility:

```bash
git -C "$WORKTREE_DIR" log --since="12 months" --name-only --format= -- <changed files> | sort | uniq -c | sort -rn
```

### 4. Score the risk factors

Score each factor Low / Medium / High, citing `file:line` evidence for every non-Low score.
Trace findings end to end before scoring them: a suspicion you did not confirm by reading the caller, config, or schema does not count.

| Factor | Low | Medium | High |
|---|---|---|---|
| **Blast radius** | Leaf or localized change, no external callers | Multiple callers within one subsystem | Shared core module, cross-package effect, or callers outside the repo |
| **Public interface** | No public surface touched | Additive public surface, or additive but forward-compatible-only-by-luck contract | Breaking or removed API, or a new contract that rejects unknown values and has no versioning path |
| **Security sensitivity** | None touched | Input validation, security config, or PII handling | Authentication, authorization, cryptography, or secrets handling |
| **Reversibility** | Fully reversible by revert | Migration or config change with a documented rollback | Destructive or irreversible operation (data drop, permanent transform, one-way door) |
| **Operational exposure** | Internal only | Behavior change behind a flag or config | Hot path, externally triggered behavior change, or rollout with no guard |
| **Coverage gap** | Changed behavior covered by tests | Partial coverage, edge cases untested | Core behavior with no test (use the analyze-test-coverage or review-pr coverage tables when current, else inspect the diff) |
| **Churn** | Files stable (few touches in 12 months) | Monthly-level activity | Hotspot: touched weekly or by many authors |

Rollup rules, applied in order:
1. Any factor High → **risk: High**.
2. Otherwise two or more factors Medium → **risk: Medium**.
3. Otherwise → **risk: Low**.

Every High factor must name the concrete failure or future change it makes expensive; if you cannot name it, downgrade to Medium and say why.

### 5. Score the confidence

Confidence reflects the evidence base, not the gut. Count points:

| Evidence | Points |
|---|---|
| Current validate-pr report | +1 |
| Current verify-pr report | +1 |
| All Must criteria Conforms (runtime proof, not static-only) in that report | +1 |
| Current review-pr report | +1 |
| Linked issue describing the change (verifiable intent) | +1 |
| Analyzable diff (under 1000 changed lines) | +1 |

Map the total: 0-1 → **Low**, 2-4 → **Medium**, 5-6 → **High**.

Caps:
- No linked issue (nothing to validate the need against) → at most Medium.
- Verification is static-only (no runtime proof of any Must criterion) → at most Medium.
- Diff 1000 lines or more → at most Medium, and say which areas were sampled rather than read.

State in one sentence what would raise confidence (e.g. "running /verify-pr to get runtime proof would add 2 points").

### 6. Route the next action

| Risk | Confidence | Verdict token | Recommended next action |
|---|---|---|---|
| Low | High | `fast-track` | Safe to unblock: run `/quick-pr-review`, or merge once checks pass |
| Low | Medium | `confirm` | Cheap confirmation first: run `/review-pr`, then fast-track |
| Low | Low | `investigate` | Evidence is thin: run `/review-pr-full`, then re-assess |
| Medium | High | `decide` | Read the risk drivers below and decide with findings in hand |
| Medium | Medium or Low | `investigate` | Run `/review-pr-full`, then re-assess before deciding |
| High | High | `block` | Address the High risk drivers before merging |
| High | Medium or Low | `hold` | Treat as high risk until proven otherwise: full review plus human deep-dive |

The verdict token goes in the report marker so orchestrators can act on it mechanically.

### 7. Write the report and post it

Write the report to `$PR_REVIEW_DIR/assess-pr-risk.<SHORT_SHA>.md` and point the stable symlink at it (`ln -sf "assess-pr-risk.<SHORT_SHA>.md" "assess-pr-risk.report.md"`).
Start the file with the marker, substituting the verdict token, the risk level, and the confidence level (the orchestrator script displays the last two in its Risk column):

```
<!-- {"step":"assess-pr-risk","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"VERDICT_TOKEN","risk":"RISK_LEVEL","confidence":"CONFIDENCE_LEVEL"} -->
```

Posting as a PR comment is decided by `should-post-to-github`. Run `~/.agents/scripts/should-post-to-github --repo "$REPO" --author "$PR_AUTHOR"`; if it exits 1, skip posting (the report is saved locally). If it exits 0, post the report file with the attribution footer per `../github-post-attribution/SKILL.md`.

### 8. Clean up

```bash
if [ "$_WORKTREE_OWNER" = true ]; then
  git worktree remove $WORKTREE_DIR
fi
```

## Output Format

```markdown
<!-- {"step":"assess-pr-risk","sha":"HEAD_COMMIT","tree":"HEAD_TREE","verdict":"VERDICT_TOKEN","risk":"RISK_LEVEL","confidence":"CONFIDENCE_LEVEL"} -->
# PR Risk Assessment: #<PR_NUMBER> <title>

Reviewed commit: `SHORT_SHA`
**Risk: Low / Medium / High** · **Confidence: Low / Medium / High** · **Next action: <verdict token>**

**Recommended next step:** <one sentence from the routing table, naming the skill to run>

## Risk factors

| Factor | Score | Evidence |
|---|---|---|
| Blast radius | Low/Medium/High | <file:line and one-line reasoning> |
| Public interface | ... | ... |
| Security sensitivity | ... | ... |
| Reversibility | ... | ... |
| Operational exposure | ... | ... |
| Coverage gap | ... | ... |
| Churn | ... | ... |

## Confidence

| Evidence | Present? | Points |
|---|---|---|
| validate-pr report current | Yes / No / Missing | 0-1 |
| verify-pr report current | Yes / No / Missing | 0-1 |
| Runtime proof of Must criteria | Yes / No / Static only | 0-1 |
| review-pr report current | Yes / No / Missing | 0-1 |
| Linked issue describing the change | Yes / No | 0-1 |
| Analyzable diff | Yes / No (<N> lines) | 0-1 |

Total: <N> points -> <level>. Caps applied: <none / which and why>.
What would raise confidence: <one sentence>.

## Top risk drivers

<For each High factor: the concrete failure or expensive future change, with file:line. Omit the section when risk is Low.>

---
<Attribution footer per github-post-attribution>
```

## Failure Modes

| Mode | Response |
|---|---|
| **Worktree creation fails** | Stop |
| **PR is CLOSED or MERGED** | Note it and stop |
| **No sibling reports at all** | Proceed with diff-only evidence; confidence will be Low or Medium, say which report would help most |
| **Diff 1000 lines or more** | Sample entry points and public surface, say what was sampled, cap confidence at Medium |
| **`ghx` unavailable** | Fall back to `gh pr view` |
| **Churn unavailable (shallow clone)** | Score churn from the diff alone, note the limitation |

## Example Usage

**Scenario 1: Small, tested, internal fix**
```
/assess-pr-risk 42 acme/api
```
Leaf change, no public surface, tests cover it, one commit a year of churn. All factors Low. No sibling reports, so confidence Medium. Verdict `confirm`: run `/review-pr`, then fast-track.

**Scenario 2: Auth change with full pipeline evidence**
```
/assess-pr-risk 88
```
Touches session validation (Security High) with callers across three packages (Blast radius Medium). Current verify report shows runtime proof of all Must criteria and a current review report: 5 points, confidence High. Verdict `block` until the security driver is resolved, with the concrete session-invalidation gap named.

**Scenario 3: Scary-looking diff, thin evidence**
```
/assess-pr-risk 55
```
1200-line migration touching the billing schema (Reversibility High, Coverage High). No reports, no linked issue. Risk High, confidence Low (capped). Verdict `hold`: treat as high risk until `/review-pr-full` runs.

**Scenario 4: Re-assess after evidence lands**
```
/assess-pr-risk 55
```
The same PR after `/review-pr-full` completed on this commit: the migration has a documented rollback and new tests. Reversibility drops to Medium, Coverage to Low, confidence rises to High. Verdict `decide`, with the remaining driver named.

## Next Step

Act on the verdict token: `fast-track` → `/quick-pr-review`; `confirm` → `/review-pr`; `investigate` → `/review-pr-full`; `decide` → the human reads the risk drivers and chooses; `block` or `hold` → the findings go to the author before merging.
