# Cookie - Claude Code Configuration

This directory contains Cookie's Claude Code customization: rules, hooks, and skills.

## Directory Structure

```
.claude/
├── rules/                    # Domain-specific knowledge (read by Claude)
│   ├── es5-compliance.md    # ES5 JavaScript for iOS 9 Safari
│   ├── docker-environment.md # Docker-only command patterns
│   ├── code-quality.md      # Immutable quality gates (100 lines, complexity 15)
│   ├── ai-features.md       # 10 AI features + fallback behavior
│   ├── django-security.md   # SQL injection, XSS, CSRF prevention
│   └── react-security.md    # React XSS, safe rendering patterns
├── hooks/                    # Pre-execution validation (auto-runs)
│   ├── es5-syntax-check.sh  # BLOCKS ES6+ in apps/legacy/
│   ├── complexity-check.sh  # BLOCKS functions >100 lines
│   └── docker-command-check.sh # WARNS about host commands
├── skills/                   # User-invocable workflows
│   └── qa-session/          # Manual testing checklist (/qa-session)
├── logs/                     # Hook execution logs
│   └── hooks.log            # Timestamped hook results
└── settings.local.json       # Hooks config + permissions

## How It Works

### Rules (Domain Knowledge)

Rules are markdown files that document project-specific patterns and constraints. Claude reads these automatically when:
- Reviewing PRs (via GitHub Actions)
- Working in local sessions (references them from claude.md)
- Running skills that need domain context

**Example:** `.claude/rules/es5-compliance.md` documents iOS 9 Safari requirements (no const/let, arrow functions, etc.)

### Hooks (Quality Gates)

Hooks are shell scripts that run **automatically** before tool operations:

| Hook | Triggers | Purpose |
|------|----------|---------|
| `es5-syntax-check.sh` | Before Edit/Write | Blocks ES6+ syntax in `apps/legacy/` |
| `complexity-check.sh` | Before Edit/Write | Blocks functions >100 lines or complexity >15 |
| `docker-command-check.sh` | Before Bash | Warns if Python/Django run on host |

**Configuration:** `settings.local.json` registers hooks for each tool (Edit, Write, Bash)

**Logs:** All hook executions logged to `.claude/logs/hooks.log`

**Exit codes:**
- `0` = Allow operation
- `1` = Block operation (show error message)

### Skills (User Workflows)

Skills are invoked by typing `/skill-name` in Claude Code:

```bash
/qa-session           # Full QA checklist
/qa-session legacy    # iOS 9 iPad testing
/qa-session ai        # AI features testing
```

Each skill has:
- `SKILL.md` - Metadata (name, description, user_invocable)
- `prompt.md` - Instructions for Claude when skill runs

## Examples

### Hook Blocking ES6+ Syntax

```javascript
// ❌ This would be BLOCKED in apps/legacy/static/legacy/js/
const myVar = 'value';

// Error: ES6+ Syntax Detected in Legacy Frontend
// - Found 'const' declaration (use 'var' for ES5)
```

### Docker Command Warning

```bash
# ❌ This would show a WARNING
pytest

# ⚠️  WARNING: Docker Environment Check
# This command may run on host instead of in Docker
# Use: docker compose exec web python -m pytest
```

### QA Session Skill

```bash
/qa-session legacy

# Generates interactive checklist:
# - Pre-requisites (cache cleared, containers restarted)
# - Test cases (profile selection, search, detail page)
# - Common issues (ES5 errors, image caching)
# - Post-testing cleanup
```

## Adding New Rules

1. Create `.claude/rules/your-rule.md`
2. Use YAML frontmatter:
   ```yaml
   ---
   description: Brief description of what this rule covers
   ---
   ```
3. Reference from `claude.md` or PR review prompt

## Adding New Hooks

1. Create `.claude/hooks/your-hook.sh`
2. Make executable: `chmod +x .claude/hooks/your-hook.sh`
3. Add to `settings.local.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Edit",
           "hooks": [
             {
               "type": "command",
               "command": ".claude/hooks/your-hook.sh",
               "statusMessage": "Checking..."
             }
           ]
         }
       ]
     }
   }
   ```
4. Test by attempting an Edit operation

## Adding New Skills

1. Create `.claude/skills/skill-name/SKILL.md`:
   ```yaml
   ---
   name: skill-name
   description: What the skill does
   user_invocable: true
   ---
   ```
2. Create `.claude/skills/skill-name/prompt.md` with Claude instructions
3. Invoke with `/skill-name`

## Best Practices

### Rules
- Keep rules focused (one concern per file)
- Include examples (before/after, do/don't)
- Reference authoritative sources (RFCs, docs)
- Update rules when patterns change

### Hooks
- Keep hooks fast (<1 second)
- Exit 0 (allow) or 1 (block) only
- Provide actionable error messages
- Log to `.claude/logs/hooks.log` for debugging

### Skills
- Make skills task-specific
- Include clear input/output examples
- Document required context files
- Test with different argument patterns

## Troubleshooting

### Hook not running?
- Check `settings.local.json` syntax (valid JSON)
- Verify hook is executable: `ls -l .claude/hooks/`
- Check logs: `tail -f .claude/logs/hooks.log`

### Hook blocking incorrectly?
- Test hook manually: `echo '{}' | jq '.tool_input = {file_path: "test.js", new_string: "var x = 1;"}' | .claude/hooks/es5-syntax-check.sh`
- Check logs for the specific failure
- Adjust regex patterns in hook script

### Skill not found?
- Ensure `SKILL.md` has `user_invocable: true`
- Check skill name matches directory name
- Verify `SKILL.md` and `prompt.md` both exist

## References

- Claude Code Docs: https://docs.anthropic.com/claude-code
- Hooks Guide: https://docs.anthropic.com/claude-code/hooks
- Skills Guide: https://docs.anthropic.com/claude-code/skills
- MCP Servers: https://docs.anthropic.com/claude-code/mcp

## Comparison: Cookie vs PeerTalk

| Feature | Cookie (Web App) | PeerTalk (Classic Mac SDK) |
|---------|------------------|----------------------------|
| **Rules** | ES5, Docker, Security, AI | ISR safety, MacTCP, OpenTransport |
| **Hooks** | ES5 syntax, complexity | ISR forbidden calls, userFlags |
| **Skills** | QA session | Build, deploy, hardware test |
| **MCP** | None (not needed) | Classic Mac hardware access |
| **Complexity** | Web compatibility | Interrupt-time safety |

Both use the same Claude Code extensibility features, just applied to different domains!
