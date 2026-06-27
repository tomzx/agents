---
issue: "#15"
status: Active
---

# Assumption: The shared review checklist reference can be a plain markdown file in skills/sdlc/references/

**Date:** 2026-06-27
**Status:** Active
**Author:** Skill reviewer

---

## Statement

The shared reference file for the extracted review checklist will be a plain markdown file (not a full SKILL.md with frontmatter), placed in `skills/sdlc/references/`.

## Basis

The existing SDLC shared conventions use plain markdown files for references (e.g., `skills/sdlc/references/shared.md`). Keeping the same format aligns with established patterns and avoids unnecessary overhead of frontmatter parsing for a reference document.

## Confidence

**Level:** Medium

The pattern exists in the same directory, but it is not confirmed that all downstream tools and skills that will reference this file exclusively require the SKILL.md format.

## Risk if Wrong

**Impact:** Medium

If tools processing the reference require SKILL.md frontmatter (e.g., for discovery, classification, or skill loading), a plain markdown file may be invisible or misprocessed. This would require re-formatting as a SKILL.md and updating all references.

## Validation Plan

**Method:** Review existing shared references (`skills/sdlc/references/`) to confirm they are plain markdown. Verify with the skill library maintainer during NFR-03 review that a plain markdown file is acceptable.
**Owner:** Implementer
**By:** Before merging the refactoring PR

## Related

- Requirements FEAT-0001: NFR-02 (conventions alignment), NFR-03 (maintainer review)
- Open question in questions.md: shared reference format
