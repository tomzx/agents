---
name: create-documentation
description: Create documentation for a feature or component following the Divio documentation framework (tutorials, how-to guides, reference, explanation).
argument-hint: "[feature or component]"
---

# Create Documentation

Produces documentation for a feature or component organized according to the [Divio documentation framework](https://docs.divio.com/documentation-system/): tutorials, how-to guides, reference, and explanations.

## Prerequisites

- Feature or component description provided in context or as `$1`
- Access to the codebase, specification, or implementation (if available)

## Divio Documentation Structure

| Type | Answers | Oriented toward |
|---|---|---|
| Tutorial | "How do I get started?" | Learning by doing |
| How-To Guide | "How do I do X?" | Solving a specific problem |
| Reference | "What is X?" | Information lookup |
| Explanation | "Why does X work this way?" | Understanding |

Write only the sections relevant to the feature. Not every feature needs all four types.

## Steps

1. Understand the feature: what it does, who uses it, and common use cases.
2. Identify which documentation types are needed.
3. Write a tutorial if users need onboarding guidance.
4. Write how-to guides for the most common user tasks.
5. Write reference documentation for all public APIs, config options, and interfaces.
6. Write an explanation section if the design or behavior needs conceptual context.

## Output Format

```markdown
# <Feature Name>

## Overview

<One paragraph describing what the feature does and when to use it.>

---

## Tutorial: Getting Started with <Feature>

<Step-by-step guide for a first-time user achieving a minimal working result.>

---

## How-To Guides

### How to <Task 1>

<Steps to accomplish the specific task.>

### How to <Task 2>

...

---

## Reference

### Configuration

| Option | Type | Default | Description |
|---|---|---|---|

### API

#### <Method / Endpoint>

<Parameters, return values, errors.>

---

## Explanation

### <Concept or Design Decision>

<Why the feature works the way it does, trade-offs made, or the conceptual model.>
```

## Example Usage

**Scenario 1: New CLI command**
Document `create-requirements`: tutorial (run your first requirements doc), how-to (generate requirements from a GitHub issue), reference (all input formats accepted), explanation (why MoSCoW prioritization is used).

**Scenario 2: Internal library**
Document a cache abstraction: how-to guides for common cache patterns, full reference for every method, explanation of the eviction strategy chosen.

## Useful Commands Reference

No CLI commands required. This skill operates on information provided in context.
