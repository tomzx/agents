---
name: address-pr-comments
description: Pull and address review comments on a GitHub pull request, implementing appropriate changes or explaining why a change won't be made.
argument-hint: <pr-number>
---

Pull the comments about the PR $1 using `gh pr view $1 --comments`.

For each comment, determine whether the feedback is appropriate and actionable.
If it is appropriate and actionable, implement the requested changes in the codebase.
If it is not appropriate or actionable, respond to the comment explaining why the change will not be made.

When addressing the comments, first display its content, then explain your reasoning for accepting or rejecting it, then let me approve or reject your decision
If the decision is approved, either make the change or respond to the comment as appropriate.
