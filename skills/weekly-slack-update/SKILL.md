---
name: weekly-slack-update
description: Summarize the past week of merged changes on the main/master branch into a ready-to-paste Slack update for stakeholders. Use this whenever the user wants a weekly update, changelog, "what shipped this week", release notes, or a Slack-ready summary of recent git activity, even if they don't say "Slack" explicitly.
---

# Weekly Slack Update

Turn the last week of commits on the default branch into a short, stakeholder-friendly Slack message that the user can copy and paste directly into the Slack message box.

The goal is communication, not a raw git log. Stakeholders care about *what changed for them*, not commit SHAs or refactor details. Translate engineering changes into plain language, lead with the highlights, drop noise, and attach a link to each item so readers can click through for details.
Apply the shared communication guidelines in `skills/communication-guidelines/SKILL.md` when composing the update.

## Steps

1. **Find the default branch.** Don't assume `main`. Detect it:
   ```
   git remote show origin | sed -n 's/.*HEAD branch: //p'
   ```
   Fall back to `main`, then `master`, whichever exists locally if there is no remote.

2. **Make sure history is current.** Fetch so the window reflects what actually shipped:
   ```
   git fetch origin <default-branch> --quiet
   ```
   Use `origin/<default-branch>` as the ref to read from when a remote exists, otherwise the local branch.

3. **Collect the past week's commits.** Read the commit subjects (and bodies when useful) from the last 7 days:
   ```
   git log origin/<default-branch> --since="7 days ago" --no-merges \
     --pretty=format:"%h%x09%s%x09%an"
   ```
   Notes:
   - `--no-merges` keeps the list to real changes. If the repo squash-merges PRs, each PR is already one commit, which is ideal.
   - If the repo uses merge commits for PRs and the non-merge log is noisy (many tiny WIP commits), prefer the merge commits instead: `git log origin/<default-branch> --since="7 days ago" --merges --pretty=format:"%h%x09%s"` and read the PR titles from the merge subjects.
   - If nothing was merged in the window, say so plainly rather than inventing content (see the empty-week example).

4. **Resolve a link for each kept change.** Stakeholders should be able to click through to the change. Capture a URL per commit/PR so you can attach it to its bullet:
   - Squash-merged PRs usually carry the PR number in the subject as `(#123)`. Build the URL from the repo's remote: `https://github.com/<org>/<repo>/pull/123`. Find `<org>/<repo>` with `git remote get-url origin`.
   - Merge commits typically read `Merge pull request #123 from ...`. Use the same URL pattern.
   - If you can't extract a PR number, link to the commit instead: `https://github.com/<org>/<repo>/commit/<full-sha>`. Get the full SHA with `%H` instead of `%h` in the format string.
   - If `gh` is available, you can resolve PR numbers and titles more reliably: `gh pr list --state merged --base <default-branch> --search "merged:>=<date>" --json number,title,url,mergedCommit`.
   - Collapse near-duplicate commits into one bullet, then attach the most representative PR link (usually the feature PR, not a follow-up fix).

5. **Group by Conventional Commit type.** Parse the `type(scope):` prefix on each subject and bucket accordingly. Map types to stakeholder-facing sections using the table below. Commits without a recognizable prefix get classified by reading the subject and inferring intent.

6. **Translate, filter, and write the message.** Rewrite each kept item as a plain-language, user-facing bullet and append its link. Drop anything stakeholders won't care about (see "What to drop"). Then assemble the message using the output template and markdown formatting rules.

7. **Output the message in a copy-paste block.** Present the final message inside a fenced code block so the user can copy it verbatim, then stop. Don't post it anywhere.

## Type to section mapping

| Commit type | Stakeholder section | Keep by default? |
|---|---|---|
| `feat` | New & improved | Yes |
| `fix` | Fixes | Yes |
| `perf` | New & improved (as "faster ...") | Yes |
| `docs` | Usually drop unless user-facing docs | No |
| `refactor`, `style`, `chore`, `build`, `ci`, `test` | Internal, not shown | No |

If a kept section ends up empty, omit the section header entirely. Never show an empty heading.

## What to drop

Stakeholders are not reading a git log. Remove or merge:
- Pure internal work: refactors, test changes, CI/build tweaks, dependency bumps, formatting.
- Reverts that cancel out a change made in the same window (omit both).
- SHAs, branch names, and raw PR numbers in the prose. Keep the link itself (attached at the end of the bullet, see formatting rules), but don't lead the sentence with a SHA or `#123`.
- Jargon and internal component names. Say "search results load faster" not "optimized the ElasticQueryBuilder N+1".
- Near-duplicate commits for the same feature: collapse them into one bullet.

