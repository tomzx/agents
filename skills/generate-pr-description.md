---
argument-hint: [repository] [issue]
description: Generate a PR description based on changes. If a repository/issue is provided, use its description to assess issue completeness.
---

Generate a PR description using the follow changes.

!`git diff $(gt parent)..HEAD` (use `gt`, which is the graphite CLI)

If a repository/issue is provided, use `gt issue view $2 --repo $1` to get the issue details and use its description to assess issue completeness as part of the PR description.

The PR description should be in the following format:

```
# What

A summary of the changes in this PR.
Use the present tense.

# Why

A summary of the reason for the changes in this PR.

# How to test

A summary of how to test the changes in this PR.

# Acceptance criteria covered

A summary of the acceptance criteria covered by this PR.

# References

- https://github.com/$1/issues/$2
- To be filled by the user (if the above link is not provided)
```

The returned response should be returned within a markdown code block.
Each sentence should be its own line.
Use bullet points whenever appropriate.
