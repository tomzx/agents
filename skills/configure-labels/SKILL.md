---
name: configure-labels
description: Configure the standard label set in a GitHub repository to match the SDLC labeling conventions used by triage and issue management skills.
argument-hint: "[repository]"
---

# Configure Repository Labels

Sets up the standard label taxonomy in a GitHub repository so that downstream skills (triage-issues, label-issue, prioritize-issues) can classify and manage issues consistently.
Creates missing labels, updates descriptions and colors for existing labels that do not match the convention, and removes conflicts with GitHub defaults.
Idempotent: safe to re-run on a repository that already has some or all labels configured.

## Prerequisites

- `gh` CLI authenticated with write access to the target repository
- Repository in `owner/repo` format (`$1`), or omit to use the repository in the current working directory

## Workflow

```
Determine target repository ($1 or CWD)
         |
         v
Fetch existing labels via gh label list
         |
         v
Compute desired label set (standard + project-specific)
         |
         v
For each desired label:
   Exists?
    /       \
  Yes         No
   |           |
   v           v
 Update if     Create label
 name/color/   via gh label
 desc differ
   |           |
   +-----+-----+
         |
         v
Report: created, updated, unchanged, conflicts
```

## Standard Label Taxonomy

The label set is organized into dimensional namespaces.
Every SDLC-managed repository should have labels from the dimensions that are relevant to its domain.

### Type Labels

| Name | Color | Description |
|---|---|---|
| `bug` | `d73a4a` | Something isn't working |
| `feature` | `0075ca` | New feature or request |
| `question` | `d876e3` | Further information is requested |
| `chore` | `fef2c0` | Maintenance, refactoring, or dependency updates |
| `documentation` | `0075ca` | Improvements or additions to documentation |
| `security` | `b60205` | Vulnerability or security concern |

### Area Labels

Area labels use the `area:` prefix.
Do not create the full catalog blindly.
Instead, derive the project's areas from its structure and context files (see "Area Discovery" below).

#### Area Discovery

1. **Read context files**: Check `.sdlc/context/architecture.md` and `.sdlc/context/project-overview.md` for subsystems, modules, or components explicitly named in the project's architecture.
2. **Scan directory structure**: List top-level and second-level directories to identify subsystem boundaries (e.g., `src/api/`, `src/ui/`, `extensions/`, `cmd/`, `internal/auth/`).
3. **Check existing labels**: If the repository already has `area:*` or `component:*` labels, include them in the desired set as-is (update color/description only if they differ).
4. **Map to area labels**: For each identified subsystem, create an `area:<slug>` label with a description derived from the subsystem's purpose.

Common area labels and when they apply:

| Name | Description | Create when |
|---|---|---|
| `area:core` | Core functionality and shared logic | Project has a shared/core/common module |
| `area:ui` | User interface components | Project has a frontend or UI layer |
| `area:api` | API endpoints and contracts | Project exposes or consumes APIs |
| `area:auth` | Authentication and authorization | Project has auth/login/session logic |
| `area:docs` | Documentation and examples | Project has a docs site or extensive documentation |
| `area:ci` | CI/CD pipelines and infrastructure | Project has CI workflows worth tracking separately |
| `area:testing` | Test infrastructure and fixtures | Project has test harnesses or fixture generators |

If the project's architecture does not map to any of these, do not create them.
If the project has subsystems not listed above (e.g., `area:storage`, `area:networking`, `area:billing`), create those instead.

### Platform Labels

Platform labels use the `platform:` prefix.
Only create these if the project is cross-platform.

| Name | Color | Description |
|---|---|---|
| `platform:linux` | `c5def5` | Linux-specific issues |
| `platform:macos` | `c5def5` | macOS-specific issues |
| `platform:windows` | `c5def5` | Windows-specific issues |

### Provider Labels

Provider labels use the `api:` prefix.
Only create these if the project integrates with external APIs.

| Name | Color | Description |
|---|---|---|
| `api:openai` | `fbca04` | OpenAI API integration |
| `api:anthropic` | `fbca04` | Anthropic API integration |
| `api:bedrock` | `fbca04` | AWS Bedrock integration |
| `api:vertex` | `fbca04` | Google Vertex AI integration |

### Priority Labels

