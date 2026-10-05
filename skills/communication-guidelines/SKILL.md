---
name: communication-guidelines
description: Shared guidelines for writing concise, high-signal outbound communication the agent posts or drafts on the user's behalf, covering GitHub PR and issue comments, inline review comments, review reports, thread replies, PR and issue descriptions, Slack messages and announcements, and email. Other skills reference this instead of restating concision and tone rules.
---

# Communication Guidelines

Shared baseline for every piece of text the agent writes on the user's behalf, whether the agent posts it or returns it for the user to send.
Other skills reference this file instead of restating concision and tone rules.
This is a reference, not a workflow: no command to run and no artifact to produce.

## When to use

- Any skill that composes text a human will read on GitHub, Slack, or email.
- Loaded by name from other skills, for example "apply `skills/communication-guidelines/SKILL.md` before composing the body".
- Loaded directly when the user asks to post a comment, reply on a PR or issue, write a PR or issue description, or draft a message.

## Core principles

- Be concise.
- Use plain language: short, direct sentences in the active voice, with common words over jargon and buzzwords.
- Write literally, with no metaphors, idioms, or other figurative language the reader must decode.
- Lead with the point: the ask, finding, decision, or answer is the first sentence.
- Do not use em-dashes, use commas or parentheses instead.
- One sentence per line.
- Write the shortest form that carries the signal, then delete every sentence that does not change what the reader knows or does.
- One idea per message, comment, or thread reply.
- Do not restate what the code, diff, linked issue, or the comment being replied to already says.
- Be concrete: name the file, line, symbol, and the specific change.
- Give the reader the reason they need to act, not the reasoning trail that produced it.
- Prefer a link to the artifact (issue, ADR, spec, dashboard) over re-explaining its content.
- Mark severity and optionality so the reader can prioritize, using MUST/SHOULD/MAY or an explicit "nit".
- Assume competence and criticize the work, not the person.
- For tone rewrites, use [`create-message`](../create-message/SKILL.md).
- For the full catalog of patterns to remove (AI-favored words, filler, hedging, punctuation, and artificial patterns), apply [`references/writing-rules.md`](references/writing-rules.md).

## Length budgets

These are ceilings, not targets. Shorter is almost always better.

| Surface | Budget |
|---|---|
| Inline review comment | 1-3 sentences, plus a code suggestion when useful |
| Thread reply | 1-2 sentences |
| Top-level PR or issue comment | Lead paragraph under about 4 lines, then supporting detail only if needed |
| Review report | Findings terse, with detail only where it changes a decision |
| PR or issue description | Structured sections, bullets over paragraphs |
| Slack message | Scannable, short bullets, no long unbroken text |
| Email | The ask first, then context |

## Cut fluff on sight

- Preamble and closers such as "I took a look at this", "Let me know if you have questions", or "Hope this helps".
- Filler praise and flattery such as "Great work" or "Nice catch" when it does not change the review.
- Filler that delays the point, such as "Quick question" or "Just a thought".
- Restating the diff, the code, or the comment being answered.
- Hedging chains and qualifiers that add no decision information.
- Context already present in the description or a linked artifact.
- Self-narration about how the agent arrived at the conclusion.
- Multiple sign-offs, since one attribution footer is enough.

## Channel notes

### GitHub comments and reviews

- Put the verdict or finding first and the supporting reasoning after.
- Anchor an inline comment to the smallest code range that makes the point.
- Do not post a comment that only says the code looks fine, because routine approval belongs in the review verdict, not as extra comments on the diff.
- Prefix findings with severity and the checklist section when the skill's format requires it, as in [`review-pr`](../review-pr/SKILL.md).
- For descriptions, write what, then why, then design decisions, with no filler sections.

### Slack

- Write for scanning: short bullets, bold the ask, and keep one topic per message.
- Move long exchanges into a thread instead of posting a wide message in the channel.
- Add detail as thread replies rather than editing the original message.

### Email

- State the ask in the subject and again in the first line.
- Link the artifact instead of pasting it.

## Attribution

- GitHub text carries the footer defined in [`github-post-attribution`](../github-post-attribution/SKILL.md).
- Slack messages and email carry no attribution footer.
- Do not add other signatures, model notes, or recaps of the conversation.

## Examples

Inline comment, too verbose:
"Great work here! I was reading through this and it looks like the function may not handle the case where the input is None. It might be worth considering adding a guard, because otherwise it could potentially raise an AttributeError. What do you think?"

Inline comment, succinct:
"This raises AttributeError when `input` is None. Add a guard, or document that None is a precondition."

Thread reply, too verbose:
"Thanks for the feedback, that is a good point. I went ahead and made the change you suggested and also updated the tests. It should be pushed now."

Thread reply, succinct:
"Done: added the null guard and a regression test in abc1234."

Slack message, too verbose:
"Hey team, quick update on the migration work. Over the last few days I have been working through the schema changes and I am happy to report that the first phase is now complete. Next up we will be looking at the backfill."

Slack message, succinct:
"Migration phase 1 done (schema changes merged). Next: backfill, starting Monday."

## Notes

- Skills do not declare dependencies in front matter, so consuming skills must read this file or follow a one-line pointer in their own `SKILL.md`.
