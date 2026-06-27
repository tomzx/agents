---
issue: "#5"
title: "Accuracy Pass on Daily Summaries"
status: draft
---

# Existing Solutions: Accuracy Pass on Daily Summaries

## Overview

Searched the internal codebase, open-source libraries, standards, and reference material for solutions that support reviewing markdown summaries for accuracy, flagging inaccuracies, storing corrections as deltas, and propagating corrections downstream. No off-the-shelf solution fits the full requirement set. The recommended direction is a hybrid: build a new skill using `deepdiff` for structured delta computation, `diff-match-patch` for text-level correction application, and `agent-audit-trail` for append-only correction logging, while borrowing Wikipedia's immutable revision model and RAID's propagation pattern for downstream correction propagation.

## Search Scope

| Source | Searched | Notes |
|---|---|---|
| Internal codebase | Yes | skills/end-day-summary, skills/end-day, skills/end-of-day-review, skills/update-pr-description, scripts/ directory, all SDLC skills. Found existing write-once pattern with no correction mechanism, but identified update-pr-description as a close precedent for minimal-edit principle. |
| Open-source | Yes | Searched PyPI and GitHub for diff/patch libraries, markdown review tools, fact-checking pipelines, delta/audit trail libraries, prose linters. |
| Commercial / SaaS | Yes | Searched for SaaS document review/correction platforms. None are compatible with the skills framework or local markdown file format. |
| Standards / protocols | Yes | RFC 6902 (JSON Patch), RFC 3284 (VCDiff), Unix diff/patch format. |
| Reference material | Yes | Searched for HITL review patterns, Wikipedia edit architecture, correction propagation papers, markdown review workflow patterns. |

## Candidate Solutions

| Solution | Type | License | Maturity | Covers | Gaps |
|---|---|---|---|---|---|
| `deepdiff` | Library | BSD-like | Mature (2500+ stars, 70M+ monthly PyPI) | FR-02, FR-03, FR-04, FR-07 | FR-01, FR-05, FR-06, FR-08, FR-09, FR-10, NFR-03, NFR-04 |
| `diff-match-patch` | Library | Apache-2.0 | Mature (Google, powers Google Docs) | FR-03, FR-04 | FR-01, FR-02, FR-05, FR-06, FR-07, FR-08, FR-09, FR-10 |
| `jsonpatch` (RFC 6902) | Library/Standard | BSD-3-Clause | Mature (494 stars, maintained) | FR-02, FR-03, FR-04, FR-07 | FR-01, FR-05, FR-06, FR-08, FR-09, FR-10 |
| `agent-audit-trail` | Library | Not specified | Active (new, 2026) | FR-07, NFR-02, NFR-05 | FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-08, FR-09, FR-10 |
| `redline` | Tool | Not specified | Active (new, Apr 2026) | FR-01, FR-02, FR-03, FR-08 | FR-04, FR-05, FR-06, FR-07, FR-09, FR-10, NFR-04 |
| `md-redline` | Tool | Not specified | Active (new, Mar 2026) | FR-01, FR-02, FR-03 | FR-04, FR-05, FR-06, FR-07, FR-08, FR-09, FR-10, NFR-04 |
| `mdprobe` | Tool | Not specified | Active (new, 2026) | FR-01, FR-02, FR-03, FR-06 (drift detection) | FR-04, FR-05, FR-07, FR-08, FR-09, FR-10, NFR-04 |
| LOKI (OpenFactVerification) | Library | MIT | Active (medium stars) | FR-10 | FR-01 through FR-09, NFR-01 through NFR-05 |
| FactEval | Library | Not specified | Active (new) | FR-10 | FR-01 through FR-09, NFR-01 through NFR-05 |
| `eventsourcing` | Library | BSD-3-Clause | Mature (high stars, v9.5.4) | FR-07, NFR-02 | FR-01 through FR-06, FR-08, FR-09, FR-10 |
| `kang` (bitemporal) | Library | Not specified | Active (new, 2026) | FR-07, FR-09, NFR-02 | FR-01 through FR-06, FR-08, FR-10 |
| `git-chronicle` | Tool | Not specified | Active (new, Feb 2026) | FR-04, FR-07, NFR-02 | FR-01, FR-02, FR-03, FR-05, FR-06, FR-08, FR-09, FR-10 |
| `update-pr-description` (internal) | Internal skill | MIT (repo) | Mature (in production) | FR-04 (minimal-edit principle) | FR-01, FR-02, FR-03, FR-05, FR-06, FR-07, FR-08, FR-09, FR-10 |
| Vale | Tool | MIT | Mature (4500+ stars, active) | FR-10 | FR-01 through FR-09, NFR-01 through NFR-05 |
| Wikipedia revision model | Pattern | N/A (pattern) | N/A | FR-04, FR-07, NFR-02 | All others (pattern only) |
| RAID (Reflective Edit Propagation) | Paper/research | N/A | Research (arXiv 2606.05023) | FR-09 | All others (pattern only) |

