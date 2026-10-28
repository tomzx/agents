---
name: create-slack-announcement
description: Draft a Slack announcement in regular markdown, ready to copy-paste. Use when the user says /create-slack-announcement, "draft a Slack announcement", "write a Slack announcement", "prepare a Slack message", or wants announcement text formatted for immediate paste into Slack.
---

# Create Slack Announcement

Drafts a Slack announcement in regular markdown so the output can be copied and pasted directly. The announcement is presented inside a code block to preserve formatting during copy. Optionally delegates posting to **post-slack-message** if the user wants to send it directly, converting the draft to Slack mrkdwn at that point.

## Prerequisites

- A topic or context for the announcement (provided inline, from a file, or gathered from recent work)
- If posting directly: **post-slack-message** skill available, plus `SLACK_TOKEN` in `.env`
- Apply the shared communication guidelines in `skills/communication-guidelines/SKILL.md` when composing the announcement.

## Inputs

- **topic:** the subject of the announcement (e.g., "new deployment process", "API v2 launch", "scheduled maintenance window"). Can be a brief description or a detailed context file.
- **audience:** who the announcement is for (e.g., engineering team, all-hands, specific channel). Used to calibrate tone and detail level.
- **context:** optional path to a summary file, GitHub activity file, or notes to draw from. If omitted, the user describes the announcement verbally.
- **channel:** optional target Slack channel. If provided, the skill can delegate posting to **post-slack-message** after the user reviews the draft.
- **action items:** optional list of things recipients need to do (e.g., "update your CLI", "review the PR by Friday").

## Markdown Formatting Rules

The user reads and copies this draft in regular markdown, so use standard markdown syntax. Slack mrkdwn is only applied later, when the agent posts the message through the Slack API. Slack does not render markdown headers, so use a bold line on its own instead of `#`.

| Element | Markdown |
|---|---|
| Bold | `**bold text**` |
| Italic | `*italic text*` |
| Strikethrough | `~~strikethrough~~` |
| Link with label | `[label](https://example.com)` |
| Bare link | `https://example.com` |
| User mention | `@name` |
| Channel mention | `#channel-name` |
| Group mention | `@here` or `@channel` |
| Bullet list | `- item` |
| Numbered list | `1. item` |
| Inline code | `` `code` `` |
| Code block | ` ``` code ``` ` |
| Section header | `**Header**` on its own line (Slack does not render `#` headings) |
| Divider | `---` on its own line |
| Line break | Blank line between paragraphs |

