---
description: iOS 9 Safari CSS limitations and safe patterns
paths:
  - "apps/legacy/static/legacy/css/**/*"
  - "apps/legacy/templates/**/*"
---

# iOS 9 Safari CSS Reference

CSS features available and unavailable in Mobile Safari on iOS 9.3.6.

## Flexbox - FULLY SUPPORTED

iOS 9 Safari has full flexbox support (unprefixed):

```css
/* All of these work */
.container {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    align-content: stretch;
}

.item {
    flex: 1 1 auto;
    flex-grow: 1;
    flex-shrink: 0;
    flex-basis: 200px;
    align-self: flex-start;
    order: 1;
}
```

### Flexbox Quirks

```css
/* Bug: flex-basis with calc() may fail */
.item {
    flex-basis: calc(50% - 10px);  /* May not work */
    width: calc(50% - 10px);       /* Use width instead */
    flex-basis: auto;
}

/* Bug: min-height on flex container */
.container {
    display: flex;
    min-height: 100vh;  /* Children may not stretch properly */
    height: 100vh;      /* Use height instead when possible */
}
```

## CSS Grid - NOT AVAILABLE

> **iOS 9 Safari does NOT support CSS Grid**

| Feature | iOS 9 | Alternative |
|---------|-------|-------------|
| `display: grid` | ❌ | Flexbox or floats |
| `grid-template-*` | ❌ | Flexbox with `flex-wrap` |
| `grid-gap` | ❌ | Margins |
| `grid-area` | ❌ | Flexbox `order` |

### Grid Alternative Pattern

```css
/* Instead of grid, use flexbox */
.grid-replacement {
    display: flex;
    flex-wrap: wrap;
    margin: -10px;  /* Negative margin for gap */
}

.grid-item {
    flex: 0 0 calc(33.333% - 20px);
    margin: 10px;
}

/* Or use inline-block for simpler layouts */
.simple-grid {
    font-size: 0;  /* Remove whitespace gaps */
}

.simple-grid-item {
    display: inline-block;
    width: 33.333%;
    font-size: 16px;  /* Reset font size */
    vertical-align: top;
}
```

## CSS Variables - NOT AVAILABLE

> **iOS 9 Safari does NOT support CSS Custom Properties**

```css
/* Does NOT work */
:root {
    --primary-color: #007bff;
}
.button {
    background: var(--primary-color);  /* Fails silently */
}

/* Use preprocessor variables (Sass) or static values */
.button {
    background: #007bff;
}
```

## Viewport Units

| Unit | iOS 9 | Notes |
|------|-------|-------|
| `vw` | ✅ | Works |
| `vh` | ⚠️ | Buggy - see below |
| `vmin` | ✅ | Works |
| `vmax` | ✅ | Works |

### vh Unit Bug

```css
/* vh includes Safari toolbar height, causing jumps */
.fullscreen {
    height: 100vh;  /* Jumps when toolbar shows/hides */
}

/* Workaround: Use JavaScript to set height */
```

```javascript
// Set --vh custom property (but CSS vars don't work, so use inline style)
function setVh() {
    var vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', vh + 'px');
    // For iOS 9, set directly on elements
    var fullscreen = document.querySelector('.fullscreen');
    if (fullscreen) {
        fullscreen.style.height = window.innerHeight + 'px';
    }
}
window.addEventListener('resize', setVh);
setVh();
```

## Position: sticky - NOT AVAILABLE

> **iOS 9 Safari does NOT support `position: sticky`**

```css
/* Does NOT work */
.header {
    position: sticky;
    top: 0;
}

/* Alternative: position: fixed */
.header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
}
.content {
    padding-top: 60px;  /* Account for fixed header height */
}
```

## Transforms

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `transform` | ✅ | Unprefixed |
| `transform-origin` | ✅ | |
| `translate()` | ✅ | |
| `rotate()` | ✅ | |
| `scale()` | ✅ | |
| `skew()` | ✅ | |
| `matrix()` | ✅ | |
| `translate3d()` | ✅ | Hardware accelerated |
| `perspective` | ✅ | |

### Hardware Acceleration

```css
/* Force GPU acceleration for smooth animations */
.animated {
    transform: translateZ(0);  /* or translate3d(0,0,0) */
    will-change: transform;    /* Hint to browser */
}
```

## Transitions & Animations

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `transition` | ✅ | Unprefixed |
| `animation` | ✅ | Unprefixed |
| `@keyframes` | ✅ | Unprefixed |
| `animation-fill-mode` | ✅ | |

```css
/* Transitions work normally */
.button {
    transition: background-color 0.3s ease, transform 0.2s ease;
}

.button:active {
    transform: scale(0.95);
}

/* Keyframe animations work */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.fade-in {
    animation: fadeIn 0.3s ease forwards;
}
```

## Filters

| Filter | iOS 9 | Notes |
|--------|-------|-------|
| `blur()` | ✅ | `-webkit-filter` prefix needed |
| `brightness()` | ✅ | |
| `contrast()` | ✅ | |
| `grayscale()` | ✅ | |
| `saturate()` | ✅ | |
| `sepia()` | ✅ | |
| `backdrop-filter` | ❌ | iOS 9 doesn't support |

```css
/* Must use -webkit- prefix */
.blurred {
    -webkit-filter: blur(5px);
    filter: blur(5px);
}

/* backdrop-filter NOT supported - use overlay instead */
.overlay {
    background: rgba(0, 0, 0, 0.5);  /* Semi-transparent overlay */
}
```

