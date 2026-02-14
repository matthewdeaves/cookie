# Cookie - Claude Code Configuration

This directory contains Cookie's Claude Code customization: rules, hooks, and skills.

## Directory Structure

```
.claude/
├── rules/                         # Domain-specific knowledge
│   ├── es5-compliance.md         # ES5 syntax requirements
│   ├── ios9-safari-api.md        # JavaScript API limitations
│   ├── ios9-safari-css.md        # CSS feature limitations
│   ├── legacy-patterns.md        # Approved code patterns
│   ├── docker-environment.md     # Docker-only commands
│   ├── code-quality.md           # Function length, complexity
│   ├── ai-features.md            # 10 AI features + fallback
│   ├── django-security.md        # SQL injection, XSS, CSRF
│   └── react-security.md         # React XSS, CSP
├── hooks/                         # Pre/post execution validation
│   ├── lib/
│   │   └── common.sh             # Shared hook functions
│   ├── es5-syntax-check.sh       # BLOCKS ES6+ in legacy JS
│   ├── complexity-check.sh       # BLOCKS functions >100 lines
│   ├── security-check.sh         # BLOCKS dangerous patterns
│   ├── docker-command-check.sh   # WARNS about host commands
│   ├── post-edit-lint.sh         # Runs linter after edits
│   ├── commit-msg-check.sh       # Enforces conventional commits
│   └── pre-push-tests.sh         # Runs tests before push
├── skills/
│   └── qa-session/               # Manual QA checklist (/qa-session)
├── logs/
│   └── hooks.log                 # Hook execution logs
└── settings.local.json           # Hooks config + permissions
```

## Rules

Rules are markdown documentation that Claude reads automatically. They provide domain-specific knowledge.

| Rule | Purpose | Applies To |
|------|---------|-----------|
| `es5-compliance.md` | ES5 syntax requirements | `apps/legacy/static/legacy/js/` |
| `ios9-safari-api.md` | JS API limitations | Legacy frontend |
| `ios9-safari-css.md` | CSS limitations | Legacy frontend |
| `legacy-patterns.md` | IIFE, callbacks, namespace | Legacy frontend |
| `docker-environment.md` | Docker-only commands | All Python/Django |
| `code-quality.md` | 100 line / complexity 15 limits | All code |
| `ai-features.md` | 10 AI features, fallback behavior | AI integration |
| `django-security.md` | SQL injection, XSS, CSRF | Django backend |
| `react-security.md` | React XSS, CSP | React frontend |

## Hooks

### Claude Code Hooks (PreToolUse/PostToolUse)

| Hook | Trigger | Behavior |
|------|---------|----------|
| `es5-syntax-check.sh` | Before Edit/Write | **Blocks** ES6+ in legacy JS |
| `complexity-check.sh` | Before Edit/Write | **Blocks** functions >100 lines |
| `security-check.sh` | Before Edit/Write | **Blocks** dangerous patterns |
| `docker-command-check.sh` | Before Bash | **Warns** about host commands |
| `post-edit-lint.sh` | After Edit/Write | **Warns** with lint issues |

### Git Hooks (via pre-commit)

| Hook | Stage | Behavior |
|------|-------|----------|
| `commit-msg-check.sh` | commit-msg | **Blocks** non-conventional commits |
| `pre-push-tests.sh` | pre-push | **Blocks** push if tests fail |

### Hook Exit Codes

- `0` = Allow operation (or warning only)
- `1` = Block operation (show error)

### Hook Logging

All hooks log to `.claude/logs/hooks.log`:

```bash
tail -f .claude/logs/hooks.log
```

## Skills

Skills are user-invocable workflows. Type `/skill-name` in Claude Code.

| Skill | Command | Purpose |
|-------|---------|---------|
| qa-session | `/qa-session [area]` | Manual QA checklist |

### QA Session Usage

```bash
/qa-session           # Full checklist
/qa-session legacy    # iOS 9 iPad testing
/qa-session ai        # AI features
/qa-session search    # Search functionality
```

## Adding New Rules

1. Create `.claude/rules/your-rule.md`
2. Add YAML front matter:
   ```yaml
   ---
   description: Brief description
   paths:
     - "path/to/files/**/*"
   ---
   ```
3. Document patterns, examples, and references

## Adding New Hooks

1. Create `.claude/hooks/your-hook.sh`
2. Source common library:
   ```bash
   #!/bin/bash
   source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
   init_hook "your-hook"

   FILE_PATH=$(get_file_path)
   NEW_CONTENT=$(get_new_content)

   # Your logic here...

   log_hook "PASS: $FILE_PATH"
   exit 0
   ```
3. Make executable: `chmod +x .claude/hooks/your-hook.sh`
4. Add to `settings.local.json`

## Troubleshooting

### Hook not running?
```bash
# Check JSON syntax
cat settings.local.json | jq .

# Check executable
ls -l .claude/hooks/

# Check logs
tail .claude/logs/hooks.log
```

### Hook blocking incorrectly?
```bash
# Test manually
echo '{"tool_input":{"file_path":"test.js","new_string":"var x = 1;"}}' | \
  .claude/hooks/es5-syntax-check.sh
```

## References

- Claude Code: https://docs.anthropic.com/claude-code
- pre-commit: https://pre-commit.com/
