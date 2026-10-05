# Writing Rules

One catalog of prose patterns that make text read as machine-written, vague, or hard to parse.
Skills cite this file by rule ID instead of restating the rules in each place.
It applies to every prose surface the agent writes: articles, documentation, PR and issue descriptions, review comments, Slack messages, email, commit messages, code comments, and the agent's own replies.

## How to use

- When drafting, write clean prose directly. A cleanup pass at the end removes less than writing clean the first time.
- When reviewing or revising, scan for each rule below and fix what you find. Keep the meaning and the intended tone.
- Rule IDs are stable. Cite one as `writing-rules.md#7`. A rule that is removed leaves its number unused, so the later numbers never move.

## Content

1. **Empty "-ing" tails.** "highlighting the importance of", "ensuring that", "showcasing", "fostering". State the action or delete the tail.
2. **Vague attribution.** "experts believe", "studies show", "industry reports suggest". Name the source or cut the claim.
3. **Invented importance.** "it is crucial", "plays a vital role". Say what changes if the thing is absent, or delete the sentence.

## Vocabulary

4. **AI-favored words.** "additionally", "crucial", "delve", "enhance", "foster", "garner", "interplay", "intricate", "pivotal", "showcase", "testament", "underscore", "vibrant". Use the plain word.
5. **Roundabout "is".** "serves as", "stands as", "boasts", "features". Write "is" or "has".
6. **Showy synonyms.** "utilize" becomes "use", "leverage" becomes "use", "facilitate" becomes "help", "numerous" becomes "many", "in the event that" becomes "if".
7. **Jargon and metaphor nouns.** "wedge", "vector", "locus", "nexus", "bedrock", "paradigm", "north star", "flywheel", "gold-plating", "ratchet". Name the concrete thing. `banned-terms.txt` at the skills library root is the canonical list for the most common ones.

## Punctuation and formatting

8. **Em dashes.** Do not use them. Use commas, parentheses, or a new sentence.
9. **Colons as connectors.** A colon is fine before a list or an example, not to join two clauses. Let the second clause stand on its own.
10. **Boldface overuse.** Do not bold every term or name. Bold the few statements that carry the argument.
11. **Inline labels that restate the line.** "**Performance:** performance improved" is a tell. A bold lead-in that names the item and continues with new detail is fine.
12. **Title case headings.** Use sentence case.
13. **Decorative emojis.** Remove them from headings and bullets.
14. **Curly quotes.** Use straight quotes.

## Filler and hedging

15. **Filler phrases.** "in order to" becomes "to", "due to the fact that" becomes "because", "it is important to note that" gets deleted.
16. **Hedging chains.** "could potentially possibly" becomes "may". Take a position when the evidence supports one.
17. **Generic closers.** "the future looks bright", "in conclusion, we have seen". End on a specific fact, action, or takeaway.
18. **Chatbot phrases and flattery.** "I hope this helps", "let me know if you have questions", "great question", "you are absolutely right". Delete them.

## Sentence structure

19. **Passive voice.** Prefer the active voice and name the actor. Passive is fine only when the actor is unknown or does not matter. "queries are validated" becomes "the compiler validates queries".
20. **A weak verb propped up by an adverb.** "runs quickly" becomes "is fast" or the number. "significantly improves" becomes the measured delta.
21. **Dense sentences.** Split a sentence the reader has to backtrack to parse. One idea per sentence.
22. **Unnamed referents.** "this", "that", "these", "those", and "it" when the referent is ambiguous. Name the thing instead.
23. **Dropped articles and verbless fragments.** Write whole sentences. "Parser rejects bad date, exit 2" becomes "The parser rejects a bad date and exits with code 2".

## Artificial patterns

24. **Rule of three.** Do not force items into groups of three. Use the natural number.
25. **Synonym cycling.** Do not rotate labels for one thing ("protagonist", "main character", "hero"). Pick one and repeat it.
26. **False ranges.** "from X to Y" where the ends are not on a meaningful scale. List the items directly.
27. **"Not just X, but Y".** State the point directly instead.
28. **Mannered prose.** Aphorisms, rhetorical fragments, personified code, and figurative verbs ("rides along", "stands on"). Say what you mean.

## Worked example

Before:

> Configuration of the export budget is performed via `budget.json`. It is important to note that running with `--write` should only be done when lowering the budget. If exceeded, CI fails.

After:

> `budget.mjs` reads the committed budget from `budget.json` and counts the files that import protos. If the count exceeds the budget, CI fails. Run `budget.mjs --write` only to lower the budget.
