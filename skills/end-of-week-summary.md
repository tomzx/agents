BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`

# Summarize Slack Activity
Summarize what I discussed on slack based on the notes (`.slack.md` files) taken during the week ending {TODAY} in the directory `{BASE_DIR}`.
Write the response to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.md`.

# Summarize #help-ml-infrastructure Slack Channel Activity
Summarize the activity in the #help-ml-infrastructure Slack channel during the week ending {TODAY}. (use slack MCP server to get the messages)
Write the response to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.help-ml-infrastructure.md`.

Use the following format:
```
# Issue (one entry per issue)

## Link

A link to the slack message.

## Participants
A list of the participants in the conversations.

## Issue
A summary of the issue discussed.

## Key events
A summary of the key events discussed.

## Outcome
A summary of the outcome of the conversations.

# Overall

## Response Quality

A summary of the response quality of the conversations.

## Common Issues

A summary of the common issues identified in the conversations.

## Action Items

A summary of the action items generated from the conversations.
```

# Summarize Colleagues Slack Channel Activity
For each person in the following list !`scripts/get-env COLLEAGUES`, summarize their slack activity during the week ending {TODAY}.
Get the replies from all the thread in which they were discussing to gather additional context.
At the end, list all the channels they contributed to.
Use slack MCP server to get the messages.
Run all those in parallels using subagents.
Write each person's summary to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack/{COLLEAGUE}.md`.

Summarize the overall activity of the colleagues during the week ending {TODAY} in the file `{BASE_DIR}/{YEAR}/weekly/{WEEK}/slack.colleagues.md`.

# Summarize Action Items
Summarize the action items I need to follow up on based on the notes taken during the week ending {TODAY} in the directory `{BASE_DIR}`.
Write the response to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/action-items.md`.

# Summarize Thanks
Summarize the thanks I want to give to others during the week ending {TODAY}.
Write the response to `{BASE_DIR}/{YEAR}/weekly/{WEEK}/thanks.md`.
