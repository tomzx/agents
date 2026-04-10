BASE_DIR=!`scripts/get-env ISSUES_DIR`

Pull the information and comments about the issue $1 using `gh issue view --comments`.
Write the raw output of the command to `{BASE_DIR}/{REPOSITORY}/{ISSUE_NUMBER}/issue.md`.

Pull the codebase for the repository using `gh repo clone` in a directory under `src/{owner}/{repository}`.
Make sure that the trunk branch (main/master) is checked out and up to date.

Given the codebase, the issue description, and any discussion within the issue comments, determine if there is enough information to implement the issue.
If there is not enough information, ask for more information by using `gh issue comment`.
If there is enough information, create a plan to implement the issue.

Write the plan to `{BASE_DIR}/{REPOSITORY}/{ISSUE_NUMBER}/prepare-issue.md`.

The plan should be in the following format (each section as a bullet point list):

```
---
created_at: {now in iso 8601 format}
issue: $1 (link to issue)
---

# Summary

A high level overview of what needs to get done.

# Expectations and Assumptions

A list of expectations and assumptions about the issue.

# Current State

A summary of the current state of the codebase related to the issue.

# Related Issues

A list of related issues that may impact the implementation of the issue.

# Information Sufficiency Assessment

An evaluation of whether there is enough information to implement the issue.

# Open Questions

A list of open questions that need to be answered before implementation can begin.

# Implementation Plan

A detailed plan to address the issue.
```
