BASE_DIR=!`scripts/get-env NOTES_DIR`
TODAY=`date +%Y-%m-%d`

# Summarize GitHub Activity
Call `$HOME/repos/git/personal-automation/others/summarize-github-activity tomzx {TODAY} {TODAY} Shopify,shop`.
Write the output to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.github.md`.

# Summarize Slack Activity
Summarize what I discussed on slack on {TODAY}?
Write the response to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.slack.md`.

The slack summary should be in the following format (each section as a bullet point list):

```
# Summary

A summary of the key conversations.

# Key Conversations

A list of the key conversations (including a link to the conversation).

# Action Items Generated

A list of the action items generated.
```

Use my slack activity to identify who I collaborated with and what I want to thank them for.

# Summarize overall activity
Summarize my overall activity on {TODAY}?
Write the response to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.overall.md`.

The overall summary should be in the following format (each section as a bullet point list):

```
# Accomplishments

A summary of what I accomplished.

# Decisions

A summary of the decisions I made.

# Blockers/Waiting for

A summary of what I was blocked by or waiting for.

# For Your Information

A summary of what I should let others be aware of.

# Need to Discuss

A summary of what I need to discuss with others.

# Thanks

A summary of what I want to thank others for, organized by person.

# Next Steps

A summary of what I need to do next.
```

Avoid repeating the same information said differently within the same section.

# Timeline
Using the information collected, create a timeline of the day.

Write the response to `{BASE_DIR}/{YEAR}/{MONTH}/{DAY}.timeline.md`.

The timeline should be in the following format (each section as a bullet point list):

```
# Timeline

* Timestamp - Activity
```

# Standup
Generate information to share in the next day's standup.
Write the response to `{BASE_DIR}/{YEAR}/{MONTH}/{NEXT_WORKDAY}.standup.md`.

The standup should be in the following format (each section as a bullet point list):

```
# What I did yesterday

A summary of what I did yesterday.

# What I will do today

A summary of what I will do today.

# Blockers/Waiting for

A summary of what I am blocked by or waiting for.

# For Your Information

A summary of what I should let others be aware of.

# Thanks

A summary of what I want to thank others for, organized by person.
```

Each section should be at most 5 bullet points.