## Gradients

```css
/* Linear gradients work */
.gradient {
    background: linear-gradient(to bottom, #fff, #f0f0f0);
}

/* Radial gradients work */
.radial {
    background: radial-gradient(circle, #fff, #000);
}

/* Multiple backgrounds work */
.multi {
    background:
        linear-gradient(to bottom, transparent, rgba(0,0,0,0.5)),
        url('image.jpg');
}
```

## calc() - SUPPORTED

```css
/* calc() works in iOS 9 */
.sidebar {
    width: calc(100% - 250px);
}

.padded {
    padding: calc(1rem + 10px);
}

/* But avoid in flex-basis (buggy) */
```

## Media Queries

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `@media (min-width)` | ✅ | |
| `@media (max-width)` | ✅ | |
| `@media (orientation)` | ✅ | |
| `@media (hover)` | ❌ | Always false on touch |
| `@media (pointer)` | ❌ | |
| `@media (prefers-color-scheme)` | ❌ | |
| `@media (prefers-reduced-motion)` | ❌ | |

```css
/* Standard responsive breakpoints work */
@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }
}

/* Orientation works */
@media (orientation: landscape) {
    .fullscreen {
        flex-direction: row;
    }
}
```

## Pseudo-elements & Pseudo-classes

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `::before` | ✅ | |
| `::after` | ✅ | |
| `:hover` | ⚠️ | Triggers on tap, stays until tap elsewhere |
| `:active` | ✅ | But needs `-webkit-tap-highlight-color` |
| `:focus` | ✅ | |
| `:not()` | ✅ | Single selector only |
| `:nth-child()` | ✅ | |
| `:first-child` | ✅ | |
| `:last-child` | ✅ | |
| `:focus-within` | ❌ | |
| `:focus-visible` | ❌ | |

### Touch Feedback

```css
/* Enable :active on iOS */
button {
    -webkit-tap-highlight-color: transparent;  /* Remove default highlight */
}

button:active {
    background: #0056b3;
    transform: scale(0.98);
}

/* Alternative: Use JavaScript for touch feedback */
```

## Box Model

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `box-sizing` | ✅ | Unprefixed |
| `border-radius` | ✅ | |
| `box-shadow` | ✅ | |
| `outline` | ✅ | |
| `object-fit` | ✅ | |
| `object-position` | ✅ | |

```css
/* Apply border-box globally */
*, *::before, *::after {
    box-sizing: border-box;
}

/* object-fit for images */
.cover-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
}
```

## Typography

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `@font-face` | ✅ | WOFF supported |
| `font-feature-settings` | ✅ | |
| `text-overflow: ellipsis` | ✅ | |
| `word-break` | ✅ | |
| `hyphens` | ⚠️ | Needs `-webkit-hyphens` |
| `font-variant-numeric` | ❌ | Use `font-feature-settings` |

```css
/* Text truncation */
.truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Multi-line truncation */
.line-clamp {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* Hyphenation needs prefix */
.hyphenate {
    -webkit-hyphens: auto;
    hyphens: auto;
}
```

## Colors

| Format | iOS 9 | Notes |
|--------|-------|-------|
| `#rgb` | ✅ | |
| `#rrggbb` | ✅ | |
| `rgb()` | ✅ | |
| `rgba()` | ✅ | |
| `hsl()` | ✅ | |
| `hsla()` | ✅ | |
| `#rrggbbaa` | ❌ | Use `rgba()` |
| `rgb(r g b / a)` | ❌ | Use `rgba(r, g, b, a)` |
| `color()` | ❌ | |
| `lab()` | ❌ | |
| `oklch()` | ❌ | |

```css
/* Use rgba() for transparency */
.overlay {
    background: rgba(0, 0, 0, 0.5);  /* Works */
    background: #00000080;           /* Does NOT work */
}
```

## Scroll Behavior

| Feature | iOS 9 | Notes |
|---------|-------|-------|
| `overflow-x/y` | ✅ | |
| `-webkit-overflow-scrolling` | ✅ | Critical for smooth scroll |
| `scroll-behavior: smooth` | ❌ | Use JavaScript |
| `overscroll-behavior` | ❌ | |
| `scroll-snap-*` | ❌ | |

```css
/* CRITICAL: Enable momentum scrolling on iOS */
.scrollable {
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;  /* Smooth scrolling */
}

/* Without this, scrolling feels "stuck" */
```

## Not Supported in iOS 9

These CSS features do NOT work:

- `display: grid` and all grid properties
- `position: sticky`
- CSS Custom Properties (`--var`)
- `backdrop-filter`
- `gap` on flexbox (works on grid only, which doesn't exist)
- `:focus-within`, `:focus-visible`
- `aspect-ratio`
- `clamp()`, `min()`, `max()`
- Container queries
- `@supports`
- Subgrid
- `content-visibility`
- `color-scheme`

## Testing CSS Changes

1. After CSS changes: `docker compose down && docker compose up -d`
2. Clear Safari cache on iPad: Settings → Safari → Clear History and Website Data
3. Hard refresh: Tap and hold reload button
4. Check Web Inspector for CSS errors (requires Mac + Safari + USB cable)

## References

- iOS 9 Safari on caniuse: https://caniuse.com/?compare=ios_saf+9.3
- WebKit CSS support: https://webkit.org/status/
