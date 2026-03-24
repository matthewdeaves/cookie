---
description: React security patterns - XSS prevention, safe rendering
---

# React Security

React has XSS protections by default, but developers can bypass them. This document covers safe patterns and common pitfalls.

## XSS Prevention

### JSX Auto-Escapes

✅ **Safe by default** - React escapes values:
```jsx
// Safe - React escapes recipe.name
<h1>{recipe.name}</h1>
<p>{recipe.description}</p>

// Safe - Even if name contains <script>, it's escaped
const name = "<script>alert('xss')</script>";
<div>{name}</div>  // Renders as text, not executed
```

### dangerouslySetInnerHTML

❌ **Dangerous** - Allows raw HTML:
```jsx
// VULNERABLE - XSS if recipe.html is user-controlled!
<div dangerouslySetInnerHTML={{__html: recipe.html}} />
```

✅ **Safe** - Sanitize first if needed:
```jsx
import DOMPurify from 'dompurify';

// Only if you MUST render HTML
const sanitized = DOMPurify.sanitize(recipe.html, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br'],
  ALLOWED_ATTR: []
});
<div dangerouslySetInnerHTML={{__html: sanitized}} />
```

**Better:** Avoid `dangerouslySetInnerHTML` entirely. Use markdown or structured data instead:
```jsx
import ReactMarkdown from 'react-markdown';

// Safe - Markdown is parsed, not executed
<ReactMarkdown>{recipe.description}</ReactMarkdown>
```

## URL Safety

### Href Injection

❌ **Dangerous** - JavaScript URLs execute:
```jsx
// VULNERABLE - If url is "javascript:alert('xss')"
<a href={url}>Link</a>
```

✅ **Safe** - Validate URLs:
```jsx
function isSafeUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

// Safe - Only allows http/https
<a href={isSafeUrl(url) ? url : '#'}>Link</a>
```

### Image Sources

✅ **Safe** - React doesn't execute src:
```jsx
// Safe - Even if imageUrl is javascript:, it won't execute
<img src={recipe.imageUrl} alt={recipe.name} />
```

But still validate for good practice:
```jsx
const imageUrl = recipe.imageUrl?.startsWith('http')
  ? recipe.imageUrl
  : '/static/placeholder.jpg';
<img src={imageUrl} alt={recipe.name} />
```

## Event Handlers

### onClick Safety

✅ **Safe** - Functions, not strings:
```jsx
// Safe - onClick expects function
<button onClick={() => handleClick(recipe.id)}>
  Click
</button>

// Safe - Even if name contains <script>
<button onClick={() => alert(recipe.name)}>
  {recipe.name}
</button>
```

❌ **Dangerous** - Don't use eval:
```jsx
// VULNERABLE - eval executes arbitrary code!
<button onClick={() => eval(recipe.action)}>
  Click
</button>
```

## Component Injection

### Dynamic Components

❌ **Dangerous** - Arbitrary component rendering:
```jsx
// VULNERABLE - User controls which component renders!
const Component = components[userInput];
<Component {...props} />
```

✅ **Safe** - Whitelist components:
```jsx
const ALLOWED_COMPONENTS = {
  'header': HeaderComponent,
  'footer': FooterComponent,
  'recipe': RecipeComponent
};

const Component = ALLOWED_COMPONENTS[userInput] || DefaultComponent;
<Component {...props} />
```

## API Data Handling

### Rendering API Responses

✅ **Type check API data:**
```typescript
interface Recipe {
  id: number;
  name: string;
  description: string;
}

async function fetchRecipe(id: number): Promise<Recipe> {
  const response = await fetch(`/api/recipes/${id}`);
  const data = await response.json();

  // Validate shape matches expected interface
  if (typeof data.name !== 'string') {
    throw new Error('Invalid recipe data');
  }

  return data;
}
```

✅ **Use Zod for runtime validation:**
```typescript
import { z } from 'zod';

const RecipeSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string(),
  imageUrl: z.string().url().optional()
});

const data = await response.json();
const recipe = RecipeSchema.parse(data); // Throws if invalid
```

## Local Storage

### Don't Store Sensitive Data

