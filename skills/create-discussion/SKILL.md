---
name: create-discussion
description: Create a GitHub Discussion (for example a feature request in a repository that routes them to Discussions instead of issues) with background, prioritized acceptance criteria (Must/Should), and a justified time budget.
argument-hint: "[repository]"
---

# Create GitHub Discussion

Creates a structured GitHub Discussion in the specified repository with background, prioritized acceptance criteria (Must/Should), and (for private repositories) a justified time budget.
Use it for repositories that route requests (typically feature requests) to GitHub Discussions instead of issues, so the request arrives in the channel the maintainers asked for.
This skill is standalone: it is the Discussion counterpart to `/create-issue` and does not participate in the issue-driven SDLC pipeline.

## Prerequisites

- Apply the shared SDLC conventions in `skills/sdlc/references/shared.md`.
- If no argument is provided, operate on `$REPO`.
- `gh` CLI authenticated with write access to the target repository, and Discussions enabled for it
- Repository name in `owner/repo` format (`$1`), or omitted to use the repository in the current working directory

### Skill attribution (GitHub)

Before creating the discussion with `createDiscussion`, read [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md) and append the **Created with** footer for `SKILL_DIR` = `create-discussion` to the discussion body.
The SDLC phase footer does not apply: a discussion is not issue-driven and has no issue number.

### Communication guidelines (outbound text)

Before composing any text posted or drafted on the user's behalf, apply [`communication-guidelines/SKILL.md`](../communication-guidelines/SKILL.md).

## Formatting

- Do not use curly or typographic quotation marks in any text you write for the discussion (title, body, sections, lists, or examples). Use straight ASCII double quotes (`"`) and straight apostrophes (`'`) only.
- Write one sentence per line throughout the discussion body. Lists and checklist items follow their own format, but any prose paragraph should have each sentence on its own line.

## Acceptance Criteria

- Split into **Must** (the exit gate, the minimum bar for "done") and **Should** (deferrable without blocking the request).
- Aim for the smallest set that proves the request is resolved. If **Must** grows beyond roughly 5 items, the request is probably too broad and should be split rather than padded with more criteria.
- Each criterion must be testable (a concrete test can be written for it) and specific about *what*, not *how*.
- Put the happy path in **Must**. Move edge cases, error handling, and polish to **Should** unless they are part of the core definition of done.
- Omit the **Should** subsection entirely when there are no deferrable items. Do not invent nice-to-haves just to fill it.

## Time Budget

- Give a **total** plus a short **breakdown** so the estimate can be defended and challenged rather than asserted.
- Weight the estimate toward **planning and evaluation**, not implementation. With AI-assisted development, writing the code is nearly free and instant; the real cost is understanding the problem, designing the solution, evaluating alternatives, and validating the result. Treat implementation sub-estimates as negligible unless the work is genuinely large (e.g. multi-day migrations, hardware-bound work, or mass repetitive changes).
- The breakdown should list the activities that actually limit delivery: research, design, feasibility evaluation, review, and validation/testing.
- Each breakdown line pairs a work area with a sub-estimate and a one-line cost driver (e.g. "unfamiliar codepath", "needs a design decision", "requires cross-team input").
- List the **assumptions** the estimate depends on (what is already in place, what is out of scope). When an assumption breaks, the estimate should be revisited.
- Keep it rough: half-day precision is fine. Do not over-engineer the breakdown for small requests (a single line is acceptable when the work is genuinely one lump).

## Summary

- If the description (background plus any context you would write) exceeds 200 words, add a **Summary** section before the **Background** section.
- The summary must be less than 200 words, at most 5 sentences, with one sentence per line, and concisely summarize the ask: what is needed and why, in plain terms.
- If the description is 200 words or fewer, omit the Summary section entirely.

## Discussion Body Scope

