# Cookie Architecture

This document describes the system architecture, data models, and API structure.

## System Overview

```
                    ┌──────────────────────────────────────────────────────────────────────┐
                    │                       Production Container                           │
                    │                                                                      │
                    │  ┌─────────────────────────────────────────────────────────────────┐ │
                    │  │                         nginx (port 80)                         │ │
                    │  │                                                                 │ │
                    │  │  /api/, /admin/, /legacy/  ───►  gunicorn (127.0.0.1:8000)      │ │
                    │  │  /static/                  ───►  /app/staticfiles/              │ │
                    │  │  /media/                   ───►  /app/data/media/               │ │
                    │  │  /                         ───►  React SPA (/app/frontend/dist/)│ │
                    │  │                                                                 │ │
                    │  │  Browser Detection: iOS <11, IE, Edge Legacy ───► /legacy/      │ │
                    │  └─────────────────────────────────────────────────────────────────┘ │
                    │                              │                                       │
                    │                              ▼                                       │
                    │  ┌─────────────┐    ┌─────────────┐                                  │
                    │  │   Gunicorn  │───▶│   Django    │                                  │
                    │  │  (2 workers │    │  (Python    │                                  │
                    │  │  4 threads) │    │   3.14)     │                                  │
                    │  └─────────────┘    └─────────────┘                                  │
                    │                                                                      │
                    └──────────────────────────────────────────────────────────────────────┘
                             │
                             ▼ Port 80
                          Internet / LAN

                    ┌──────────────────┐
                    │   PostgreSQL     │  (db container)
                    └──────────────────┘
                             │
                             ▼ (optional)
                    ┌──────────────────┐
                    │   OpenRouter AI  │
                    └──────────────────┘
```

## Directory Structure

```
cookie/
├── apps/                    # Django applications
│   ├── ai/                  # AI/OpenRouter integration
│   │   ├── api.py           # AI API endpoints
│   │   ├── models.py        # AIPrompt, AIDiscoverySuggestion
│   │   └── services/        # AI service implementations
│   ├── core/                # App settings, auth, system endpoints
│   │   ├── api.py           # System health, reset endpoints
│   │   ├── auth.py          # SessionAuth (home/passkey mode-aware)
│   │   ├── passkey_api.py   # WebAuthn registration and login
│   │   ├── device_code_api.py # Device code pairing for legacy devices
│   │   └── models.py        # AppSettings, WebAuthnCredential, DeviceCode
│   ├── legacy/              # ES5 frontend for old browsers
│   │   ├── views.py         # Django template views
│   │   ├── templates/       # HTML templates
│   │   └── static/          # ES5 JavaScript and CSS
│   ├── profiles/            # User profiles
│   │   ├── api.py           # Profile CRUD endpoints
│   │   └── models.py        # Profile model
│   └── recipes/             # Recipe management
│       ├── api.py           # Recipe endpoints
│       ├── api_user.py      # Favorites, collections, history
│       ├── sources_api.py   # Search source management
│       ├── models.py        # Recipe, SearchSource, etc.
│       └── services/        # Scraping, caching services
├── cookie/                  # Django project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing (Django Ninja API)
│   └── wsgi.py              # WSGI entry point
├── frontend/                # React SPA
│   └── src/
│       ├── api/             # API client
│       ├── screens/         # Page components
│       ├── components/      # Reusable UI components
│       ├── contexts/        # React Context (AI status)
│       ├── hooks/           # Custom hooks (timers, wake lock)
│       ├── lib/             # Utilities
│       └── styles/          # CSS and themes
├── nginx/                   # nginx configurations
│   ├── nginx.conf           # Development config
│   └── nginx.prod.conf      # Production config (browser detection)
├── bin/                     # Helper scripts
│   ├── dev                  # Development commands
│   └── prod                 # Production commands
├── docker-compose.yml       # Development stack
├── docker-compose.prod.yml  # Production container
└── Dockerfile.prod          # Production image
```

## Data Models

### Profile (Hub)

All user data is scoped to a Profile. Deleting a profile cascades to all associated data.

```
Profile
├── name: str
├── avatar_color: str (hex)
├── theme: light | dark
├── unit_preference: metric | imperial
└── timestamps: created_at, updated_at
```

### Recipe

Core model for imported recipes.

