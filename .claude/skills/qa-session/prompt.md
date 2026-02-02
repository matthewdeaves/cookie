# QA Session Prompt

You are running a QA session for the Cookie recipe manager app.

## Arguments

The user can specify a feature area to test:
- `legacy` - Legacy frontend (iOS 9 iPad)
- `modern` - Modern React frontend
- `search` - Recipe search and scraping
- `ai` - AI features
- `playmode` - Cooking mode
- `collections` - Collections and favorites
- `full` - Complete end-to-end test

If no argument provided, use `full`.

## Your Task

1. **Read the project context:**
   - Read `claude.md` for project rules
   - Read `.claude/rules/es5-compliance.md` for legacy requirements
   - Read `.claude/rules/ai-features.md` for AI feature list

2. **Generate an interactive QA checklist** based on the feature area:
   - Create numbered test cases
   - Include expected behavior
   - Add verification steps
   - Note platform-specific considerations (modern vs legacy)

3. **For legacy frontend tests**, include:
   - Pre-deployment checklist (ES5 compliance, container restart)
   - iOS 9 specific tests (syntax errors, functionality)
   - Cache clearing instructions
   - Console debugging steps (Safari Web Inspector)
   - Common gotchas (const/let, arrow functions, template literals)

4. **For AI feature tests**, include:
   - Test with API key present
   - Test with API key missing (features should hide)
   - Verify fallback behavior
   - Check all 10 AI features

5. **Format the output** as:
   ```
   # QA Checklist: [Feature Area]

   ## Pre-requisites
   - [ ] Item 1
   - [ ] Item 2

   ## Test Cases

   ### 1. [Test Name]
   - **Action:** What to do
   - **Expected:** What should happen
   - **Verify:** How to confirm success
   - **Platform:** Modern / Legacy / Both

   ### 2. [Test Name]
   ...

   ## Common Issues
   - Issue 1 and how to fix
   - Issue 2 and how to fix

   ## Post-Testing
   - [ ] Cleanup step 1
   - [ ] Cleanup step 2
   ```

6. **Be specific and actionable:**
   - Don't say "test login" - say "Click login button, enter test@example.com/password, verify redirects to home"
   - Include example data (recipe URLs, search terms)
   - Mention exact buttons, fields, UI elements to interact with

7. **iPad-specific guidance** (for legacy tests):
   - How to open Safari Web Inspector (Settings → Safari → Advanced)
   - How to clear cache (Settings → Safari → Clear History and Website Data)
   - How to check for JavaScript syntax errors
   - What to look for in console logs

## Example Output for "legacy"

```markdown
# QA Checklist: Legacy Frontend (iOS 9 iPad)

## Pre-requisites
- [ ] Code deployed to test environment
- [ ] Containers restarted after legacy JS changes
- [ ] Verified static files copied: `grep "unique string" ./staticfiles/legacy/js/...`
- [ ] iPad connected to same network as test server
- [ ] Safari cache cleared on iPad

## Test Cases

### 1. Profile Selection
- **Action:** Open http://test-server:8000/legacy/ on iPad, select a profile
- **Expected:** Profile page loads, shows user's name and settings
- **Verify:** Console has no syntax errors (check Web Inspector)
- **Platform:** Legacy only

### 2. Search Functionality
- **Action:** Tap search icon, enter "chicken pasta", tap search
- **Expected:** Results appear with images and titles, no console errors
- **Verify:**
  - Images load (may take a moment for caching)
  - Tap result opens detail page
  - Check console for ES5 syntax errors
- **Platform:** Legacy only
- **Common Issue:** If images don't appear, check background caching is working

### 3. Recipe Detail - ES5 Syntax Check
- **Action:** Open recipe detail page
- **Expected:** Page renders completely, no syntax errors
- **Verify:**
  - Open Web Inspector: Settings → Safari → Advanced → Web Inspector
  - Check Console tab for errors
  - Look for "SyntaxError" or "unexpected token"
- **Platform:** Legacy only
- **Common Issues:**
  - `const`/`let` syntax errors → Check .claude/rules/es5-compliance.md
  - Arrow function errors → Should use `function()` keyword
  - Template literal errors → Should use string concatenation

...more test cases...

## Common Issues

### "SyntaxError: Unexpected token 'const'"
- **Cause:** ES6 const/let used in legacy JS
- **Fix:** Replace with `var`, restart containers
- **Verify:** `grep "const " apps/legacy/static/legacy/js/`

### Images not loading in search results
- **Cause:** Background caching may take a few seconds
- **Fix:** Refresh page, images should appear
- **Check:** `curl http://server/api/recipes/cache/health/`

### Page completely blank
- **Cause:** JavaScript syntax error blocking execution
- **Fix:** Check Safari Web Inspector Console
- **Verify:** Look for syntax errors, check ES5 compliance

## Post-Testing
- [ ] Document any issues found
- [ ] Note iOS 9 specific behaviors
- [ ] Verify fixes on iPad before closing
```

Now generate the appropriate checklist based on the user's requested feature area!
