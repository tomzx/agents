---
name: spec-format
description: Format a specification document with one sentence per line.
---

# Format Specification

Reformats a specification document so that each sentence appears on its own line, making the document easier to diff and review sentence by sentence.

## Prerequisites

- A specification document provided in context or as a file path to read

## Steps

1. Read the specification document.
2. Split compound sentences and multi-sentence paragraphs so each sentence occupies exactly one line.
3. Preserve section headings, lists, and code blocks unchanged.
4. Return the reformatted document.

## Example Usage

**Scenario 1: Dense paragraph**
Input:
```
The API must validate all inputs. It should return 400 for invalid requests. Errors must include a message field.
```
Output:
```
The API must validate all inputs.
It should return 400 for invalid requests.
Errors must include a message field.
```

**Scenario 2: Already formatted document**
Input has one sentence per line. No changes are made; return as-is.

**Scenario 3: Mixed content**
A spec with headings, a code block, and prose paragraphs. Only the prose paragraphs are reformatted; headings and code blocks are left intact.

## Useful Commands Reference

No CLI commands required. This skill operates on document content provided in context.
