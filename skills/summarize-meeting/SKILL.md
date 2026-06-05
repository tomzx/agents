---
name: summarize-meeting
description: Produces a structured meeting summary document from a transcript file. Use when the user says "summarize meeting", "meeting summary", "summarize transcript", or provides a meeting transcript file to process.
argument-hint: "<path-to-transcript-file>"
---

# Summarize Meeting

Reads a meeting transcript file and produces a structured summary covering key topics, decisions, action items, owners, and open questions.

## Prerequisites

- A transcript file (markdown, plain text, or any readable text format) provided by the user
- If no file path is provided, stop and ask the user to supply one

## Steps

1. Read the full transcript file provided by the user.
2. Identify meeting participants from the transcript (speakers, attendees mentioned).
3. Extract the main topics discussed, preserving chronological order where it aids comprehension.
4. For each topic, summarize the discussion in 1-3 sentences capturing the key points.
5. Identify all explicit decisions made during the meeting (decisions with clear consensus or sign-off).
6. Extract all action items with assigned owners and deadlines where mentioned.
7. List any open questions, unresolved issues, or items deferred to future meetings.
8. Write the output to a file named `<transcript-stem>-summary.md` in the same directory as the input transcript (e.g., `transcript.md` becomes `transcript-summary.md`).

## Output Format

```markdown
# Meeting Summary: <Title or Topic>

**Date:** <date if mentioned, otherwise "Not specified">
**Duration:** <duration if mentioned, otherwise "Not specified">
**Participants:** <comma-separated list of names/identifiers>

---

## Topics Discussed

### <Topic 1>

<1-3 sentence summary of the discussion on this topic.>

### <Topic 2>

<1-3 sentence summary of the discussion on this topic.>

## Decisions

- **<Decision 1>:** <brief context or rationale>
- **<Decision 2>:** <brief context or rationale>

## Action Items

| Action | Owner | Deadline |
|---|---|---|
| <What needs to be done> | <Who> | <When, or "Not specified"> |

## Open Questions

- <Question or unresolved issue 1>
- <Question or unresolved issue 2>

## Key Quotes (optional)

> "<Notable or important quote>" — <Speaker>

> "<Notable or important quote>" — <Speaker>

Only include this section if there are quotes that capture important decisions, commitments, or insights not easily paraphrased.
```

## Guidelines

- Omit sections that have no content (e.g., if there are no decisions, skip the Decisions section).
- Merge closely related topics to avoid excessive granularity (aim for 3-8 topics for a typical one-hour meeting).
- Attribute action items to specific people where the transcript identifies them; use "Unassigned" otherwise.
- Do not invent information not present in the transcript. If something is ambiguous, note it as uncertain.
- Preserve the intent and nuance of what was said. Do not editorialize or add opinions.
- If the transcript is very long (multi-hour meeting), group topics under higher-level themes rather than listing every subtopic.

## Example Usage

**Scenario 1: Weekly team standup**
Input: `transcripts/2026-06-04-standup.md` containing a 30-minute standup transcript.
Output: `transcripts/2026-06-04-standup-summary.md` with 4-5 topics, action items with owners, and any blockers noted.

**Scenario 2: Design review meeting**
Input: `meetings/auth-redesign.md` containing a 90-minute design review.
Output: `meetings/auth-redesign-summary.md` with key design decisions, trade-offs discussed, and follow-up tasks assigned.

**Scenario 3: Brief sync with no decisions**
Input: `sync.md` containing a short 10-minute sync.
Output: `sync-summary.md` with topics discussed and open questions, omitting the Decisions and Action Items sections since none were present.

## Useful Commands Reference

No CLI commands required. This skill operates on transcript files provided by the user.
