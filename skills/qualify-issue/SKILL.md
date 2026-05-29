---
name: qualify-issue
description: Drive a multi-round Q&A loop with an external reporter to gather enough information to proceed to requirements.
allowed-tools: Bash(gh:*, gh-cached:*, scripts/get-env:*), Read, Write
argument-hint: "<issue-url-or-number> [repository]"
---

# Qualify Issue

Takes an externally submitted GitHub issue (feature request or bug report) and drives a structured Q&A loop with the reporter until the issue contains enough information to proceed to `/create-requirements`.

Assumes `review-issue` has already been run and identified what is missing.
This skill owns the iterative clarification loop. It stops when the issue is fully qualified or the reporter is unresponsive.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Issue URL or number (`$1`), and optionally repository in `owner/repo` format (`$2`)
- Read any files present under `.sdlc/context/` and apply any artifact style rules found there

### Skill attribution (GitHub)

Before posting any comment with `gh`, read [`../github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `qualify-issue`.

## Workflow

```
Fetch issue + comment history
           |
           v
Identify open questions
           |
           v
All answered?
   /          \
 Yes            No
  |              |
  v              v
Update issue   Post questions
body + signal  as comment
"qualified"         |
                    v
              Wait for reporter
              (skill stops here)
                    |
                    v
              Re-invoke when
              replies arrive
```

## Steps

### 1. Fetch the issue and full comment history

```bash
gh-cached issue view $1 [--repo $2] --comments
```

Extract:
- Issue type (bug / feature request)
- What is already known (background, version, steps, ACs, etc.)
- What is still missing or ambiguous
- Any prior clarification comments and their answers

### 2. Identify open questions

Using the `review-issue` checklist as the standard, determine what information is still needed:

**Bug reports -- ask if missing:**
- Steps to reproduce (exact sequence)
- Expected vs. actual behavior
- Version or environment (OS, runtime, config)
- Whether the issue is consistently reproducible or intermittent
- Any error messages or logs

**Feature requests -- ask if missing:**
- The underlying problem or use case (not just the desired solution)
- Who the intended user or stakeholder is
- What "done" looks like -- proposed acceptance criteria
- Whether there are known constraints or non-goals

**All types:**
- Any ambiguous terms in the description
- Scope boundaries if the request is broad

If previous comments already answered some questions, treat those as resolved and only ask what remains open.

### 3a. If all questions are answered -- qualify the issue

1. Synthesize the answers into a revised issue body that incorporates everything learned.
2. Update the issue:
   ```bash
   gh issue edit $1 [--repo $2] --body "$(cat <<'EOF'
   <revised body with all gathered information incorporated>
   EOF
   )"
   ```
3. Post a comment signalling qualification is complete:
   ```bash
   gh issue comment $1 [--repo $2] --body "$(cat <<'EOF'
   This issue is now fully qualified and ready for requirements analysis.

   ---

   Posted with [qualify-issue](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
   EOF
   )"
   ```
4. Inform the user: "Issue #N is qualified -- proceed with `/create-requirements`."

### 3b. If questions remain open -- post a clarification comment

Group the open questions into a single comment. Do not spread them across multiple comments.
Number the questions so the reporter can answer by number.

```bash
gh issue comment $1 [--repo $2] --body "$(cat <<'EOF'
Thanks for the report. To move this forward, a few questions:

1. <question>
2. <question>
3. <question>

---

Posted with [qualify-issue](SKILL_FILE_URL) (`SKILL_SHORT_SHA`)
EOF
)"
```

Then stop. Inform the user which questions were posted and that the skill should be re-invoked once the reporter replies (e.g. via `/qualify-issue $1`).

### 4. On re-invocation after reporter replies

Repeat from step 1. The comment history now contains the reporter's answers.
Mark each prior question as resolved or still open based on the replies.
If new ambiguities surfaced in the answers, add them to the open question list.
Continue until step 3a is reached.

## Qualification Standard

An issue is qualified when it meets all of the following:

- The problem or use case is clearly described
- A developer unfamiliar with the request could write acceptance criteria from the description alone
- There are no undefined terms or unexplained assumptions
- The scope is bounded (it is clear what is and is not included)
- For bug reports: reproduction steps are present and the environment is identified

## Failure Modes

| Mode | Response |
|---|---|
| **Reporter does not reply after one round** | Inform the user; they decide whether to close, wait, or proceed with assumptions |
| **Reporter's answers introduce new ambiguities** | Incorporate resolved answers, post a follow-up comment with remaining questions |
| **Issue is a duplicate** | Stop, point to the existing issue, suggest running `/check-duplicates` |
| **Issue is out of scope for the project** | Stop, suggest running `/decline-issue` |

## Example Usage

**Scenario 1: Feature request missing use case**
```
/qualify-issue 88 owner/myrepo
```
Issue asks for a dark mode toggle but doesn't explain who needs it or why.
Posts one question asking for the use case and the target user.
Re-invoked after reply -- reporter explains accessibility need.
Updates issue body with the new context, posts qualification comment.

**Scenario 2: Bug report with no reproduction steps**
```
/qualify-issue 42
```
Issue says "export fails sometimes." No steps, no version, no error message.
Posts three questions: reproduction steps, version, error output.
Re-invoked after partial reply -- reporter provides version and error but steps are still vague.
Posts one follow-up question about the steps.
Re-invoked again -- now fully qualified. Updates body and signals ready.

**Scenario 3: Already answered on re-invocation**
```
/qualify-issue 42
```
Prior comment thread contains answers to all questions.
Skips posting new questions, updates issue body, signals qualification complete.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh-cached issue view <issue> [--repo <repo>] --comments` | Fetch issue and full comment history |
| `gh issue edit <issue> [--repo <repo>] --body "..."` | Update the issue body with synthesized content |
| `gh issue comment <issue> [--repo <repo>] --body "..."` | Post a clarification question comment |