- Keep the discussion body focused on summary (when applicable), background, acceptance criteria, and time budget.
- If you have detailed code analysis (e.g. files examined, codepaths traced, root-cause reasoning, relevant snippets), do not add it to the body. Instead, post it as a follow-up comment after the discussion is created.
- The body should give readers enough context to discuss the request; the follow-up comment provides the deeper analysis for those who want the reasoning.
- Discussions do not support labels or issue types. Do not attempt to apply either.

## Steps

1. **Search for duplicates** first, before any codebase investigation. The report alone supplies the keywords (error messages, command, skill, or feature names, component names). Search Discussions and issues, because a duplicate may already exist in either channel:
   ```
   gh api graphql -f query='
   query($q:String!){ search(query:$q, type:DISCUSSION, first:10){ nodes{ ... on Discussion{ number title url } } } }
   ' -f q='repo:{owner}/{repo} <keywords>'

   ghx issue list --repo $1 --search "<keywords>" --state all --limit 10
   ```
   If a duplicate is found, stop and inform the user with the existing URL. Do not create a new discussion unless the user confirms it is not a duplicate.
2. If the request is a feature request, determine the current version on the default branch (main/master) so the discussion records what commit the request was filed against. Use `gh api repos/{owner}/{repo} --jq '.default_branch'` to find the default branch, then get the short SHA via `gh api repos/{owner}/{repo}/commits/<default_branch> --jq '.sha[0:7]'`.
3. Determine if the repository is public or private using `gh repo view [--repo $1] --json isPrivate --jq '.isPrivate'`. A public repository is treated as open source; omit the **Time budget** section. A private repository includes it.
4. **Resolve the repository node ID and the target category**. First confirm Discussions is enabled:
   ```
   gh api repos/{owner}/{repo} --jq '{id: .node_id, has_discussions: .has_discussions}'
   ```
   If `has_discussions` is false, stop and tell the user the repository does not accept discussions.
   Then list the categories:
   ```
   gh api graphql -f query='
   query($owner:String!,$name:String!){
     repository(owner:$owner,name:$name){ discussionCategories(first:50){ nodes{ id name slug } } }
   }' -f owner=<owner> -f name=<repo>
   ```
   Pick the target category in this order:
   1. The category the user named.
   2. The category in the repository's feature-request contact link, read from the issue-template config (its URL is `/discussions/categories/<slug>` or `/discussions/new?category=<slug>`):
      ```
      gh api "repos/{owner}/{repo}/contents/.github/ISSUE_TEMPLATE/config.yml" --jq '.content' 2>/dev/null | base64 -d
      ```
   3. The first category whose `slug` or `name` matches ideas/feature/suggestions (case-insensitive).
   4. The first category.
   If there are no categories, stop and tell the user.
5. **Compose the body and create the discussion.** Include a **Version** section with the default-branch version determined in step 2 for feature requests (omit for requests that are neither). Omit `--repo`-style flags: the mutation takes the repository node ID directly. Append the attribution footer resolved per [`github-post-attribution/SKILL.md`](../github-post-attribution/SKILL.md):
   ```
   gh api graphql -f query='
   mutation($repoId:ID!,$categoryId:ID!,$title:String!,$body:String!){
     createDiscussion(input:{repositoryId:$repoId, categoryId:$categoryId, title:$title, body:$body}){
       discussion{ id number url }
     }
   }' -f repoId="<repo_node_id>" -f categoryId="<category_node_id>" -f title="<title>" -f body="$(cat <<'EOF'
   # Summary

   <less than 200 words, at most 5 sentences, one sentence per line, summarizing the ask, only if the description exceeds 200 words; omit this section otherwise>

   # Background

   <context and motivation>

   # Version

   <current default-branch version for feature requests; do NOT wrap in backticks so GitHub renders it as a commit link> (omit when not a feature request)

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

   Created with [create-discussion]({SKILL_FILE_URL}) (`SKILL_SHORT_SHA`)
   EOF
   )"
   ```
   Capture `discussion.id` and `discussion.url` from the response.
