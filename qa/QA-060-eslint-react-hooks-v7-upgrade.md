# QA-060: eslint-plugin-react-hooks v7 Upgrade Breaks Build

## Status
**RESOLVED** - Fix applied to `frontend/src/App.tsx`

## Phase
Dependency Upgrades

## Issue

PR #9 upgrades `eslint-plugin-react-hooks` from 5.2.0 to 7.0.1 (major version upgrade). The build fails with:

```
src/App.tsx:60:7  error  Cannot access variable before it is declared
`loadFavorites` is accessed before it is declared
```

---

## Root Cause Analysis

### The Code Pattern

**File:** `frontend/src/App.tsx:58-73`

```typescript
// Lines 58-64: useEffect calls loadFavorites
useEffect(() => {
  if (currentProfile) {
    loadFavorites()  // Called on line 60
  } else {
    setFavoriteRecipeIds(new Set())
  }
}, [currentProfile])

// Lines 66-73: loadFavorites is declared AFTER the useEffect
const loadFavorites = async () => {
  try {
    const favorites = await api.favorites.list()
    setFavoriteRecipeIds(new Set(favorites.map((f) => f.recipe.id)))
  } catch (error) {
    console.error('Failed to load favorites:', error)
  }
}
```

The code relies on JavaScript function hoisting. In regular JavaScript, this works at runtime because `const` arrow functions are hoisted (though they remain in the "temporal dead zone" until their declaration line is reached). However, since the callback passed to `useEffect` is not immediately executed (it runs after render), the function is available when needed.

### Why v7 Catches This

`eslint-plugin-react-hooks` v7 includes React Compiler diagnostics that are surfaced automatically via ESLint. The plugin now enforces stricter rules around variable access patterns to ensure code is compatible with React Compiler's optimization strategies.

