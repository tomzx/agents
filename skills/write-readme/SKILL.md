---
name: write-readme
description: Generate a README.md for a project using a structured template with badges, feature lists, roadmap, and setup instructions.
argument-hint: "[project directory or repository name]"
---

# Write README

Produces a `README.md` for a project using a fixed template with centered header, badges, feature list, roadmap, and setup instructions. Derives content from the codebase, existing configuration files, and any available context.

## Prerequisites

- A project directory with source code, a license file, and a package manifest (e.g., `go.mod`, `package.json`, `Cargo.toml`, `pyproject.toml`)
- If `$1` is provided, use it as the project directory; otherwise use the current working directory

## Steps

1. Scan the project for metadata: repository name from git remote or directory name, license type, language/runtime version from the package manifest, storage or database dependencies, and platform targets.
2. Determine a one-sentence description of the project from existing docs, the package manifest description, or by reading the main entry point.
3. List features by scanning source directories, CLI commands, exported functions, and any existing documentation.
4. Identify roadmap items from open GitHub issues, TODO comments, or stated goals in docs.
5. Identify out-of-scope items by reading issue discussions, design docs, or the package manifest's stated purpose.
6. Determine install steps from the package manifest, Makefile, or build scripts.
7. Write the README following the output template exactly.
8. Write the file to `README.md` in the project root.

## Output Format

```markdown
<h1 align="center">{repository}</h1>

<p align="center">
  <strong>{one sentence description of the project}</strong>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/tomzxcode/{repository}" alt="License"></a>
  <img src="https://img.shields.io/badge/{language}-{version}%2B-{color}" alt="{Language} {version}+">
  <img src="https://img.shields.io/badge/platform-{platforms}-lightgrey" alt="Platform">
</p>

<p align="center">
  <img src="screenshot.png" alt="{repository} Demo"/>
</p>

## What

{2-4 sentences explaining what the project is and what it does.}

## Why

{2-4 sentences explaining the motivation behind the project, the problem it solves, and why it exists.}

## Included

{bullet point list of features, one per line, using - prefix}

## Roadmap

{bullet point list of planned features, one per line, using - prefix}

## Out of Scope

{bullet point list of features explicitly not planned, one per line, using - prefix}

## Requirements

{List of system requirements needed to build and run the project. Include language version, OS, and any external dependencies.}

## Install

{Step-by-step installation instructions with code blocks for commands.}

## Getting Started

{Step-by-step guide to using the project after installation. Include code examples where applicable.}

## License

The code is licensed under the [MIT license](http://choosealicense.com/licenses/mit/). See [LICENSE](LICENSE).
```

## Badge Configuration

Derive badge values from the project:

| Badge | Source |
|---|---|
| License | Read `LICENSE` file or `package.json` license field |
| Language + version | Read `go.mod`, `package.json`, `Cargo.toml`, or `pyproject.toml` |
| Storage | Scan imports/dependencies for database drivers (SQLite, PostgreSQL, etc.) |
| Platform | Infer from build targets, CI config, or source code platform checks |

Remove badges that do not apply (e.g., if no storage dependency, omit the storage badge).

## Quality Criteria

**Strong READMEs:**
- Description is specific and concrete, not generic
- Features are expressed as user-facing capabilities, not implementation details
- Install steps are copy-pasteable and tested against a clean environment
- Getting Started section gets the user to a working result in under 5 minutes
- Roadmap items are concrete and actionable
- Out of Scope items demonstrate deliberate scoping decisions

**Avoid:**
- Vague descriptions like "a tool that helps you manage things"
- Listing every internal function as a feature
- Install steps that assume prior setup not mentioned in Requirements
- Empty placeholder sections (omit Roadmap or Out of Scope if no content exists)

## Example Usage

**Scenario 1: New Go CLI tool**
Project has `go.mod`, `main.go`, and a `LICENSE`.
Scan source for CLI commands and flags to populate Included, read `go.mod` for Go version, detect SQLite dependency in imports for the storage badge.

**Scenario 2: Existing project without README**
Project has `pyproject.toml`, `src/` directory, and GitHub issues labeled "enhancement".
Derive features from the public API, pull roadmap items from open enhancement issues, read `pyproject.toml` for Python version requirement.

## Next Step

Run `/review-documentation` to audit the README for completeness, accuracy, and clarity.

## Useful Commands Reference

No CLI commands required. This skill operates on the codebase and project files.