❌ **NEVER store in localStorage:**
- Passwords
- API keys
- Session tokens
- Credit card numbers

✅ **OK for localStorage:**
- User preferences (theme, language)
- Non-sensitive UI state
- Public data cache

```typescript
// Safe - Non-sensitive preference
localStorage.setItem('theme', theme);

// WRONG - Sensitive data!
localStorage.setItem('apiKey', key);  // Use httpOnly cookies instead
```

## Third-Party Libraries

### Package Security

✅ **Check dependencies regularly:**
```bash
# Run security audit
docker compose exec frontend npm audit

# Fix vulnerabilities automatically
docker compose exec frontend npm audit fix
```

### Dynamic Imports

✅ **Only import known modules:**
```typescript
// Safe - Static import
import { Button } from '@/components/ui/button';

// Safe - Dynamic with known path
const module = await import('@/features/recipes');

// DANGEROUS - User-controlled path!
const module = await import(userInput);  // Don't do this!
```

## React Router

### Route Parameters

✅ **Validate route params:**
```typescript
import { useParams } from 'react-router-dom';
import { z } from 'zod';

function RecipeDetail() {
  const { id } = useParams();

  // Validate it's a number
  const recipeId = z.coerce.number().parse(id);

  // Use validated ID
  const { data } = useQuery(['recipe', recipeId], () =>
    fetchRecipe(recipeId)
  );

  return <div>{data?.name}</div>;
}
```

### Redirect Safety

❌ **Dangerous** - Open redirect:
```typescript
// VULNERABLE - Can redirect to evil.com!
const redirect = new URLSearchParams(location.search).get('redirect');
navigate(redirect);
```

✅ **Safe** - Validate redirect URLs:
```typescript
function isSafeRedirect(url: string): boolean {
  // Only allow relative URLs (no protocol)
  return url.startsWith('/') && !url.startsWith('//');
}

const redirect = new URLSearchParams(location.search).get('redirect');
if (redirect && isSafeRedirect(redirect)) {
  navigate(redirect);
} else {
  navigate('/');
}
```

## Content Security Policy

### Meta Tag (Basic)

✅ **Add CSP to index.html:**
```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self';
               style-src 'self' 'unsafe-inline';
               img-src 'self' data: https:;">
```

### Nginx Header (Better)

✅ **Set CSP in nginx config:**
```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;";
```

## Common Pitfalls

### 1. innerHTML

❌ **Never use innerHTML:**
```typescript
// VULNERABLE!
element.innerHTML = userInput;
```

✅ **Use textContent or React:**
```typescript
element.textContent = userInput;  // Safe
// Or just use React JSX (auto-escaped)
```

### 2. eval / Function constructor

❌ **Never use eval:**
```typescript
// VULNERABLE!
eval(userInput);
new Function(userInput)();
```

### 3. postMessage

✅ **Validate origin:**
```typescript
window.addEventListener('message', (event) => {
  // Check origin
  if (event.origin !== 'https://trusted-domain.com') {
    return;
  }

  // Validate data structure
  if (typeof event.data.action !== 'string') {
    return;
  }

  // Safe to process
  handleMessage(event.data);
});
```

## Security Checklist

Before deploying:

- [ ] No `dangerouslySetInnerHTML` (or sanitized if required)
- [ ] No `eval` or `Function` constructor
- [ ] URLs validated before use in href/src
- [ ] API responses validated (Zod schemas)
- [ ] No sensitive data in localStorage
- [ ] CSP headers configured
- [ ] `npm audit` run and vulnerabilities fixed
- [ ] No secrets in client code
- [ ] HTTPS enforced in production

## CI Security Scanning

Cookie's CI runs:
- **ESLint security plugin** - Detects common React vulnerabilities
- **npm audit** - Dependency vulnerability scanner

See `.github/workflows/ci.yml` and `eslint.config.js`.

## References

- React Security: https://react.dev/learn/security
- OWASP React Security: https://cheatsheetseries.owasp.org/cheatsheets/ReactJS_Security_Cheat_Sheet.html
- CSP Guide: https://content-security-policy.com/
- DOMPurify: https://github.com/cure53/DOMPurify
