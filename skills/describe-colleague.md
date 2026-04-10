---
argument-hint: [colleague]
---

BASE_DIR=!`scripts/get-env NOTES_DIR`

Based on slack activity and github activity (use `gh`), generate a profile for {COLLEAGUE}.
Do not read local files.

Write the response to `{BASE_DIR}/colleagues/{COLLEAGUE}.md`.

The response should be in the following format (each section as a bullet point list):

```
# Strengths

A list of the strengths of {COLLEAGUE}.

# Weaknesses

A list of the weaknesses of {COLLEAGUE}.

# Interests

A list of topics that {COLLEAGUE} is interested in.

# Avoids

A list of topics that {COLLEAGUE} avoids.

# Other relevant information

A list of other relevant information about {COLLEAGUE}.
```