```
Recipe
├── Source: source_url, canonical_url, host, site_name
├── Content: title, author, description, image, image_url
├── Ingredients: ingredients (JSON), ingredient_groups (JSON)
├── Instructions: instructions (JSON), instructions_text
├── Timing: prep_time, cook_time, total_time (minutes)
├── Servings: yields, servings
├── Categorization: category, cuisine, cooking_method, keywords
├── Nutrition: nutrition (JSON), rating, rating_count
├── AI: ai_tips (JSON)
├── Remix: is_remix (bool), remix_profile (FK)
└── Timestamps: scraped_at, updated_at
```

### User Data Models

```
RecipeFavorite
├── profile (FK → Profile)
├── recipe (FK → Recipe)
└── created_at
    Constraint: unique(profile, recipe)

RecipeCollection
├── profile (FK → Profile)
├── name: str
├── description: str (optional)
└── timestamps

RecipeCollectionItem
├── collection (FK → RecipeCollection)
├── recipe (FK → Recipe)
├── order: int
└── added_at

RecipeViewHistory
├── profile (FK → Profile)
├── recipe (FK → Recipe)
└── viewed_at

ServingAdjustment (cached AI results)
├── recipe (FK → Recipe)
├── profile (FK → Profile)
├── target_servings: int
├── unit_system: metric | imperial
├── ingredients, instructions, notes (JSON)
└── adjusted times (optional)
```

### Search and AI Models

```
SearchSource
├── host (unique): str
├── name: str
├── is_enabled: bool
├── search_url_template: str
├── result_selector: str
├── logo_url: str
└── Maintenance: last_validated_at, consecutive_failures, needs_attention

AIPrompt
├── prompt_type (unique): 11 types
├── name, description: str
├── system_prompt: str
├── user_prompt_template: str
├── model: str (10 available models)
└── is_active: bool

AIDiscoverySuggestion
├── profile (FK → Profile)
├── suggestion_type: favorites | seasonal | new
├── search_query, title, description: str
└── created_at

AppSettings (singleton)
├── openrouter_api_key: str (Fernet encrypted)
└── default_ai_model: str

WebAuthnCredential (passkey mode)
├── user (FK → User)
├── credential_id: binary
├── public_key: binary
├── sign_count: int
├── transports: JSON
└── timestamps: created_at, last_used_at

DeviceCode (passkey mode)
├── code: str (6 chars)
├── session_key: str
├── status: pending | authorized | expired | invalidated
├── authorized_user (FK → User, nullable)
├── attempts: int
└── timestamps: created_at, expires_at
```

## Relationship Map

```
Profile (center hub)
├── Recipe.profile ──────────────► User's imported recipes
├── Recipe.remix_profile ────────► User's AI-remixed recipes
├── RecipeFavorite.profile ──────► User's favorites
├── RecipeCollection.profile ────► User's collections
├── RecipeViewHistory.profile ───► Recently viewed
├── ServingAdjustment.profile ───► Cached scaling results
└── AIDiscoverySuggestion.profile → Discovery cache

Recipe
├── RecipeFavorite.recipe ───────► Favorited by users
├── ServingAdjustment.recipe ────► Cached scaling per recipe
└── RecipeCollectionItem.recipe ─► In collections

RecipeCollection
└── RecipeCollectionItem.collection → Recipes in collection
```

## API Structure

All API endpoints use Django Ninja and are prefixed with `/api/`.

### System (`/api/system/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mode/` | Current auth mode |
| GET | `/health/` | Container health check |
| GET | `/ready/` | Readiness check |
| GET | `/reset-preview/` | Preview reset data |
| POST | `/reset/` | Database reset (requires confirmation) |

### Auth (`/api/auth/`, passkey mode)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/options/` | WebAuthn registration options |
| POST | `/register/verify/` | Complete registration |
| POST | `/login/options/` | WebAuthn login options |
| POST | `/login/verify/` | Complete login |
| POST | `/logout/` | End session |
| GET | `/me/` | Current user info |

### Device Code (`/api/device/`, passkey mode)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/code/` | Generate pairing code |
| POST | `/poll/` | Poll for authorization |
| POST | `/authorize/` | Authorize a device code |

### Profiles (`/api/profiles/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all profiles |
| POST | `/` | Create profile |
| GET | `/{id}/` | Get profile |
| PUT | `/{id}/` | Update profile |
| GET | `/{id}/deletion-preview/` | Preview what deleting this profile would remove |
| DELETE | `/{id}/` | Delete profile and all data |
| POST | `/{id}/select/` | Set current profile |

