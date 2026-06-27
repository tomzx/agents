---
name: create-issue
description: Create a GitHub issue with background, prioritized acceptance criteria (Must/Should), and a justified time budget.
argument-hint: "[repository]"
---

# Create GitHub Issue

Creates a structured GitHub issue in the specified repository with background, prioritized acceptance criteria (Must/Should), and (for private repositories) a justified time budget so implementers have clear scope and exit criteria.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, operate on `$REPO`.
- `gh` CLI authenticated with write access to the target repository
- Repository name in `owner/repo` format (`$1`), or omitted to use the repository in the current working directory

### Skill attribution (GitHub)

Before creating an issue with `gh issue create`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Created with** footer for `SKILL_DIR` = `create-issue` to the issue body.

When this skill is invoked as part of an `sdlc` pipeline run, also include the **SDLC phase footer** described in `github-post-attribution/SKILL.md` (prepend the `SDLC phase: <phase> (<FEAT-id> #<issue>)` line above the `Created with` line).

## Formatting

- Do not use curly or typographic quotation marks in any text you write for the issue (title, body, sections, lists, or examples). Use straight ASCII double quotes (`"`) and straight apostrophes (`'`) only.

## Acceptance Criteria

- Split into **Must** (the exit gate, the minimum bar for "done") and **Should** (deferrable without blocking the issue).
- Aim for the smallest set that proves the issue is resolved. If **Must** grows beyond roughly 5 items, the issue is probably too broad and should be split rather than padded with more criteria.
- Each criterion must be testable (a concrete test can be written for it) and specific about *what*, not *how*.
- Put the happy path in **Must**. Move edge cases, error handling, and polish to **Should** unless they are part of the core definition of done.
- Omit the **Should** subsection entirely when there are no deferrable items. Do not invent nice-to-haves just to fill it.

## Time Budget

- Give a **total** plus a short **breakdown** so the estimate can be defended and challenged rather than asserted.
- Weight the estimate toward **planning and evaluation**, not implementation. With AI-assisted development, writing the code is nearly free and instant; the real cost is understanding the problem, designing the solution, evaluating alternatives, and validating the result. Treat implementation sub-estimates as negligible unless the work is genuinely large (e.g. multi-day migrations, hardware-bound work, or mass repetitive changes).
- The breakdown should foreground the activities that actually constrain delivery: research, design, feasibility evaluation, review, and validation/testing.
- Each breakdown line pairs a work area with a sub-estimate and a one-line cost driver (e.g. "unfamiliar codepath", "needs a design decision", "requires cross-team input").
- List the **assumptions** the estimate depends on (what is already in place, what is out of scope). When an assumption breaks, the estimate should be revisited.
- Keep it rough: half-day precision is fine. Do not over-engineer the breakdown for small issues (a single line is acceptable when the work is genuinely one lump).

## Steps

1. If the issue is a bug report, ask the user: "Which version are you on?" and wait for their answer before proceeding.
2. If the issue is a feature request, determine the current version on the default branch (main/master) so the issue records what commit the request was filed against. Use `gh api repos/{owner}/{repo} --jq '.default_branch'` to find the default branch, then get the short SHA via `gh api repos/{owner}/{repo}/commits/<default_branch> --jq '.sha[0:7]'`.
3. Determine if the repository is public or private using `gh repo view [--repo $1] --json isPrivate --jq '.isPrivate'`. A public repository is treated as open source; omit the **Time budget** section. A private repository includes it.
4. **Determine the issue type**. Query the repository for available issue types:
    ```
    gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") { issueTypes(first:20) { nodes { name id } } } }'
    ```
    Map the issue content to a type:
    - Bug reports → `Bug`
    - Feature requests → `Feature`
    - Everything else → `Task`
    If the query returns `null` or an empty list, the repository does not support issue types; skip type assignment.
5. **Choose labels and verify they exist**. Determine the desired labels: defaults `not-urgent` and `not-important`, or whatever the user asked for instead. Then query the repository for existing labels:
    ```
    gh label list [--repo $1] --json name --jq '.[].name'
    ```
    Filter the desired labels to only those that exist in the repository. If none of the desired labels exist, create the issue without labels and note which labels were skipped. Do not attempt to create labels.