6. **Post detailed code analysis as a follow-up comment** (if applicable). If the discussion was informed by code analysis (files examined, codepaths traced, root-cause reasoning, relevant snippets), post that analysis as a comment rather than including it in the body:
   ```
   gh api graphql -f query='
   mutation($discussionId:ID!,$body:String!){
     addDiscussionComment(input:{discussionId:$discussionId, body:$body}){ comment{ url } }
   }' -f discussionId="<discussion_node_id>" -f body="<analysis>"
   ```
   Include the same attribution footer as the body.
7. **Report the result**. Print the discussion URL and note that it has no issue number (it is not part of the issue-driven SDLC pipeline).

## Example Usage

**Scenario 1: Feature request in a repository that uses Discussions**
```
/create-discussion owner/myrepo
```
The repository's issue-template config points feature requests at `/discussions/categories/ideas`. Create the discussion in the `ideas` category with background, the default-branch version, Must/Should acceptance criteria, and (for a private repo) a time budget with breakdown.

**Scenario 2: A question or open-ended proposal**
```
/create-discussion owner/myrepo
```
Create a discussion in the default category with background and acceptance criteria. Omit the Version section since it is not a feature request.

**Scenario 3: User names the category**
```
/create-discussion owner/myrepo
```
User says "put it in the RFC category." Resolve that category by name or slug and create the discussion there.

## Completion Checklist

Before finishing, confirm:

- [ ] Duplicate search ran first, across Discussions and issues (no existing discussion or issue matches)
- [ ] Discussions was enabled and a valid category was used
- [ ] No labels or issue types were applied (discussions do not support them)
- [ ] Summary section included only when the description exceeds 200 words; less than 200 words, at most 5 sentences, one sentence per line
- [ ] Time budget included only for private repos; Should section omitted when empty
- [ ] Detailed code analysis posted as a follow-up comment, not in the discussion body
- [ ] The missing issue number was reported to the user

Self-check the discussion against the [`review-issue` checklist](../review-issue/SKILL.md) and fix what you can, so it is as complete as an issue would be.
There is no `review-discussion` skill; this self-check is the only review pass.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh repo view [--repo <repo>] --json isPrivate --jq '.isPrivate'` | Check if a repository is private |
| `gh api repos/<owner>/<repo> --jq '{id: .node_id, has_discussions: .has_discussions}'` | Get the repository node ID and check whether Discussions is enabled |
| `gh api repos/<owner>/<repo> --jq '.default_branch'` | Get the default branch name |
| `gh api repos/<owner>/<repo>/commits/<branch> --jq '.sha[0:7]'` | Get the short SHA of the default branch (version for feature requests) |
| `gh api graphql -f query='query($owner:String!,$name:String!){repository(owner:$owner,name:$name){discussionCategories(first:50){nodes{id name slug}}}}' -f owner=... -f name=...` | List Discussion categories to pick the target |
| `gh api "repos/<owner>/<repo>/contents/.github/ISSUE_TEMPLATE/config.yml" --jq '.content' \| base64 -d` | Read the issue-template config to find the preferred feature-request category |
| `gh api graphql -f query='query($q:String!){search(query:$q,type:DISCUSSION,first:10){nodes{...on Discussion{number title url}}}}' -f q='repo:<repo> <keywords>'` | Search Discussions for duplicates |
| `ghx issue list --repo <repo> --search "<keywords>" --state all --limit 10` | Search issues for duplicates (a duplicate may be an issue) |
| `gh api graphql -f query='mutation($repoId:ID!,$categoryId:ID!,$title:String!,$body:String!){createDiscussion(input:{repositoryId:$repoId,categoryId:$categoryId,title:$title,body:$body}){discussion{id number url}}}' -f repoId=... -f categoryId=... -f title=... -f body=...` | Create the discussion |
| `gh api graphql -f query='mutation($discussionId:ID!,$body:String!){addDiscussionComment(input:{discussionId:$discussionId,body:$body}){comment{url}}}' -f discussionId=... -f body=...` | Post a follow-up comment with detailed code analysis |
