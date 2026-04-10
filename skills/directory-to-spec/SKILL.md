---
name: directory-to-spec
description: Create a spec directory with specification files per major feature for code in the current directory and its subdirectories.
---

# Convert Directory to Spec

Analyzes code in the current directory and generates a `spec/` directory containing one specification file per major feature, each with MUST/SHOULD/MAY requirements.

## Prerequisites

- Read access to the current directory and its subdirectories
- A codebase with identifiable features or modules

## Steps

1. Read and analyze the code in the current directory and subdirectories to identify major features.
2. Create the `spec/` directory.
3. For each major feature, create a descriptively named specification file (e.g., `authentication.md`).
4. Each file must include a `requirements` section using RFC 2119 language (`MUST`, `SHOULD`, `MAY`).

**Naming rules:**
- Use descriptive, lowercase names: `authentication.md`
- Do NOT number files: ~~`01-authentication.md`~~
- Do NOT suffix with `-spec`: ~~`authentication-spec.md`~~

## Example Usage

**Scenario 1: REST API project**
Working directory contains `auth/`, `orders/`, `payments/`. Produces:
- `spec/authentication.md`
- `spec/order-management.md`
- `spec/payment-processing.md`

**Scenario 2: Single-module library**
Working directory contains a single Python library with multiple classes. Produces one spec file per major class or responsibility area.

**Scenario 3: Frontend application**
Working directory contains React components. Produces spec files organized around user-facing features rather than individual component names.

## Useful Commands Reference

| Command | Description |
|---|---|
| `mkdir spec` | Create the spec output directory |
