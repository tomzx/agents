# Per-repository instructions

This directory holds AGENTS.md overrides that apply to a single GitHub repository without committing anything inside that repository.

## Layout

Instructions are keyed by `{owner}/{repository}` as derived from a repository's GitHub remote:

```
repositories/
  {owner}/
    {repository}/
      AGENTS.md
```

The base AGENTS.md instructs the agent to look here before working in a repository, read `repositories/{owner}/{repository}/AGENTS.md` if it exists, and apply it alongside the base instructions.

## Resolution

The agent resolves this directory by following the real path of the loaded AGENTS.md and using its sibling `repositories/` directory (a sibling of `skills/`). `{owner}/{repository}` is derived from the current repository's `origin` remote URL.

## Forks

A fork usually wants the same instructions as its upstream. Symlink the fork's entry to the upstream entry so both resolve to the same file:

```bash
mkdir -p repositories/your-fork-owner
ln -s ../../upstream-owner/repository repositories/your-fork-owner/repository
```

The symlink target is relative so the whole tree stays portable across machines and clones.

## Tracking

Per-repository files are gitignored by default (see the root `.gitignore`), because they are local and may be private. To version-control a specific file anyway, force-add it:

```bash
git add -f repositories/owner/repository/AGENTS.md
```
