# Phase 11: Fix npm Security Vulnerabilities

## Overview

Upgrade Vitest from v2.1.8 to v4.x to resolve 6 moderate severity vulnerabilities in the esbuild dependency chain. This is a breaking change upgrade that requires test adjustments.

**Vulnerability Chain:**
```
esbuild <=0.24.2 (GHSA-67mh-4wv8-2f99)
  └── vite 0.11.0 - 6.1.6
      └── vite-node <=2.2.0-beta.2
      └── @vitest/mocker <=3.0.0-beta.4
          └── vitest 0.3.3 - 3.0.0-beta.4
              └── @vitest/coverage-v8 <=2.2.0-beta.2
```

**Fix:** Upgrade to `vitest@^4.0.16` and `@vitest/coverage-v8@^4.0.16`

---

## Session Scope

| Session | Tasks | Focus | Files Changed |
|---------|-------|-------|---------------|
| A | 11.1-11.3 | Upgrade packages + fix breaking changes | `frontend/package.json`, `frontend/vitest.config.ts`, test files |

---

## Phase 11.1: Upgrade Vitest Packages

### Pre-Upgrade Verification

Run tests in dev container to confirm current state:

```bash
docker compose exec frontend npm test
docker compose exec frontend npm audit
```

### Upgrade Commands

```bash
docker compose exec frontend npm install vitest@^4.0.16 @vitest/coverage-v8@^4.0.16 --save-dev
```

### File Changes: `frontend/package.json`

Update devDependencies:

```json
{
  "devDependencies": {
    "vitest": "^4.0.16",
    "@vitest/coverage-v8": "^4.0.16"
  }
}
```

---

## Phase 11.2: Fix Vitest 4 Breaking Changes

### Breaking Change 1: `vi.restoreAllMocks()` Behavior

**Change:** `vi.restoreAllMocks()` no longer resets mocks created with `vi.fn()`. It only restores mocks created with `vi.spyOn()`.

**Affected Files:**
- `frontend/src/test/api.test.ts` (line 14)
- `frontend/src/test/components.test.tsx` (line 57, 170)

**Fix:** Replace `vi.restoreAllMocks()` with `vi.resetAllMocks()` for `vi.fn()` mocks, or remove if `vi.clearAllMocks()` in `beforeEach` is sufficient.

**Before:**
```typescript
afterEach(() => {
  vi.restoreAllMocks()
})
```

**After:**
```typescript
afterEach(() => {
  vi.resetAllMocks()
})
```

### Breaking Change 2: Mock Constructor Behavior

**Change:** Mocks called with `new` keyword now construct instances instead of calling `mock.apply`. Arrow functions will throw `is not a constructor` error.

**Current Tests:** No tests use mock constructors - no changes needed.

### Breaking Change 3: `invocationCallOrder` Starts at 1

**Change:** `vi.fn().mock.invocationCallOrder` now starts at 1 instead of 0.

**Current Tests:** No tests check `invocationCallOrder` - no changes needed.

### Breaking Change 4: Coverage Options Removed

**Change:** `coverage.all` and `coverage.ignoreEmptyLines` options removed.

**Current Config:** Does not use these options - no changes needed.

### File Changes: `frontend/src/test/api.test.ts`

```typescript
// Line 14: Change from
afterEach(() => {
  vi.restoreAllMocks()
})

// To:
afterEach(() => {
  vi.resetAllMocks()
})
```

### File Changes: `frontend/src/test/components.test.tsx`

```typescript
// Line 57 and 170: Change from
afterEach(() => {
  vi.restoreAllMocks()
})

// To:
afterEach(() => {
  vi.resetAllMocks()
})
```

---

## Phase 11.3: Verify and Test

### Run Tests

```bash
docker compose exec frontend npm test
```

**Expected:** All 55+ tests pass.

### Run Coverage

```bash
docker compose exec frontend npm run test:coverage
```

**Expected:** Coverage report generates without errors.

### Verify Security Fix

```bash
docker compose exec frontend npm audit
```

**Expected:** 0 vulnerabilities (or no moderate/high/critical).

### Run Full CI Locally (Optional)

```bash
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

---

## Verification Checklist

- [ ] `npm install vitest@^4.0.16 @vitest/coverage-v8@^4.0.16 --save-dev` completes
- [ ] All tests pass with `npm test`
- [ ] Coverage report generates with `npm run test:coverage`
- [ ] `npm audit` shows 0 moderate+ vulnerabilities
- [ ] ESLint passes with `npm run lint`
- [ ] Build succeeds with `npm run build`
- [ ] CI pipeline passes after push

---

## Rollback Plan

If issues arise:

```bash
docker compose exec frontend npm install vitest@^2.1.8 @vitest/coverage-v8@^2.1.8 --save-dev
git checkout frontend/src/test/api.test.ts frontend/src/test/components.test.tsx
```

---

## References

- [Vitest 4.0 Migration Guide](https://vitest.dev/guide/migration.html)
- [Vitest 4.0 Announcement](https://vitest.dev/blog/vitest-4)
- [GHSA-67mh-4wv8-2f99 - esbuild vulnerability](https://github.com/advisories/GHSA-67mh-4wv8-2f99)
