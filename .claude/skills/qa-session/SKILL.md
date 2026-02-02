---
name: qa-session
description: Run manual QA checklist for Cookie features
user_invocable: true
---

# QA Session Skill

Interactive QA checklist for testing Cookie features, especially legacy frontend on old iPads.

## Usage

```
/qa-session [feature-name]
```

Examples:
- `/qa-session` - Full QA checklist
- `/qa-session legacy` - Legacy frontend only
- `/qa-session ai` - AI features only
- `/qa-session search` - Search functionality

## What This Skill Does

1. Presents an interactive checklist based on the feature area
2. Guides you through manual testing steps
3. Helps you verify functionality on both modern and legacy frontends
4. Provides specific test cases for iOS 9 iPad compatibility

## Feature Areas

- **legacy** - Legacy frontend (iOS 9 iPad testing)
- **modern** - Modern React frontend
- **search** - Recipe search and scraping
- **ai** - AI features (10 total)
- **playmode** - Cooking mode with timers
- **collections** - User collections and favorites
- **full** - Complete end-to-end test

## Legacy Frontend Testing

For iPad testing, this skill provides:
- Pre-deployment checklist
- iOS 9 compatibility verification
- Common issues to watch for
- Cache clearing instructions
- Console debugging steps

## Output

The skill generates:
- Numbered checklist items
- Expected behavior for each test
- How to verify success
- What to look for if it fails
- Browser/device specific notes