| Name | Color | Description |
|---|---|---|
| `priority:high` | `e11d48` | Urgent: blocking production or multiple users |
| `priority:medium` | `fb923c` | Important: high business value or core functionality |
| `priority:low` | `a3a3a3` | Nice-to-have: low business impact |

### Triage State Labels

| Name | Color | Description |
|---|---|---|
| `needs-info` | `fef2c0` | Issue needs more information from the reporter |
| `needs-repro` | `fef2c0` | Bug report lacks reproduction steps |
| `has-repro` | `0e8a16` | Bug report includes clear reproduction steps |
| `stale` | `eeeeee` | No activity for an extended period |

### Severity Labels

| Name | Color | Description |
|---|---|---|
| `regression` | `b60205` | Functionality that used to work but broke |
| `data-loss` | `b60205` | User data is lost or corrupted |
| `duplicate` | `cfd3d7` | Duplicate of another issue |
| `invalid` | `e4e669` | Issue is not valid or not applicable |

## Project-Specific Labels

Area labels are always derived from the project's actual structure (see Area Discovery above).
If the architecture context files describe subsystems that are not covered by the common area labels, create `area:*` labels for those subsystems.

## Steps

1. Determine the target repository: use `$1` if provided, otherwise derive from the current working directory's git remote.
2. Fetch the repository's current labels:
   ```
   gh label list --repo <repo> --limit 200 --json name,color,description
   ```
3. Discover area labels using the Area Discovery process:
   a. Read `.sdlc/context/architecture.md` and `.sdlc/context/project-overview.md` for named subsystems.
   b. List top-level and second-level directories to identify module boundaries.
   c. Include any existing `area:*` or `component:*` labels already in the repo.
   d. Map findings to `area:*` labels. Only create labels that correspond to real subsystems in the project.
4. Compute the desired label set:
   - Type, priority, triage state, and severity labels are always included (standard set).
   - Area labels come from step 3.
   - Omit platform labels if the project is single-platform.
   - Omit provider labels if the project has no external API integrations.
5. For each desired label, compare against the existing label set:
   - **Missing**: create it.
     ```
     gh label create "<name>" --repo <repo> --color "<hex>" --description "<desc>"
     ```
   - **Exists with different color or description**: update it.
     ```
     gh label edit "<name>" --repo <repo> --color "<hex>" --description "<desc>"
     ```
   - **Exists and matches**: skip (unchanged).
6. Do not delete labels that are not in the desired set.
   Those may have been created manually or by other tools.
   Report them as "extra labels" in the summary.
7. Output the configuration summary.

## Output Format

```markdown
## Label Configuration Summary

### Created (N)
| Label | Color | Description |
|---|---|---|
| `area:core` | `0075ca` | Core functionality and shared logic |
| `bug` | `d73a4a` | Something isn't working |

### Updated (N)
| Label | Changes |
|---|---|
| `feature` | description: "" -> "New feature or request" |

### Unchanged (N)
`question`, `documentation`, `area:api`

### Extra labels (not in standard set)
`custom-label`, `legacy-tag`

### Recommendations
- Consider adding `area:networking` based on the networking subsystem described in architecture.md
- Remove unused `legacy-tag` if no longer needed
```

## Example Usage

**Scenario 1: New repository with no labels**
```
/configure-labels owner/myrepo
```
Creates the full standard label set. Reports all labels as created.

**Scenario 2: Existing repository with partial labels**
```
/configure-labels
```
Repository already has GitHub defaults (`bug`, `documentation`, `duplicate`, etc.) with no descriptions.
Creates missing labels (area, platform, priority, triage state) and updates existing labels with correct descriptions and colors.

**Scenario 3: Re-running after adding project context**
```
/configure-labels owner/myrepo
```
Project has added `architecture.md` describing a `storage` subsystem.
Creates the missing `area:storage` label. All other labels are unchanged.

## Useful Commands Reference

| Command | Description |
|---|---|
| `gh label list --repo <repo> --limit 200 --json name,color,description` | Fetch all existing labels |
| `gh label create "<name>" --repo <repo> --color "<hex>" --description "<desc>"` | Create a new label |
| `gh label edit "<name>" --repo <repo> --color "<hex>" --description "<desc>"` | Update an existing label's color or description |
| `gh repo view --json isPrivate --jq '.isPrivate'` | Check repository visibility |
