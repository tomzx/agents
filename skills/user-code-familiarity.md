BASE_DIR=!`scripts/get-env NOTES_DIR`

For each user in the list of {USERS} and {ORGANIZATIONS}, use `gh` to retrieve on what they have worked in the past.
Build a profile for each user that indicates their familiarity with the codebase, including:
- Areas of the codebase they have contributed to.
- Types of issues they have resolved.
- Technologies and languages they have experience with in the context of this codebase.

Indicate this information with the time period.

Store this information in `{BASE_DIR}/users/{USERNAME}/codebase-familiarity.md`.
