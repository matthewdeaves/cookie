# Code Quality Gates

These limits are **IMMUTABLE**. When exceeded, REFACTOR — never raise limits in linter configs.

## Limits

| Metric | Limit | Applies To |
|--------|-------|------------|
| Max function length | 100 lines (prefer 50) | All code |
| Max cyclomatic complexity | 15 | All code |
| Max file size | 500 lines | All code |

## When Limits Are Exceeded

- Extract helper functions
- Split into multiple smaller functions
- Move related logic to separate modules
- Apply Single Responsibility Principle

**Never**: raise thresholds in `eslint.config.js` or ruff config, add `# noqa` or `// eslint-disable` comments, rename a large file instead of splitting it.

## Checking Locally

```bash
# Python complexity
docker compose exec web radon cc apps/ -a -nb
docker compose exec web ruff check apps/

# Frontend
docker compose exec frontend npm run lint
```

## CI Enforcement

CI blocks PRs exceeding these limits via Ruff (backend) and ESLint (frontend).
