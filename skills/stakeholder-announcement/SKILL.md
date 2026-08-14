---
name: stakeholder-announcement
description: Draft and post a structured infrastructure progress announcement to relevant stakeholder Slack channels. Use when the user says /stakeholder-announcement, "announce to stakeholders", "post progress update", or wants to share infrastructure changes (GSAs, WIF, cluster provisioning, batch inference milestones) with stakeholder channels.
argument-hint: "[--yes] [--context <summary-file>] <topic>"
---

# Stakeholder Announcement

Drafts a structured progress announcement from recent work context (overall summary, GitHub activity, or explicit description) and posts it to the appropriate stakeholder Slack channels. Delegates posting to **post-slack-message**.

## Prerequisites

- `SLACK_TOKEN`, `SLACK_COOKIE`, and `SLACK_USER` in `.env` (same credentials used by `slack-kb-individual`)
- **post-slack-message** skill available
- Activity context: either an overall summary file (e.g., `{NOTES_DIR}/{YEAR}/{MONTH}/{DAY}.overall.md`), a GitHub activity file, or an explicit topic description from the user

## Inputs

- **topic:** the subject of the announcement (e.g., "batch inference GSA creation", "B300 cluster preparation", "WIF setup complete"). If omitted, inferred from the context file.
- **context:** path to a summary file to draw from. Defaults to today's overall summary if it exists.
- **channels:** target Slack channels. If not specified, inferred from the topic and stakeholder map (see below).
- **mode:** `--yes` for immediate send; otherwise review mode (user confirms before posting).

## Stakeholder Channel Map

Default channel mapping by topic area. The user can override at any step.

| Topic area | Default channel(s) |
|---|---|
| Batch inference / batch API | `#batch-api-discussion`, `#ml-cp-batch` |
| GPU infrastructure / clusters | `#ml-infra-prod`, `#team-ml-infra-gpu` |
| WIF / identity / auth | `#cloud-platform-k8s` |
| Data platform / offline inference | `#proj-data-platform-gpu-offline-inference` |
| Davies / ML control plane | `#ml-cp-eng` |
| General ML infra | `#ml-infra-prod` |

## Steps

### 1. Gather context

Read the context file (overall summary, GitHub activity, or user-provided description). Extract:
- What was done (accomplishments, merged PRs, created resources)
- What stakeholders need to do (actions requested from them, e.g., "create terraform to give GSA access")
- Relevant links (PR URLs, documentation links, issue links)
- Timeline or next steps

### 2. Identify target channels

Determine which stakeholder channels should receive the announcement based on the topic and the stakeholder channel map. Confirm with the user if unsure.

### 3. Compose the announcement

Structure the message using Slack mrkdwn:

```
*<Topic header>*

*What was done:*
- <accomplishment 1>
- <accomplishment 2>

*What we need from you:*
- <action item 1 for stakeholders>

*Links:*
- <PR/issue/doc link 1>

*Next steps:*
- <next step 1>

Note: <any caveats, e.g., "GSAs are likely temporary as we iterate">
```

Adapt the structure to the topic. Omit empty sections. Keep it concise. Mention specific people (`<@USERID>`) when an action is directed at them.

### 4. Post via post-slack-message

Delegate posting to the **post-slack-message** skill. In review mode (default), write the message to a temp file and ask the user to confirm before sending to each channel. In immediate mode (`--yes`), post directly.

If posting to multiple channels, post the same message to each (or tailored variants if the audience differs).

### 5. Report back

Report the posted permalink(s) and channel(s) to the user.

## Example Usage

**Scenario 1: Announcing GSA creation for batch inference**
```
/stakeholder-announcement "batch inference GSA creation" --context 2026/08/13.overall.md
```
Action: Drafts an announcement about 3 GSAs created for data transfer, posts to #batch-api-discussion after user confirmation.

**Scenario 2: Announcing B300 cluster preparation**
```
/stakeholder-announcement "B300 cluster prep" --yes
```
Action: Drafts a brief update about B300 terraform and skypilot PRs being ready, posts immediately to #team-ml-infra-gpu.

**Scenario 3: WIF setup complete**
```
/stakeholder-announcement "WIF setup complete on pw1"
```
Action: Drafts an announcement about WIF being validated end-to-end, posts to #cloud-platform-k8s and #ml-cp-batch after confirmation.

## Useful Commands Reference

| Command | Description |
|---|---|
| `~/.agents/scripts/get-env NOTES_DIR` | Resolve the notes directory for context files |
| `uv run post_slack_message.py --channel <id> --file <path>` | Post announcement to a channel (via post-slack-message) |
