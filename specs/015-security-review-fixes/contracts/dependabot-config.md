# Contract — `.github/dependabot.yml`

## File location

`/home/matt/cookie/.github/dependabot.yml` (new; replaces any existing skeleton if present).

## Full contents (normative)

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Australia/Sydney"
    open-pull-requests-limit: 5
    assignees: ["matthewdeaves"]
    labels: ["dependencies", "python"]
    commit-message:
      prefix: "deps(python):"
    groups:
      python:
        patterns: ["*"]
        update-types: ["minor", "patch"]

  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Australia/Sydney"
    open-pull-requests-limit: 5
    assignees: ["matthewdeaves"]
    labels: ["dependencies", "javascript"]
    commit-message:
      prefix: "deps(npm):"
    groups:
      types:
        patterns: ["@types/*"]
      npm:
        patterns: ["*"]
        exclude-patterns: ["@types/*"]
        update-types: ["minor", "patch"]

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Australia/Sydney"
    open-pull-requests-limit: 3
    assignees: ["matthewdeaves"]
    labels: ["dependencies", "docker"]
    commit-message:
      prefix: "deps(docker):"

  - package-ecosystem: "docker-compose"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Australia/Sydney"
    open-pull-requests-limit: 3
    assignees: ["matthewdeaves"]
    labels: ["dependencies", "docker"]
    commit-message:
      prefix: "deps(docker):"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Australia/Sydney"
    open-pull-requests-limit: 3
    assignees: ["matthewdeaves"]
    labels: ["dependencies", "github-actions"]
    commit-message:
      prefix: "ci:"
```

## Behavioral guarantees

1. **Weekly cadence**: all five ecosystems run every Monday at 09:00 Sydney time.
2. **Grouped routine updates**: one PR per ecosystem per week for minor+patch; majors are ungrouped and get their own PR each.
3. **Security updates**: Dependabot creates a separate PR for each security advisory regardless of grouping. This is the default — no config needed.
4. **Auto-assignment**: every PR is assigned to `matthewdeaves`.
5. **Consistent labels**: every PR carries `dependencies` plus an ecosystem label.
6. **Commit-message prefixes**: stable across PRs, greppable in history.
7. **Base-image digest pins**: the `docker` ecosystem updates `FROM image:tag@sha256:...` references in both Dockerfiles automatically — no extra config.
8. **PR cap**: 5 for pip/npm, 3 for docker/actions. Stalls creating new PRs past the cap, surfacing backlog rather than hiding it.

## Tests / validation

- Manual: paste the file into GitHub's Dependabot config validator (Repo → Settings → Dependabot → Dependabot rules) and confirm green.
- CI: add a step in the lint/validation workflow that runs `gh api repos/:owner/:repo/dependabot/alerts` (optional, not required for the spec).
- Lifecycle: after merge, watch for the first Monday's PR batch. If nothing lands within 8 days, manually trigger the check via the GitHub UI.

## Footguns avoided

- `groups` ordering: `@types/*` listed before `*` in the npm block so it matches first.
- No daily schedule — weekly is the consensus best practice.
- `docker` and `docker-compose` are listed separately (they are distinct ecosystems as of Feb 2025 GA) so both Dockerfiles and compose files are covered.
- Security PRs are not configured — they run automatically and bypass groups.
- Every block has `assignees` so PRs don't rot unassigned.