## Evaluation

### deepdiff

- **Strengths:** Mature, well-maintained library for computing and applying granular diffs on Python objects. `DeepDiff` and `Delta` classes directly support the FR-07 delta storage pattern. 70M+ monthly PyPI downloads. Handles nested structures, which maps to markdown sections. Can serialize deltas to JSON for storage.
- **Weaknesses:** Operates on structured Python objects, not raw markdown text directly. Would need an intermediate representation layer to parse summary sections before diffing. No built-in support for the review workflow itself.
- **Integration effort:** Low. Single dependency (`pip install deepdiff`). The `Delta` class provides apply/unapply out of the box.
- **Cost:** Free (open source).
- **Risks:** Low. BSD-style license, very active maintenance, no security concerns. Version range safety: semver discipline, major versions rare.

### diff-match-patch

- **Strengths:** Character/word-level diff with best-effort patch application (`patch_apply` with fuzzy matching). Powers Google Docs diffing. Available in multiple languages including Python. The fuzzy match capability is critical for FR-09 (propagating corrections to downstream files where exact text may differ slightly).
- **Weaknesses:** Provides text-level operations only. No structured understanding of markdown sections or summary metadata. No built-in audit trail or session management.
- **Integration effort:** Low. Single source file per language, no dependencies. Well-documented API.
- **Cost:** Free (open source, Apache-2.0).
- **Risks:** Low. Google-backed, very stable (little churn). The algorithm has been production-proven for decades.

### jsonpatch (RFC 6902)

- **Strengths:** Standardized format for describing JSON modifications as an ordered array of operations. Widely adopted, multiple implementations. If summaries are represented as structured JSON (with `op`, `path`, `value`), every correction maps to a standardized patch operation.
- **Weaknesses:** Works on flat/dotted paths in JSON, not on arbitrary text. Would require parsing markdown into a JSON tree representation first. Does not support fuzzy matching.
- **Integration effort:** Low for structured data, high if parsing markdown to JSON first.
- **Cost:** Free (BSD-3-Clause).
- **Risks:** Low. Standard is stable (RFC 6902, 2013). The `copy` and `move` operations are relevant for reorganizing summary sections.

### agent-audit-trail

- **Strengths:** Nearly exact match for FR-07 audit trail requirement. Zero-dependency, stdlib-only Python implementation. Append-only NDJSON with SHA-256 hash chaining for tamper detection. Gate references linking corrections to human approval. Domain partitioning separates correction namespaces.
- **Weaknesses:** Append-only log only — no diff computation, no review workflow, no correction application. Would need to be paired with deepdiff or diff-match-patch for the actual correction mechanism.
- **Integration effort:** Low. Single file, no dependencies, Python stdlib only.
- **Cost:** Free.
- **Risks:** Low, but project is new and unproven at scale. The hash chaining adds useful tamper evidence but is not strictly required for NFR-02.

### redline

- **Strengths:** Built specifically for human-in-the-loop AI document review. Inline comments on markdown. Sidecar JSON state. Accept/reject edits. Agent handoff skill bundled. Closest fit for FR-01, FR-02, FR-03 user experience.
- **Weaknesses:** External tool, not embeddable as a skill step. Requires its own setup and workflow. Does not match the skills framework conventions (SKILL.md + shell commands). Sidecar state diverges from the existing flat-file archive pattern.
- **Integration effort:** High. Would require wrapping as a skill step, managing sidecar state separately, and mapping its output to the delta storage format.
- **Cost:** Free.
- **Risks:** New project (April 2026), low adoption. Lock-in risk: the sidecar format and workflow are specific to redline. If it goes unmaintained, migration effort is high.

### LOKI (OpenFactVerification)

- **Strengths:** Full fact-checking pipeline: claim decomposition, check-worthiness, evidence retrieval, verification. Human-in-the-loop at each step. Directly maps to FR-10 (flag potential inaccuracies during generation).
- **Weaknesses:** Complex pipeline with external LLM dependencies. Overkill for a manual review pass. Does not address storage, review UX, or propagation. Requires running LLM calls inline during summary generation, which violates NFR-04 (no changes to existing skills).
- **Integration effort:** High. Would need to run LLM-based claim extraction against summary text, store per-claim verdicts, and integrate into the generation pipeline.
- **Cost:** Free (MIT). Ongoing LLM API costs for fact-checking.
- **Risks:** Dependency on external LLM APIs. Pipeline complexity increases maintenance burden. The automated approach may have false positive/negative rates that degrade trust.

### Vale

