---
name: review-article
description: Review an article for accuracy, clarity, structure, sourcing, and audience fit.
---

# Review Article

Audits an article and reports findings across six categories: accuracy, clarity, structure, sourcing, audience fit, and style.
Each finding is prioritized with 🔴 MUST fix, 🟡 SHOULD fix, or 🟢 MAY fix.

## Prerequisites

- Article provided in context or as a file path to read
- Target audience (if known, improves audience-fit check)
- Relevant sources (optional, improves accuracy check)

## Steps

1. Read the article thoroughly.
2. Cross-reference claims against provided sources if available.
3. Identify issues in each category below.
4. Prioritize each finding: 🔴 MUST, 🟡 SHOULD, 🟢 MAY.
5. Report findings using the output format. Omit categories with no findings.

## Review Checklist

### Accuracy
- Are factual claims correct and verifiable?
- Are statistics, numbers, and dates accurate?
- Are technical concepts described correctly?
- Are attributed claims accurately representing their sources?

### Clarity
- Does the article open with the most important point, not background?
- Is every sentence necessary, with no filler or padding?
- Are abstract points anchored with concrete examples, numbers, or comparisons?
- Is jargon avoided or defined on first use?

### Structure
- Does the article follow a logical progression from hook to takeaway?
- Are sections focused on a single idea each?
- Is there a clear through-line connecting all sections?
- Does the ending provide something actionable or memorable (not a weak summary)?

### Sourcing
- Are claims attributed to sources with hyperlinks, not just textual citations?
- Are all hyperlinks verified (no 404s or broken references)?
- Are opinions clearly distinguished from sourced facts?
- Are sources credible and relevant?

### Audience Fit
- Is the tone appropriate for the stated or implied audience?
- Is the depth calibrated: neither too shallow nor too detailed?
- Does the article assume appropriate prior knowledge?
- Would the target audience find this valuable?

### Style
- Is each sentence on its own line in the markdown source?
- Are em-dashes avoided in favor of commas or parentheses?
- Is the writing concise without hedging every claim?
- Is the same point restated across multiple sections (redundancy)?

## Output Format

```markdown
## Summary

🔴 / 🟢 <Overall assessment in one sentence.>

## Accuracy

<Findings with 🔴/🟡/🟢 priority, or "No issues found.">

## Clarity

<Findings or "No issues found.">

## Structure

<Findings or "No issues found.">

## Sourcing

<Findings or "No issues found.">

## Audience Fit

<Findings or "No issues found.">

## Style

<Findings or "No issues found.">
```

## Outcome

If `$OUTCOME_YAML` is set, emit your verdict there per `skills/sdlc/references/shared.md`:

| Verdict | When |
|---|---|
| `approved` | No blocking findings; the subject passes review |
| `changes-requested` | Findings the author must address before it passes |
| `rejected` | Fundamental flaw requiring rework or stopping |

## Example Usage

**Scenario 1: Broken hyperlink**
The article cites a paper with a URL that returns 404.
🔴 MUST fix the link or find an alternative source.

**Scenario 2: Padding in the opening**
The article starts with "In today's fast-paced world of technology..." before reaching the point.
🟡 SHOULD rewrite the opening to lead with the core insight.

**Scenario 3: Em-dash usage**
Three sentences use em-dash constructions where commas would work.
🟢 MAY replace em-dashes with commas or parentheses.

## Next Step

Once all 🔴 MUST findings are resolved, the article is ready for publication.

## Useful Commands Reference

No CLI commands required. This skill operates on article content provided in context.