Per the [React docs](https://react.dev/reference/eslint-plugin-react-hooks), v7 includes 17 rules in the `recommended` preset, including:
- `purity` - Validates components/hooks are pure
- `immutability` - Prevents mutating props, state, and immutable values
- `refs` - Ensures correct ref usage

The "Cannot access variable before it is declared" error comes from React Compiler's static analysis, which requires variables to be declared before they are referenced in the source code, regardless of runtime hoisting behavior.

---

## Research

### eslint-plugin-react-hooks v7 Changes

From the [React Compiler v1.0 announcement](https://react.dev/blog/2025/04/21/react-compiler-v1-0) and [eslint-plugin-react-hooks docs](https://react.dev/reference/eslint-plugin-react-hooks):

1. **React Compiler Integration**: v7 surfaces React Compiler diagnostics automatically via ESLint, even if the app hasn't adopted the compiler yet.

2. **Stricter Analysis**: The compiler performs static analysis that requires cleaner code patterns for optimization compatibility.

3. **Migration Path**: Users are expected to remove `eslint-plugin-react-compiler` (if present) and upgrade to `eslint-plugin-react-hooks` v7.

### Known Issues

- [GitHub Issue #34888](https://github.com/facebook/react/issues/34888): Recursive functions confuse the compiler with similar "Cannot access variable before it is declared" errors.
- [GitHub Issue #34795](https://github.com/facebook/react/issues/34795): Error messages are verbose, printing entire function bodies.

### Temporal Dead Zone (TDZ)

The [ESLint `no-use-before-define` rule](https://eslint.org/docs/latest/rules/no-use-before-define) explains:

> In ES6, block-level bindings (`let` and `const`) introduce a "temporal dead zone" where a ReferenceError will be thrown with any attempt to access the variable before its declaration.

While JavaScript's runtime behavior allows the pattern used in `App.tsx` (because `useEffect`'s callback executes after the component renders), React Compiler's static analysis flags it as problematic.

---

## Options

### Option 1: Close PR #9 (Keep eslint-plugin-react-hooks v5.x)

**Pros:**
- No code changes required
- Immediate unblock

**Cons:**
- Miss out on React Compiler diagnostics
- Technical debt accumulates
- Future React 19+ compatibility concerns

### Option 2: Fix the Code (Recommended)

Move `loadFavorites` declaration before the `useEffect` that uses it. Two sub-options:

#### Option 2a: Move function declaration up

```typescript
// Declare first
const loadFavorites = async () => {
  try {
    const favorites = await api.favorites.list()
    setFavoriteRecipeIds(new Set(favorites.map((f) => f.recipe.id)))
  } catch (error) {
    console.error('Failed to load favorites:', error)
  }
}

// Then use in useEffect
useEffect(() => {
  if (currentProfile) {
    loadFavorites()
  } else {
    setFavoriteRecipeIds(new Set())
  }
}, [currentProfile])
```

#### Option 2b: Wrap in useCallback (preferred for deps tracking)

```typescript
const loadFavorites = useCallback(async () => {
  try {
    const favorites = await api.favorites.list()
    setFavoriteRecipeIds(new Set(favorites.map((f) => f.recipe.id)))
  } catch (error) {
    console.error('Failed to load favorites:', error)
  }
}, [])

useEffect(() => {
  if (currentProfile) {
    loadFavorites()
  } else {
    setFavoriteRecipeIds(new Set())
  }
}, [currentProfile, loadFavorites])
```

**Pros:**
- Enables React Compiler diagnostics
- Better code hygiene
- Future-proofs for React 19+

**Cons:**
- Requires code change (minimal)

---

## Recommendation

**Option 2a** - Move the function declaration before the `useEffect`. This is the minimal fix that:
1. Resolves the lint error
2. Follows JavaScript best practices
3. Enables the eslint-plugin-react-hooks v7 upgrade

Using `useCallback` (Option 2b) is not strictly necessary here since `loadFavorites` has no dependencies and is only called from the `useEffect`.

---

## Priority

**High** - Blocks PR #9 which includes important dependency upgrades.

## Affected Components

- `frontend/src/App.tsx` - Main application component

---

## Implementation Plan

### Step 1: Move loadFavorites declaration

**File:** `frontend/src/App.tsx`

1. Cut the `loadFavorites` function (lines 66-73)
2. Paste it before the useEffect that calls it (before line 58)
3. Ensure proper spacing/formatting

### Step 2: Verify build

```bash
cd frontend && npm run lint && npm run build
```

### Step 3: Test functionality

1. Start the app
2. Select a profile
3. Verify favorites load correctly
4. Check console for errors

### Step 4: Update PR #9

Commit the fix to the branch for PR #9 or as a separate preparatory PR.

---

## Verification Results

**Date:** 2026-01-10
**Commit:** `966ac61`

### Fixes Applied

1. **Move loadFavorites declaration before useEffect**
   - Fixes "Cannot access variable before it is declared"

2. **Remove theme sync effect, set theme in handleProfileSelect**
   - Fixes "Calling setState synchronously within an effect"

3. **Move favorites clearing from effect to handleLogout**
   - Same fix as above for `setFavoriteRecipeIds(new Set())`

4. **Inline favorites loading as promise chain**
   - Clearer async pattern that satisfies `set-state-in-effect` rule

### Test Results

| Check | Result |
|-------|--------|
| `npm run lint` (v7) | 0 errors, 17 warnings |
| `npm run build` | Built in 3.69s |
| `npm test` | 65 tests passed (3 test files) |

All `react-hooks/set-state-in-effect` and declaration order errors resolved.

---

## References

- [eslint-plugin-react-hooks docs](https://react.dev/reference/eslint-plugin-react-hooks)
- [React Compiler v1.0 Announcement](https://react.dev/blog/2025/04/21/react-compiler-v1-0)
- [ESLint no-use-before-define](https://eslint.org/docs/latest/rules/no-use-before-define)
- [GitHub Issue #34888 - Recursive functions](https://github.com/facebook/react/issues/34888)
- [GitHub Issue #34795 - Verbose error messages](https://github.com/facebook/react/issues/34795)