- **Strengths:** Fast, markup-aware prose linter. YAML-based custom rules. Zero-dependencies Go binary. Best-in-class for mechanical quality checks (style, spelling, word choice).
- **Weaknesses:** Cannot detect factual inaccuracies (only language quality). No correction workflow, no delta storage, no propagation.
- **Integration effort:** Medium. Would need custom rule configuration and integration into the generation pipeline.
- **Cost:** Free (MIT).
- **Risks:** Low. Mature, active, stable. Good fit as a complementary tool for FR-10 mechanical checks, but does not address factual accuracy.

### Wikipedia Revision Model (pattern)

- **Strengths:** Proven at global scale. Immutable revision chain where every edit creates a new revision. Corrections are never in-place edits but additions to the history. Diff computed on demand between any two revisions.
- **Weaknesses:** Pattern only, not a library. Would need to be implemented within the existing flat-file structure. Revision chain model adds complexity (versioned filenames, or a database).
- **Integration effort:** N/A (pattern).
- **Cost:** Free.
- **Risks:** N/A.

### RAID (Reflective Edit Propagation)

- **Strengths:** Directly addresses FR-09 (correction propagation). Reflect-and-propagate method infers correction intent and propagates through structural/semantic connections. Uses chain-of-tools planning for multi-step propagation.
- **Weaknesses:** Research prototype only (arXiv 2606.05023). Not a production-ready tool. Would need to be adapted to the specific summary document graph.
- **Integration effort:** N/A (research paper).
- **Cost:** Free.
- **Risks:** Research-stage. The pattern of "infer intent, then find all affected instances and apply" is valuable as a design principle even if the implementation is custom.

## Recommendation

**Direction:** Hybrid (Build core skill, adopt libraries for delta computation and audit trail)

Build a new accuracy-pass skill that:
1. Uses **deepdiff** for computing structured deltas between original and corrected summary sections, serialized as JSON delta files (FR-02, FR-03, FR-07).
2. Uses **diff-match-patch** for text-level correction application, especially the fuzzy-match patch_apply method for propagating corrections to downstream documents where exact text alignment may have drifted (FR-04, FR-09).
3. Follows the **agent-audit-trail** pattern (append-only NDJSON with hash chaining) for the correction audit trail, but implemented as a flat JSON-delta file alongside each summary rather than as a centralized log.
4. Employs the **Wikipedia immutable revision pattern** where each correction creates a new revision file, and the delta file records what changed between revisions.
5. Applies the **RAID reflect-and-propagate** pattern for FR-09: when a correction is made, scan downstream weekly/monthly files for matching text using diff-match-patch's fuzzy match, and apply corrections where confidence exceeds a threshold, queueing ambiguous cases for human review.

The core review workflow (FR-01, FR-05, FR-06, FR-08) and interruptible session management (NFR-03) must be built from scratch as a skill, since no existing tool matches the skills framework conventions (SKILL.md + shell commands + flat-file output).

Fact-checking libraries like LOKI and FactEval are deferred to FR-10 (May priority) and would be evaluated separately when that requirement is addressed.

## Sources of Information

- **Wikipedia Help:Diff / Help:Page History**: Immutable revision chain pattern. Never mutate, always append new revision. Diff computed on demand.
- **RAID (arXiv 2606.05023)**: Reflect-and-propagate pattern for correction propagation with structural/semantic connection inference.
- **update-pr-description (internal skill)**: Minimal-edit principle for correcting existing artifacts. Bias toward keeping correct text, only modify what is inaccurate.
- **google/diff-match-patch**: Fuzzy match patch_apply for best-effort correction application when exact text alignment is not available.
- **Roboflow HITL blog**: Confidence-based routing. High confidence -> auto-propagate. Medium -> suggest. Low -> human review.
- **Databricks HITL blog**: Human-on-the-loop pattern. Every approved/rejected correction is a labeled data point.
- **Wikipedia Edit Check**: Check-while-editing pattern for FR-10 (flag inaccuracies during generation).
- **githuman (mcollina)**: Review checkpoint before persisting changes. Applicable to review-before-finalize pattern.
- **agent-audit-trail**: Append-only SHA-256 hashed NDJSON for tamper-evident correction log.
- **collect_individual_threads.py --incremental**: Internal precedent for cache-merge pattern. Corrections could merge with original file the same way Slack threads merge with cached JSONL.

## Open Questions

1. Should the accuracy pass operate on individual daily files or offer a bulk-review mode across a date range? (Carried from requirements open question #1)
2. Should corrections be recorded inline (editing the original file) or as separate correction deltas (keeping an audit trail)? (Carried from requirements open question #2)
3. How are corrections propagated into downstream review files that already consumed the inaccurate data? (Carried from requirements open question #3)
4. What is the preferred granularity for corrections: line-level (difflib unified diff) or word/character-level (diff-match-patch)? The former is simpler, the latter more precise but harder to review.
5. Should the correction delta format be a custom JSON structure (section + original + corrected) or follow RFC 6902 (JSON Patch operations)? The RFC 6902 approach offers standardization but requires parsing markdown into a JSON tree.
