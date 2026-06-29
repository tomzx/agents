---
name: create-message
description: Improve a message the user wants to send by removing negative tone, providing positive formulation, and adding actionable suggestions when relevant.
---

# Write Message

Takes a draft message and improves it by removing negative tone, reformulating with positive language, and appending actionable suggestions where appropriate.

## Prerequisites

- **Draft message**: The message the user wants to send (provided inline or in a file)
- **Recipient** (optional): Who the message is for (e.g., "a colleague", "a manager", "a client"), used to calibrate tone
- **Context** (optional): Any background that helps understand the intent (e.g., "they missed a deadline", "I want to decline a meeting")

## Steps

1. Read the draft message carefully and identify the core intent.
2. Scan for negative tone markers: passive-aggression, blame, criticism without constructive framing, defensiveness, dismissiveness, or vague complaints.
3. Reformulate each negative passage using positive language that preserves the original intent.
4. Identify any places where actionable suggestions would strengthen the message, and add them.
5. Review the revised message for tone consistency, clarity, and brevity.

## Tone Rewrite Rules

**Remove:**
- Blame language ("you failed to", "you didn't", "you never")
- Passive-aggressive framing ("as I'm sure you're aware", "per my last email")
- Vague complaints ("this isn't good enough", "this needs to be better")
- Defensiveness ("I was just trying to", "that's not what I meant")
- Dismissive language ("whatever you think", "it doesn't matter to me")
- Sarcasm or backhanded compliments

**Replace with:**
- Ownership language ("I'd like us to", "we could", "I suggest")
- Specific, observable descriptions ("the report arrived on Friday, past the Wednesday deadline" instead of "you were late again")
- Constructive framing ("here's what would help", "moving forward, I'd recommend")
- Direct requests ("could you", "would it be possible to")
- Collaborative tone ("let's", "how about we")

## Actionable Suggestions

Add concrete suggestions when the message:
- Requests a change in behavior (suggest what specifically to do instead)
- Reports a problem (suggest one or more solutions)
- Sets expectations (suggest clear next steps with timelines)
- Expresses disagreement (suggest an alternative approach)

Suggestions should be:
- Specific and concrete (not "do better" but "send the summary by Thursday noon")
- Realistic and achievable
- Framed as options where appropriate ("we could A or B")
- Limited to 1-3 per message to avoid overwhelming the recipient

## Output Format

```markdown
## Improved Message

[The rewritten message in full]

---

## Changes Made

- **Tone adjustments**: [list of negative elements removed and what they were replaced with]
- **Actionable suggestions added**: [list of suggestions added, or "None needed" if the message was already actionable]
- **Preserved intent**: [one sentence confirming the core message remains the same]
```

## Example Usage

**Scenario 1: Frustrated follow-up**
Draft: "You still haven't sent me the report. I've asked three times now and I'm getting tired of chasing you."
Recipient: colleague
Improved: "I haven't received the report yet. Could you send it by end of day Wednesday? If something is blocking you, let me know and I can help unblock it."

**Scenario 2: Declining a request**
Draft: "I don't have time for this. You should have asked me earlier."
Recipient: teammate
Improved: "I won't be able to take this on this week due to my current commitments. For future requests, reaching out by Monday would give me the best chance to fit it in."

**Scenario 3: Feedback on work**
Draft: "This design is confusing and doesn't make sense. I can't believe we're considering this."
Recipient: design team
Improved: "I have some concerns about the design's clarity. Specifically, the navigation flow between steps 2 and 3 feels unclear. Could we explore adding a progress indicator or transitional labels? I'd be happy to walk through a specific example in our next review."

## Useful Commands Reference

No CLI commands required. This skill operates on content provided in context.