When in doubt, ask: would a non-engineer stakeholder understand and care? If not, cut it or rephrase it.

## Markdown formatting rules

The output is a copy/paste draft for the user, so use regular markdown. Convert to Slack mrkdwn only if the message is posted through the Slack API.

- Slack does not render markdown headers (`#`, `##`, `###`), so use a bold line on its own instead.
- Bold with double asterisks: `**New & improved**`.
- Italic with single asterisks: `*optional note*`.
- Bullets with a leading `- `. Keep them flat.
- Links: include a link on every bullet so readers can click through to the change, using `[details](https://github.com/org/repo/pull/42)`. Put the link at the end of the bullet, never lead with it.
- Inline code with backticks only when naming a real command or flag the audience needs verbatim.
- Keep it short. Aim for a one-line intro plus 3-8 bullets total. If there are many changes, keep only the highlights and add a closing line like "plus a number of smaller fixes and improvements."

## Output template

```
**What shipped this week** (<start date> – <end date>)

**New & improved**
- <plain-language highlight> [details](https://github.com/org/repo/pull/NN)
- <plain-language highlight> [details](https://github.com/org/repo/pull/NN)

**Fixes**
- <plain-language fix> [details](https://github.com/org/repo/pull/NN)

<optional one-line closer, e.g. plus several smaller improvements behind the scenes>
```

Use real dates (the 7-day window) in the header. Omit any section with no items. Attach a link to every bullet. If you genuinely cannot resolve a link for an item, leave that bullet linkless rather than fabricating a URL.

## Examples

**Example 1 — typical week**

Commits (repo `org/shop`):
```
feat(search): add fuzzy matching to product search (#812)
feat(checkout): support Apple Pay (#815)
fix(cart): prevent duplicate items when double-clicking add (#818)
refactor(api): extract pagination helper (#819)
chore: bump eslint to v9 (#820)
perf(images): lazy-load gallery thumbnails (#822)
```

Output:
```
**What shipped this week** (Jun 1 – Jun 5)

**New & improved**
- Product search now handles typos, so customers find what they mean even with a misspelling. [details](https://github.com/org/shop/pull/812)
- You can now check out with Apple Pay. [details](https://github.com/org/shop/pull/815)
- Image galleries load faster by loading thumbnails only as you scroll. [details](https://github.com/org/shop/pull/822)

**Fixes**
- Fixed an issue where double-clicking "Add to cart" could add the same item twice. [details](https://github.com/org/shop/pull/818)
```
(The refactor and chore commits are dropped as internal. Each kept bullet links to its PR.)

**Example 2 — empty week**

No commits in the last 7 days.

Output:
```
**What shipped this week** (Jun 1 – Jun 5)

No customer-facing changes merged this week. The team focused on internal work that doesn't change the product yet.
```

**Example 3 — many small commits, collapse to highlights**

When there are 20+ commits, surface the 3-5 biggest items and roll the rest into a closing line:
```
**What shipped this week** (Jun 1 – Jun 5)

**New & improved**
- Faster page loads across the dashboard. [details](https://github.com/org/shop/pull/901)
- New export-to-CSV option on reports. [details](https://github.com/org/shop/pull/904)

**Fixes**
- Resolved the login loop some users hit on Safari. [details](https://github.com/org/shop/pull/910)

Plus a number of smaller fixes and improvements behind the scenes.
```

## Useful commands reference

| Command | Description |
|---|---|
| `git remote show origin` | Find the remote default (HEAD) branch |
| `git fetch origin <branch> --quiet` | Update local view of the branch |
| `git log <ref> --since="7 days ago" --no-merges --pretty=format:"%h%x09%s%x09%an"` | List the week's commits with author |
| `git log <ref> --since="7 days ago" --merges --pretty=format:"%h%x09%s"` | List the week's merged PRs (merge-commit repos) |
| `git log <ref> --since="7 days ago" --oneline` | Quick scan of the window |
| `git remote get-url origin` | Get `org/repo` to build PR/commit URLs |
| `gh pr list --state merged --base <branch> --search "merged:>=<date>" --json number,title,url` | Resolve merged PRs with their URLs (if `gh` is available) |
