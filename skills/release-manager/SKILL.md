---
name: release-manager
description: Prepare and execute a release: version bump, changelog, artifact tagging, and rollout runbook.
argument-hint: "<version>"
---

# Release Manager

Prepares a validated build for release: bumps the version, generates a changelog, tags the artifact, and produces a deployment runbook for staged rollout.

## Prerequisites

- Validated build confirmed by the Validator
- Task list for this release (resolved issues or merged PRs)
- `git` and (if applicable) `gh` CLI available
- Version scheme: semantic versioning (MAJOR.MINOR.PATCH)

## Steps

1. Determine the version bump:
   - PATCH: bug fixes only
   - MINOR: new backward-compatible features
   - MAJOR: breaking changes
2. Update the version in the project's version file (e.g., `pyproject.toml`, `package.json`, `VERSION`).
3. Generate the changelog entry from merged PRs or resolved issues since the last release.
4. Commit the version bump and changelog update.
5. Tag the commit: `git tag -a v$1 -m "Release v$1"`.
6. Produce the deployment runbook.

## Changelog Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Description of new features.

### Changed
- Description of changes to existing behavior.

### Fixed
- Description of bug fixes.

### Breaking Changes
- Description of backward-incompatible changes (MAJOR bump only).
```

## Deployment Runbook Format

```markdown
## Release v<version> Runbook

### Pre-Deployment Checklist
- [ ] Validation report: VALIDATED
- [ ] All blocking issues resolved
- [ ] Rollback plan confirmed

### Deployment Steps
1. Step one (with exact command)
2. Step two
...

### Rollback Plan
Steps to revert to the previous version if the deployment fails.

### Post-Deployment Checks
- [ ] Smoke test: <specific action to verify>
- [ ] Monitor error rate for 15 minutes
- [ ] Confirm no alerts firing
```

## Example Usage

**Scenario 1: Patch release**
Two bug fixes merged since v1.2.0. Bump to v1.2.1, add Fixed entries to CHANGELOG, tag, produce runbook.

**Scenario 2: Minor release**
Export feature added. Bump to v1.3.0, add Added entry, tag, note no breaking changes.

## Useful Commands Reference

| Command | Description |
|---|---|
| `git tag -a vX.Y.Z -m "Release vX.Y.Z"` | Create annotated release tag |
| `git push origin vX.Y.Z` | Push tag to remote |
| `gh release create vX.Y.Z --notes "..."` | Create GitHub release |
