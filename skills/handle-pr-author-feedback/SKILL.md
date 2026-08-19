---
name: handle-pr-author-feedback
description: As a PR reviewer, verify that the author's new commits actually address your review comments, resolve fixed threads, reply on partial or unaddressed ones, and evaluate author rebuttals. The reviewer-side counterpart of handle-pr-reviewer-feedback.
allowed-tools: Bash(gh:*, ghx:*, git:*, ~/.agents/scripts/should-post-to-github:*), Read, Glob, Grep
argument-hint: "<pr-number>"
---

# Handle PR Author Feedback

As the reviewer of a GitHub pull request, verifies that the author's fixes actually address the review feedback left earlier. For each unresolved review thread, inspects the current code and diff to decide whether the comment is addressed, partially addressed, not addressed, or reasonably rejected, then resolves the fixed threads and replies on the rest. Whether replies are posted and threads resolved on GitHub is decided by `should-post-to-github` (based on `~/.sdlc/config.yaml`), otherwise replies are drafted without posting.

This skill never modifies the PR's code. To implement fixes on your own PR, use `handle-pr-reviewer-feedback` instead.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- PR number identifying an open pull request where you left review comments
  - If `$1` is provided, use it directly
  - If `$1` is not provided, resolve the PR number with: `gh pr list --head $(git branch --show-current) --json number --jq '.[0].number'`

### Skill attribution (GitHub)

Before posting any PR comment with `gh`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Posted with** footer for `SKILL_DIR` = `handle-pr-author-feedback`.

## Workflow

```
Fetch PR threads + metadata ($1)
        |
        v
Filter to unresolved threads
authored by current user
        |
        v
   For each thread
        |
        v
   Inspect current code + diff
   since the comment
        |
        v
   Verdict: addressed / partial /
   not addressed / rebuttal
        |
        v
Present verdicts to user for approval
       /         \
   Approved     Rejected
      |             |
      v             v
   Resolve +      Skip
   reply per thread
   (ghx + GraphQL),
   only if
   should-post-to-github
   allows
      |
      v
All threads resolved? --Yes--> Suggest /quick-pr-review
                              to re-approve
```

## Steps

1. Fetch PR metadata and threads:
   ```
   ghx pr view $1 --json --refresh
   ghx pr threads $1 --ids --state all
   ```
   Extract the latest commit SHA, the PR author, and the current user (`gh api user --jq .login`).

2. Filter threads to those that are:
   - unresolved, and
   - authored by the current user (the first comment's author is you).

   Threads started by other reviewers are skipped; report them as out of scope.

3. For each thread, inspect the fix. The diff is cumulative, so the test is "is the concern addressed in the current code", not "which commit touched it":
   - Read the thread's comment (file, line, request) and any author replies.
   - Fetch the current diff: `gh pr diff $1`.
   - Read the current file content at the commented location when the diff alone is insufficient:
     `gh api repos/{owner}/{repo}/contents/{path}?ref={headRefOid} --jq .content | base64 -d`.
   - Optionally check the commits added since the comment for citation: `gh pr view $1 --json commits --jq '.commits[].oid'`.

4. Assign a verdict per thread:
   - **Addressed**: the code now satisfies the comment correctly (not a cosmetic rename that dodges the issue). If the comment asked for tests, tests exist and plausibly cover the case.
   - **Partially addressed**: part of the request is done, part remains. Record precisely what remains.
   - **Not addressed**: no meaningful change and no substantive author reply.
   - **Rebuttal**: the author replied explaining why the change will not be made. Evaluate the justification on its merits; if it is sound (style preference, out of scope, documented trade-off), accept it; otherwise prepare a counter-argument citing code or requirements.

5. Present a verdict table to the user for approval: thread, comment summary, verdict, and the proposed reply or resolve action.

6. On approval, decide whether to post: get the PR author (`gh pr view $1 --json author --jq .author.login`), then run `~/.agents/scripts/should-post-to-github --repo "<owner>/<repo>" --author "<PR_AUTHOR>"`.
   If it exits 0:
   - **Addressed**: reply to the thread, then resolve it:
     ```
     ghx pr comment $1 --reply-thread <thread-id> --body "Addressed in <short-sha>. Resolving."
     gh api graphql -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }' -f id="$THREAD_ID"
     ```
   - **Partially addressed / not addressed / rebuttal not accepted**: reply with what remains or the counter-argument; do not resolve.
   - **Rebuttal accepted**: reply acknowledging the justification, then resolve as above.
   - Accepted rebuttals and addressed threads resolve only after the reply succeeds.
   - Append the **Skill attribution** footer to each reply.

   If it exits 1, present the drafted replies and the resolve list to the user without posting or resolving.

7. If every thread is resolved and your latest review was `CHANGES_REQUESTED` (check `gh pr view $1 --json reviews`), the PR is unblocked from your side: suggest running `/quick-pr-review <owner>/<repo> $1` to re-review and approve the new commit, or run `ghx pr review submit $1 --event APPROVE --body "..."` directly when the user prefers an immediate approval.

## Example Usage

**Scenario 1: Author pushed a real fix**
```
/handle-pr-author-feedback 42
```
Thread: "This function doesn't handle `user` being null."
The diff adds a null guard plus a test.
Verdict: addressed. Reply + resolve.

**Scenario 2: Partial fix**
```
/handle-pr-author-feedback 100
```
Thread asked for a null guard and a test; only the guard was added.
Verdict: partially addressed. Reply listing the missing test; keep the thread open.

**Scenario 3: Sound rebuttal**
```
/handle-pr-author-feedback 77
```
Comment: "Rename `processBatch` to `run`."
Author replies that `run` shadows an existing helper and would break the public API.
Verdict: rebuttal accepted. Reply acknowledging; resolve.

**Scenario 4: Unsupported rebuttal**
```
/handle-pr-author-feedback 88
```
Author replies "done" but the code is unchanged.
Verdict: not addressed. Reply pointing at the unchanged code and the missing change; keep the thread open.

**Scenario 5: Posting disabled**
```
/handle-pr-author-feedback 55
```
`should-post-to-github` exits 1.
Verdicts and drafted replies are presented locally; nothing is posted or resolved.

## Useful Commands Reference

| Command | Description |
|---|---|
| `ghx pr view <pr-number> --json --refresh` | Fetch PR metadata including latest commit, author, and reviews (fresh) |
| `ghx pr threads <pr-number> --ids --state all` | List all review threads with IDs, authors, and resolved state |
| `gh pr diff <pr-number>` | Show the current cumulative diff |
| `gh api repos/{owner}/{repo}/contents/{path}?ref={sha} --jq .content | base64 -d` | Read the current file content at the PR head |
| `ghx pr comment <pr-number> --reply-thread <thread-id> --body "..."` | Reply to a specific review thread |
| `gh api graphql -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }' -f id=<thread-id>` | Resolve a review thread |
| `ghx pr review submit <pr-number> --event APPROVE --body "..."` | Approve the PR after all threads are resolved |