6. **Search for duplicates** before creating. Using the issue title and keywords, run 2-3 different searches: `gh-cached issue list --repo $1 --search "<keywords from title>" --state all --limit 10`. If a duplicate is found, stop and inform the user with the existing issue URL. Do not create a new issue unless the user confirms it is not a duplicate.
7. Create the issue with the structured body. For bug reports, include a **Version** section with the version the user provided. For feature requests, include a **Version** section with the current default-branch version determined in step 2. Omit `--repo` if no repository was provided (gh will infer it from the cwd). Only include `--label` flags for labels confirmed to exist in step 5:
    ```
    gh issue create [--repo $1] --title "<title>" --body "$(cat <<'EOF'
    # Background

    <context and motivation>

    # Version

    <version reported by user for bug reports, or current default-branch version for feature requests — do NOT wrap in backticks; write it as plain text so GitHub renders it as a commit link> (omit for issues that are neither)

    # Acceptance Criteria

    ## Must

    - [ ] <minimum criterion that defines "done" (testable, specific about what not how)>

    ## Should

    - [ ] <deferrable criterion, e.g. an edge case or polish item>
    <!-- omit the Should subsection if there are no deferrable criteria -->

    # Time budget

    <total estimate>, after which the implementer should reassess or seek help.
    (omit this section entirely for public/open-source repositories)

    Breakdown:
    - <work area>: <sub-estimate> (<one-line cost driver>)
    - <work area>: <sub-estimate> (<one-line cost driver>)
    Weight the breakdown toward planning and evaluation (research, design, review, validation) rather than implementation, which is now nearly free with AI assistance.

    Assumptions: <what the estimate assumes is in place / out of scope>

    ---

    Created with [create-issue]({SKILL_FILE_URL}) (`SKILL_SHORT_SHA`)
    EOF
    )" --label "<label1>" --label "<label2>"
    ```
    Resolve `SKILL_FILE_URL` and the short SHA per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) before running the command. Omit all `--label` flags if no desired labels exist in the repository.
8. **Assign the issue type** (if the repository supports issue types from step 4). After the issue is created, get its `node_id` and set the type:
    ```
    NODE_ID=$(gh api repos/<owner>/<repo>/issues/<number> --jq '.node_id')
    gh api graphql -f query='mutation($id:ID!, $typeId:ID!) { updateIssue(input:{id:$id, issueTypeId:$typeId}) { issue { url issueType { name } } } }' -f id="$NODE_ID" -f typeId="<issue_type_node_id>"
    ```
    Use the `id` of the matching issue type from step 4 (e.g., the Bug type's node ID for bug reports).

## Example Usage

**Scenario 1: Simple bug report**
```
/create-issue owner/myrepo
```
Creates an issue titled "Fix null pointer in user login" with background explaining the crash, Must-have acceptance criteria (the fix plus a regression test), and a justified time budget with a breakdown (if private). Labels: `not-urgent`, `not-important`.

**Scenario 2: Feature request with custom labels**
```
/create-issue owner/myrepo
```
User specifies "this is urgent and important." Apply `urgent` and `important` labels instead of the defaults.

**Scenario 3: Acceptance criteria provided upfront**
```
/create-issue owner/api-service
```
User provides a list of requirements. Convert each into a checklist item, then split them into **Must** (gates "done") and **Should** (deferrable). If most items land in Must, flag to the user that the issue may be too broad and should be split.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh repo view [--repo <repo>] --json isPrivate --jq '.isPrivate'` | Check if a repository is private |
| `gh api repos/<owner>/<repo> --jq '.default_branch'` | Get the default branch name |
| `gh api repos/<owner>/<repo>/commits/<branch> --jq '.sha[0:7]'` | Get the short SHA of the default branch (version for feature requests) |
| `gh api graphql -f query='{ repository(owner:"...", name:"...") { issueTypes(first:20) { nodes { name id } } } }'` | Check available issue types for the repository |
| `gh-cached issue list --repo <repo> --search "<keywords>" --state all --limit 10` | Search for duplicate issues before creating (cached) |
| `gh label list [--repo <repo>] --json name --jq '.[].name'` | List existing label names in the repository |
| `gh issue create --repo <repo> --title "..." --body "..." --label "..."` | Create a new issue with labels |
| `gh api repos/<owner>/<repo>/issues/<number> --jq '.node_id'` | Get the issue's node ID for type assignment |
| `gh api graphql -f query='mutation($id:ID!,$typeId:ID!){updateIssue(input:{id:$id,issueTypeId:$typeId}){issue{issueType{name}}}}' -f id=... -f typeId=...` | Set the issue type after creation |
