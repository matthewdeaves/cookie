---
description: ES5 JavaScript compliance for iOS 9 Safari compatibility
---

# ES5 Compliance for Legacy Frontend

All code in `apps/legacy/static/legacy/js/` MUST be ES5 compatible for iOS 9.3 Safari.

## Target Environment

- **Browser**: Mobile Safari on iOS 9.3.6
- **Device**: Old iPads (iPad 2, iPad 3, iPad 4, iPad Mini 1)
- **JavaScript**: ECMAScript 5 (2009 spec)
- **No transpilation**: Code runs as-written

## Forbidden Syntax (ES6+)

These will cause syntax errors or runtime failures on iOS 9:

| Syntax | ES6+ (❌ Forbidden) | ES5 (✅ Required) |
|--------|---------------------|-------------------|
| Variables | `const x = 1;`<br>`let y = 2;` | `var x = 1;`<br>`var y = 2;` |
| Functions | `() => {}` | `function() {}` |
| Strings | `` `Hello ${name}` `` | `'Hello ' + name` |
| Async | `async function f() {}`<br>`await promise;` | `function f() { return promise; }`<br>`promise.then(...)` |
| Destructuring | `var {x, y} = obj;`<br>`var [a, b] = arr;` | `var x = obj.x;`<br>`var a = arr[0];` |
| Spread | `...arr`<br>`...obj` | `arr.concat()`<br>`Object.assign()` |
| Classes | `class Foo {}` | `function Foo() {}`<br>`Foo.prototype.method = function() {}` |
| Default params | `function f(x = 1) {}` | `function f(x) { x = x || 1; }` |
| Object shorthand | `{x, y}` | `{x: x, y: y}` |
| Method syntax | `{method() {}}` | `{method: function() {}}` |
| For-of | `for (let x of arr)` | `for (var i = 0; i < arr.length; i++)` |

## Allowed ES5 Features

✅ **Safe to use:**
- `var` declarations
- `function` keyword
- String concatenation with `+`
- Array methods: `map()`, `filter()`, `forEach()`, `reduce()`
- Object methods: `Object.keys()`, `Object.create()`
- Traditional `for` and `while` loops
- `try/catch/finally`
- `JSON.parse()` / `JSON.stringify()`
- `Array.isArray()`
- `Function.prototype.bind()`

⚠️ **Needs polyfill or check:**
- `Promise` (polyfill available)
- `Object.assign()` (polyfill available)
- `Array.prototype.find()` (ES6 - needs polyfill)

## Common Gotchas

### Variable Hoisting
```javascript
// ES6: Block scoped
if (true) {
  let x = 1; // x only exists in if block
}

// ES5: Function scoped
if (true) {
  var x = 1; // x exists in entire function
}
```

### Callback Context
```javascript
// ES6: Arrow preserves this
button.addEventListener('click', () => {
  this.handleClick(); // this is outer context
});

// ES5: Must bind or use closure
var self = this;
button.addEventListener('click', function() {
  self.handleClick(); // use closure variable
});
// OR
button.addEventListener('click', this.handleClick.bind(this));
```

## Container Restart Required

After ANY change to `apps/legacy/static/`:

```bash
docker compose down && docker compose up -d
```

**Why?** The entrypoint runs `collectstatic` on container start, copying from `apps/legacy/static/` to `./staticfiles/` (which nginx serves).

**Verify changes were copied:**
```bash
grep "unique string from your change" ./staticfiles/legacy/js/pages/detail.js
docker compose logs web | grep "Collecting static"
```

## Testing on iOS 9

See `/qa-session` skill for complete manual testing checklist.

**Quick smoke test:**
1. Deploy to staging/production
2. Open Safari on iPad
3. Check Console for syntax errors (Settings → Safari → Advanced → Web Inspector)
4. Test critical user journeys

**Clear cache after deploy:**
Settings → Safari → Clear History and Website Data

## References

- ES5 Specification: https://262.ecma-international.org/5.1/
- iOS 9 Safari compatibility: https://caniuse.com/?compare=ios_saf+9.3&compareCats=all
- Inside Macintosh: Not applicable (this is web, not Classic Mac!)
