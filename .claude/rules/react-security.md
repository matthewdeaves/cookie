---
paths:
  - "frontend/src/**/*.{ts,tsx}"
---

# React Security Rules

## Hard Rules

- **No `dangerouslySetInnerHTML`** — JSX auto-escapes by default. If raw HTML is absolutely needed, sanitize with DOMPurify first.
- **No `eval` or `new Function`** — never execute user-controlled strings.
- **No `element.innerHTML`** — use `textContent` or React JSX (auto-escaped).
- **Validate URLs in `href`** — `javascript:` URLs execute. Only allow `http://https://` protocols.
- **Validate redirect URLs** — only allow relative paths starting with `/` (not `//`). Prevent open redirects.
- **Whitelist dynamic components** — never render `components[userInput]`. Use an explicit allowed map.
- **No sensitive data in localStorage** — no passwords, API keys, or session tokens. Use httpOnly cookies.
- **No user-controlled dynamic imports** — `await import(userInput)` is arbitrary code execution.

## Safe Patterns

- JSX `{variable}` is always escaped — safe for user content
- `<img src={url}>` does not execute javascript: URLs — safe
- `onClick={() => fn()}` is a function reference — safe (never use `onClick={() => eval(x)}`)
- Type-check API responses with TypeScript interfaces or Zod schemas

## CI Enforcement

ESLint security plugin and `npm audit` run automatically in CI.
