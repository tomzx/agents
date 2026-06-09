---
name: divio-documentation
description: "Write or review documentation following the Divio/Diataxis system, which defines four types: tutorials, how-to guides, reference, and explanation. This is the comprehensive reference skill; create-documentation delegates to this for detailed guidance."
---

# Write Divio Documentation

Writes or reviews documentation following the Divio/Diátaxis four-type system, ensuring each document serves its intended audience and purpose without mixing concerns.

## Prerequisites

- The subject to document or the document to review provided in context
- Clarity on which documentation type is needed (or ask to determine it)
- Target audience's knowledge level

## Decision Framework

Identify the type before writing:

```
Is the user studying or working?
        /              \
   Studying           Working
      |                   |
      v                   v
Is it practical    Is it practical
or theoretical?    or theoretical?
  /      \           /      \
Pract.  Theor.    Pract.  Theor.
  |       |         |       |
  v       v         v       v
Tutorial Expl.  How-to   Ref.
```

**Quick identification:**
- "I want to learn X" -> **Tutorial**
- "I want to accomplish Y" -> **How-to**
- "What are the parameters of Z?" -> **Reference**
- "Why does X work this way?" -> **Explanation**

## The Four Documentation Types

### 1. TUTORIALS (Learning-Oriented)

**Purpose**: Take a complete beginner through steps to complete a meaningful project and gain confidence.

**Audience**: Absolute beginners with minimal prior knowledge.

**DO:**
- Start from zero, make no assumptions about prior knowledge
- Provide concrete, specific steps that are reliably repeatable
- Make every step produce a visible, comprehensible result
- Keep the learner moving forward at all times
- End each section with a meaningful accomplishment

**DON'T:**
- Explain concepts or theory in depth (link to Explanation instead)
- Provide options or alternatives (one clear path only)
- Allow the learner to encounter errors or confusion
- Discuss edge cases or advanced features

**Structure:**
```markdown
# Tutorial: [Specific Achievement]

## What You'll Build
## Prerequisites
## Step 1: [Action Verb + Specific Task]
## Step 2: [Next Action]
## What You've Learned
## Next Steps
```

### 2. HOW-TO GUIDES (Problem-Oriented)

**Purpose**: Guide users with some experience through solving a specific practical problem.

**Audience**: Users who know what they want to achieve.

**DO:**
- Start with a clear, descriptive title: "How to [specific task]"
- Focus on achieving one specific goal
- Assume the reader has basic knowledge of the system
- Be concise and action-oriented

**DON'T:**
- Try to teach concepts (link to Explanation)
- Provide exhaustive coverage of all options
- Make it tutorial-like with excessive hand-holding

**Structure:**
```markdown
# How to [Specific Task]

## Problem
## Prerequisites
## Steps
## Verification
## Related
```

### 3. REFERENCE (Information-Oriented)

**Purpose**: Provide accurate, complete technical descriptions of the system's machinery.

**Audience**: Users actively working with the code who need to look up specifics.

**DO:**
- Structure to mirror the codebase organization
- Maintain absolute consistency in tone, format, and structure
- Include all parameters, return values, exceptions
- Keep descriptions up-to-date with code changes

**DON'T:**
- Include instructions on how to achieve tasks (link to How-to)
- Explain concepts or design decisions (link to Explanation)
- Use conversational or variable tone

**Structure:**
```markdown
# [Class/Function/Module Name]

## Description
## Syntax
## Parameters
## Returns
## Exceptions
## Example
## See Also
```

### 4. EXPLANATION (Understanding-Oriented)

**Purpose**: Clarify, illuminate, and provide context about a topic to deepen understanding.

**Audience**: Users seeking deeper understanding of concepts, context, or design decisions.

**DO:**
- Take a broader, higher-level view
- Discuss background, context, and design decisions
- Explore connections between concepts
- Write in a discursive, readable style

**DON'T:**
- Give step-by-step instructions (link to Tutorial or How-to)
- Provide technical specifications (link to Reference)

**Structure:**
```markdown
# Understanding [Concept/Topic]

## Overview
## Background
## How It Works
## Why This Approach
## Alternatives
## Common Misconceptions
## Further Reading
```

## The Four Quadrants

```
              PRACTICAL
                 |
    TUTORIALS    |    HOW-TO GUIDES
   (learning)    |    (problem-solving)
                 |
STUDYING --------+-------- WORKING
                 |
   EXPLANATION   |    REFERENCE
  (understanding)|   (information)
                 |
             THEORETICAL
```

## Key Principles

1. **Keep them separate**: Each type has different demands. Don't mix them.
2. **All four are needed**: A complete documentation system includes all types.
3. **Cross-link appropriately**: Link between types but maintain boundaries.
4. **Structure explicitly**: Make it obvious which type each document is.
5. **Resist gravitational pull**: Types naturally want to blend - resist this.

## Example Usage

**Scenario 1: New library - "how do I get started?"**
User wants to learn the library from scratch. Write a **Tutorial** that walks through building a small working example, ending with a visible result.

**Scenario 2: Specific task - "how do I switch databases?"**
User knows the system and wants to accomplish a specific goal. Write a **How-to Guide**: "How to Switch from SQLite to PostgreSQL" with numbered steps and a verification step.

**Scenario 3: API documentation**
User is actively writing code and needs parameter details. Write **Reference** documentation mirroring the code structure, covering all parameters, return types, and exceptions.

**Scenario 4: Design question - "why does this use event sourcing?"**
User wants to understand architectural decisions. Write an **Explanation** covering background, trade-offs, and alternatives considered.

**Scenario 5: Reviewing existing docs**
User provides a document to review. Identify which type it is, then flag violations (e.g., a how-to that explains too much theory, or a tutorial that offers choices).

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
