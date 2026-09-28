---
title: "<Feature Name>"
status: draft
session_link: "<filled by skill>"
---

# Refactorings: <Feature Name>

## Summary

<One paragraph: what was restructured, how many seams and abstractions were introduced, and the net effect on the diff.>

## Refactorings Applied

| # | Location | Technique | Seam or abstraction | Justification | Tests |
|---|----------|-----------|---------------------|---------------|-------|
| 1 | `<file:line>` | `<technique>` | `<what was introduced>` | `<why this is the smallest change that satisfies a justification>` | `<test(s) pinning the behavior>` |

## Deliberately Not Refactored

<Items considered and left alone, each with its reason: speculative use, single occurrence, no test seam needed, out of scope. This section is what keeps the change from bloating.>

## Verification

- Behavior preservation: <tests run before and after>
- Command: `<command>`
- Result: <pass or fail>