### Recipes (`/api/recipes/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List saved recipes (paginated) |
| POST | `/scrape/` | Import recipe from URL |
| GET | `/search/` | Search across sites |
| GET | `/cache/health/` | Cache statistics |
| GET | `/{id}/` | Get recipe |
| DELETE | `/{id}/` | Delete recipe |

### Favorites (`/api/favorites/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List favorites |
| POST | `/` | Add to favorites |
| DELETE | `/{recipe_id}/` | Remove from favorites |

### Collections (`/api/collections/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List collections |
| POST | `/` | Create collection |
| GET | `/{id}/` | Get collection with recipes |
| PUT | `/{id}/` | Update collection |
| DELETE | `/{id}/` | Delete collection |
| POST | `/{id}/recipes/` | Add recipe to collection |
| DELETE | `/{id}/recipes/{recipe_id}/` | Remove recipe |

### History (`/api/history/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Recent views |
| POST | `/` | Record view |
| DELETE | `/` | Clear history |

### Search Sources (`/api/sources/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all sources |
| GET | `/enabled-count/` | Count of enabled sources |
| GET | `/{id}/` | Get single source |
| POST | `/{id}/toggle/` | Toggle source enabled/disabled |
| POST | `/bulk-toggle/` | Enable/disable all sources |
| PUT | `/{id}/selector/` | Update CSS selector for a source |
| POST | `/{id}/test/` | Test source scraping |
| POST | `/test-all/` | Test all sources |

### AI (`/api/ai/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | AI availability check |
| POST | `/test-api-key` | Validate API key |
| POST | `/save-api-key` | Store API key |
| GET | `/models` | List available models |
| GET | `/prompts` | List all prompts |
| GET | `/prompts/{type}` | Get specific prompt |
| PUT | `/prompts/{type}` | Update prompt |
| POST | `/remix-suggestions` | Get remix ideas |
| POST | `/remix` | Create remixed recipe |
| POST | `/scale` | Scale servings |
| POST | `/tips` | Generate cooking tips |
| POST | `/timer-name` | Name a timer |
| POST | `/repair-selector` | Fix broken CSS selector with AI |
| GET | `/sources-needing-attention` | List sources with broken selectors |
| GET | `/discover/{profile_id}/` | Discovery suggestions |

## Frontend Architecture

```
React SPA (TypeScript)
├── Screens (pages)
│   ├── Home - Dashboard with recent recipes and discover
│   ├── Search - Multi-site recipe search
│   ├── RecipeDetail - Recipe view with actions
│   ├── PlayMode - Step-by-step cooking mode
│   ├── AllRecipes - Browse all saved recipes
│   ├── Favorites - Favorite recipes
│   ├── Collections - Manage collections
│   ├── CollectionDetail - View collection recipes
│   ├── Settings - Configuration and AI setup
│   └── ProfileSelector - Profile selection
├── Components
│   ├── RecipeCard - Recipe preview cards
│   ├── TimerPanel - Cooking timers
│   ├── RemixModal - AI remix interface
│   └── Skeletons - Loading placeholders
├── Contexts
│   ├── ProfileContext - User profile, favorites, theme
│   └── AIStatusContext - AI availability state
├── Hooks
│   ├── useTimers - Timer management
│   ├── useRecipeDetail - Recipe page logic
│   └── useWakeLock - Screen wake lock
└── API Client
    └── Centralized backend communication
```

## Data Flow

```
User Action
    │
    ▼
React Screen
    │
    ├─► API Client (fetch)
    │       │
    │       ▼
    │   nginx (/api/*) ──► gunicorn ──► Django Ninja
    │                                       │
    │                                       ▼
    │                               PostgreSQL
    │                                       │
    │       ◄───────────────────────────────┘
    │       JSON response
    │
    ▼
Update React State / Context
    │
    ▼
Re-render UI
```

## Legacy Browser Support

Django middleware detects legacy browsers via User-Agent and redirects to `/legacy/`:
- iOS < 11 (Safari)
- Internet Explorer (all versions)
- Edge Legacy (EdgeHTML)
- Chrome < 60, Firefox < 55

The legacy frontend uses:
- ES5 JavaScript (no transpilation needed)
- Django templates (server-rendered)
- Vanilla CSS (no build step)
- Tested on iPad 3 (iOS 9.3.6)
