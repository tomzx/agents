---
name: handle-issue-comment
description: Reply to a comment on a GitHub issue using the codebase, issue description, and comment history as context.
argument-hint: <issue-url>
---

# Goal

Reply to a comment on an issue appropriately, using the codebase, issue description and comment history as context.

# Steps
* Get all the comments to build context using `gh issue view --comments $1`.
* Pull the codebase for the repository using `gh repo clone`.
* Reply to the comment appropriately, using the codebase, issue description and comment history as context.