**Critical rules:**
- Use `**double asterisks**` for bold.
- Use `[text](url)` for links.
- Use a bold line on its own for section headers; Slack does not render `#` headings.
- Separate sections with a blank line.
- Keep lines under 4000 characters (Slack's message limit).
- Mentions written as `@name` or `#channel` are plain text after the paste; the user types the real mention in Slack if the message needs one.

## Steps

### 1. Gather context

Collect information for the announcement from the user's description, a context file, or recent work notes. Extract:
- What is being announced (feature launch, process change, maintenance, milestone)
- Why it matters to the audience (impact, benefit, urgency)
- What recipients need to do (action items, deadlines)
- Relevant links (PRs, docs, issues, dashboards)
- Timeline or key dates
- Any caveats or notes

If the user provides a vague topic, ask targeted questions to fill in the gaps before drafting.

### 2. Determine the announcement type

Identify the type to select the right structure:

| Type | When to use |
|---|---|
| Launch / rollout | New feature, product, or tool is available |
| Process change | How the team works is changing |
| Maintenance / incident | Scheduled downtime, degraded service, post-mortem |
| Milestone / progress | Significant achievement, phase completion |
| FYI / informational | Awareness without action required |
| Action required | Recipients must do something by a deadline |

### 3. Compose the announcement

Write the announcement in regular markdown following the template for the identified type (see Templates below). Apply every formatting rule from the table above.

**Drafting checklist:**
- All bold text uses `**double asterisks**`
- All links use `[label](url)` format
- Headers use a bold line on its own; no `#` headings
- Mentions use `@name` or `#channel`
- Sections separated by blank lines
- Bullet lists use `-` prefix
- No Slack mrkdwn syntax (`*bold*`, `<url|label>`, `<@USERID>`, `<!here>`)

### 4. Present for copy-paste

Output the announcement inside a fenced code block so the user can select and copy it with formatting preserved:

```
Here's your announcement, ready to copy-paste into Slack:

```markdown
<announcement content here>
```

Want me to post this to a specific channel? I can send it via /post-slack-message.
```

The code block ensures the agent's output rendering does not alter the markdown. The `markdown` language tag is decorative and helps the user identify the block.

### 5. Offer to post (optional)

If the user provided a target channel or asks to post, delegate to **post-slack-message** in review mode so the user can confirm before sending. Convert the markdown draft to Slack mrkdwn before posting, because the Slack API renders mrkdwn. If the user says no, stop here, the draft is ready for manual paste.

## Templates

### Launch / rollout

```
**<Feature name> is now available**

<1-2 sentence summary of what launched and why it matters>

**What's new:**
- <capability 1>
- <capability 2>

**What you need to do:**
- <action item 1 with deadline>
- <action item 2>

**Links:**
- [Documentation](https://example.com)
- [Pull request](https://github.com/org/repo/pull/123)

Questions? Reach out in #channel-name or ping @name.
```

### Process change

```
**<Process name> change starting <date>**

Starting <date>, <one-sentence description of the change>.

**What's changing:**
- <old behavior> -> <new behavior>
- <old behavior> -> <new behavior>

**Why:**
<one paragraph explaining the motivation>

**What you need to do:**
- <action item 1>
- <action item 2>

**Timeline:**
- <date>: <milestone>
- <date>: <milestone>

[Read the full announcement](https://example.com)
```

### Maintenance / incident

```
**<Service> maintenance on <date> from <start> to <end>**

<service> will be <unavailable / degraded> during a scheduled maintenance window.

**Impact:**
- <what will be affected>
- <expected duration>

**What to expect:**
- <behavior during maintenance>

**If you experience issues after the window:**
- Report in #channel-name or contact @name

No action needed before the maintenance window.
```

### Action required

```
**Action required: <what recipients must do> by <deadline>**

<one paragraph explaining what needs to happen and why>

**What you need to do:**
1. <step 1>
2. <step 2>
3. <step 3>

**Deadline:** <date>

**Questions?** Post in #channel-name or reach out to @name.
```

### FYI / informational

```
**FYI: <subject>**

<one paragraph summary>

**Key points:**
- <point 1>
- <point 2>

No action needed. See [details](https://example.com) if you're curious.
```

### Milestone / progress

```
**<Milestone title>**

<one paragraph describing the achievement>

**What was done:**
- <accomplishment 1>
- <accomplishment 2>

**What's next:**
- <next step 1>
- <next step 2>

[Related PR](https://github.com/org/repo/pull/123)
```

## Tone Guidelines

- Match the audience: engineering teams get technical detail, all-hands gets high-level summary.
- Be concise: Slack is scanned, not read. Prefer short bullets over paragraphs.
- Lead with the headline: the first line should tell the reader what this is about.
- Be direct about action items: use "you need to" not "we'd appreciate it if you could."
- Include deadlines explicitly: "by Friday, August 15" not "soon."
- Mention specific people with `@name` when an action is directed at them.
- Use `@here` sparingly and only when the announcement needs immediate attention.

## Output Format

The skill always produces:

1. A fenced code block containing the announcement in regular markdown, ready to copy-paste.
2. A brief note offering to post via **post-slack-message** if a channel was specified.

## Example Usage

**Scenario 1: Feature launch**
```
/create-slack-announcement "new CLI deploy command is live" --audience engineering --channel #eng-updates
```
Action: Drafts a launch announcement with what's new and action items, presents it in a code block, offers to post to #eng-updates.

**Scenario 2: Process change from a notes file**
```
/create-slack-announcement "code review SLA change" --context 2026/08/14.overall.md
```
Action: Reads the notes file, drafts a process change announcement with old/new behaviors and timeline, presents for copy-paste.

**Scenario 3: Quick FYI**
```
/create-slack-announcement "staging environment is back up after the incident"
```
Action: Asks 1-2 clarifying questions, drafts a short FYI announcement, presents for copy-paste.

**Scenario 4: Action required with deadline**
```
/create-slack-announcement "everyone needs to rotate their API keys by Aug 20"
```
Action: Drafts an action-required announcement with numbered steps and explicit deadline, presents for copy-paste.

## Useful Commands Reference

No CLI commands required for drafting. The skill produces formatted text for copy-paste. If the user opts to post:

| Command | Description |
|---|---|
| `/post-slack-message --channel <id> --file <path>` | Post the drafted announcement via post-slack-message. |
