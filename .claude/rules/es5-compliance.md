---
paths:
  - "apps/legacy/static/legacy/**"
---

# ES5 Compliance for Legacy Frontend

All code in `apps/legacy/static/legacy/js/` MUST be ES5 compatible for iOS 9.3 Safari (iPad 2/3/4, iPad Mini 1). No transpilation — code runs as-written.

## Forbidden Syntax (ES6+)

| ES6+ (forbidden) | ES5 (required) |
|-------------------|----------------|
| `const` / `let` | `var` |
| `() => {}` | `function() {}` |
| `` `Hello ${name}` `` | `'Hello ' + name` |
| `async` / `await` | `.then()` callbacks |
| `{x, y} = obj` | `var x = obj.x;` |
| `[a, b] = arr` | `var a = arr[0];` |
| `...arr` / `...obj` | `.concat()` / `Object.assign()` |
| `class Foo {}` | `function Foo() {}` + `.prototype` |
| `function(x = 1)` | `function(x) { x = x \|\| 1; }` |
| `{method() {}}` | `{method: function() {}}` |
| `for (x of arr)` | `for (var i = 0; i < arr.length; i++)` |

## CSS Compatibility (iOS 9 Safari)

Legacy CSS in `apps/legacy/static/legacy/css/` MUST avoid:

- CSS Grid, `var(--x)`, `gap` on flexbox, `position: sticky`, `backdrop-filter`, `:focus-visible`, `:is()`, `:where()`, `:has()`, `aspect-ratio`, logical properties (`margin-inline`), `clamp()`, `min()`/`max()` functions
- **Use instead**: flexbox with `-webkit-` prefix, floats, literal color values, margin-based spacing, media queries for responsive values

**Images**: WebP NOT supported — use JPEG or PNG only.
**Touch targets**: minimum 44x44px.

## Container Restart Required

After ANY change to `apps/legacy/static/`:
```bash
docker compose down && docker compose up -d
```
The entrypoint runs `collectstatic` on container start.

## Design Quality

The legacy frontend is not a second-class citizen — it MUST maintain visual coherence with the modern React frontend.
