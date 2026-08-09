# Infrastructure

<!--
This file captures the project's technology stack, development tooling, CI/CD pipelines,
environments, and deployment procedures. It gives implementation, testing, and deployment
skills the commands and configuration they need without grepping the codebase each time.
Update this file when tooling, environments, or deployment procedures change.
-->

## Technology Stack

| Component | Technology | Version |
|---|---|---|
| Language | <e.g., Python, TypeScript, Go> | <version> |
| Runtime | <e.g., Node.js, CPython, JVM> | <version> |
| Framework | <e.g., FastAPI, Next.js, Gin> | <version> |
| Database | <e.g., PostgreSQL, SQLite, MongoDB> | <version> |

## Development Tooling

| Tool | Purpose | Command |
|---|---|---|
| <e.g., uv> | Package management | `uv add <package>` |
| <e.g., ruff> | Linting and formatting | `uv run ruff check .` / `uv run ruff format .` |
| <e.g., mypy> | Type checking | `uv run mypy src/` |
| <e.g., pytest> | Testing | `uv run pytest` |
| <e.g., esbuild> | Build | `npm run build` |

## Environments

| Environment | Branch | Purpose | URL |
|---|---|---|---|
| <e.g., production> | <e.g., main> | <Live user-facing environment> | <https://...> |
| <e.g., staging> | <e.g., staging> | <Pre-release testing> | <https://...> |
| <e.g., preview> | <e.g., deploy/preview> | <Ephemeral PR previews> | <varies> |

## CI/CD Pipelines

| Workflow | Trigger | What it runs |
|---|---|---|
| <e.g., ci.yml> | <push, PR> | <lint, typecheck, test, build> |
| <e.g., deploy.yml> | <push to main> | <build, deploy to production> |

## Deployment

<Deployment procedure: what command or workflow triggers a deployment, what parameters it accepts, and whether manual approval is required.>

### Rollback

<Rollback procedure: how to revert a deployment, including the command or workflow, and any caveats.>

## Health Checks

| Endpoint | Expected response | Checked by |
|---|---|---|
| <e.g., /health> | <200 OK, JSON body> | <load balancer, k8s probe> |
| <e.g., /ready> | <200 OK when ready> | <k8s readiness probe> |

## Smoke Tests

<Location and command to run the smoke test suite, and what it covers.>

## Hosting

<Hosting platform, region(s), scaling strategy, and any relevant infrastructure-as-code location.>

## Secrets Management

<Where secrets are stored and how they are accessed at runtime.>
