# Cookie 2 - Complete Rewrite Planning Document

> **Created:** 2026-01-06
> **Purpose:** Comprehensive planning document for Cookie 2 - a from-scratch rewrite of the Cookie Recipe App
> **Figma Source:** `/home/matt/cookie2/Cookie Recipe App Design`
> **Cookie 1 Reference:** `/home/matt/cookie` (for research only - no code to be copied)
> **Library References:** (for documentation/understanding only - install from PyPI)
> - recipe-scrapers: `/home/matt/recipe-scrapers` → `pip install recipe-scrapers`
> - curl_cffi: `/home/matt/curl_cffi` → `pip install curl_cffi`

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Requirements Summary](#2-requirements-summary)
3. [Tech Stack](#3-tech-stack)
4. [Figma Design Analysis](#4-figma-design-analysis)
5. [Database Schema](#5-database-schema)
6. [API Design](#6-api-design)
7. [Dual Interface Architecture](#7-dual-interface-architecture)
8. [AI Integration](#8-ai-integration)
9. [Recipe Scraping & Search](#9-recipe-scraping--search)
10. [Search Sources Configuration](#10-search-sources-configuration)
11. [Serving Adjustment Architecture](#11-serving-adjustment-architecture)
12. [Play Mode Features](#12-play-mode-features)
13. [Build Order](#13-build-order)
14. [Design Maintenance Workflow](#14-design-maintenance-workflow)
15. [Cookie 1 Lessons Learned](#15-cookie-1-lessons-learned)
16. [AI Development Tooling](#16-ai-development-tooling)
17. [Error Handling Strategy](#17-error-handling-strategy)
18. [Background Task Architecture](#18-background-task-architecture)
19. [API Architecture Notes](#19-api-architecture-notes)

---

## 1. Project Overview

Cookie 2 is a recipe management application that allows users to:
- Search and import recipes from across the web
- Organize recipes into favorites and collections
- Use AI to remix, scale, and get tips for recipes
- Cook with step-by-step play mode with smart timers
- Support multiple user profiles (passwordless, kitchen-friendly)

### Key Principles

1. **Figma designs are the master** - All features and UI must match the Figma export
2. **From-scratch rewrite** - No code from Cookie 1, only lessons learned
3. **Dual interface** - Modern browsers get React SPA, iOS 9 iPads get simplified UI
4. **Real data only** - No mock data; real scraping, real AI integration
5. **Single environment** - One Docker environment for development with production-grade tools
6. **Full recipe-scrapers support** - Database schema supports all fields from the library
7. **15 curated search sources** - Most popular recipe sites with implemented search

---

## 2. Requirements Summary

### Features to Implement (from Figma + requirements)

| Feature | Description |
|---------|-------------|
| **Profile System** | Passwordless "Who's cooking?" selector with avatars and colors |
| **Home Screen** | Search bar + "My Favorites" / "Discover" toggle |
| **Discover (AI)** | AI generates search terms daily based on favorites, today's date/holidays, "try something new" |
| **Recipe Search** | Multi-site web search (15 sources), AI-ranked by relevance, source filters |
| **Recipe Import** | Scrape recipes from URLs, save full data including images locally to DB |
| **Recipe Detail** | Hero image, metadata, tabs (Ingredients, Instructions, Nutrition, Tips) |
| **Serving Adjustment** | AI-only scaling (hidden when no API key), not persisted |
| **Recipe Remix** | AI creates new recipe variations with AI-generated suggestions, saved as **separate recipes** (no parent link tracked) |
| **Favorites** | Per-profile heart toggle, favorites list screen |
| **Collections** | Named recipe collections per profile |
| **Play Mode** | Step-by-step cooking with smart timers, AI timer naming, auto-detected timer suggestions |
| **Timers** | Multiple browser-based timers with AI-generated labels, audio alerts |
| **Settings - General** | Theme toggle (React only), profile management, data management, API key |
| **Settings - AI Prompts** | Editable prompts for all 10 AI features, model selection per prompt |
| **Settings - Sources** | Enable/disable recipe search sources (15 available) |
| **Dark/Light Mode** | Per-profile theme preference (React only; legacy is light-only) |

### Removed from Cookie 1

- **PlaySession model** - Play mode is now stateless, browser-only
- **RecipeStep model** - Instructions stored as JSON array (recipe-scrapers format)
- **Image proxy** - Images downloaded and stored locally at scrape time
- **RecipeEnhancement for scaling** - Serving adjustment is computed on-the-fly, not persisted

### Added New

- **Full OpenRouter integration** with configurable model selection
- **AI Recipe Remix** - Creates new recipes with AI-generated variation suggestions
- **Discover AI suggestions** - AI generates search terms; results shown from running those searches
- **AI Prompts settings tab** - Edit all 10 prompts without code changes
- **15 curated search sources** - Most popular recipe sites with on/off toggles
- **Image storage** - Scrape and store images locally, no proxy needed
- **Single environment** - Dev environment with hot reload using production-grade nginx
- **Async scraping** - Parallel requests with curl_cffi AsyncSession for faster search
- **AI Timer Naming** - AI generates descriptive labels for timers based on step content
- **Smart Timer Suggestions** - Auto-detect time mentions in instructions and suggest timers
- **AI Remix Suggestions** - AI generates contextual variation prompts per recipe

---

## 3. Tech Stack

### Backend

| Component | Technology |
|-----------|------------|
| Framework | Django 5.x |
| Language | Python 3.12+ |
| Database | SQLite |
| Server | Gunicorn (with auto-reload in dev) |
| Reverse Proxy | nginx |
| Containerization | Docker + Docker Compose (single environment) |

### Modern Frontend (React)

| Component | Technology |
|-----------|------------|
| Framework | React 18.3 |
| Language | TypeScript |
| Build Tool | Vite 6.x |
| Styling | Tailwind CSS v4.1.x (stable, released Jan 22, 2025) |
| Tailwind Plugin | @tailwindcss/vite 4.1.x |
| UI Primitives | Radix UI |
| Icons | Lucide React |
| Notifications | Sonner |
| Animations | Motion (framer-motion successor) |
| State | React useState/useEffect (local) |

### Legacy Frontend (iOS 9)

| Component | Technology |
|-----------|------------|
| Language | Vanilla ES5 JavaScript |
| Styling | CSS3 (flexbox, -webkit prefixes) - **Light theme only** |
| Templates | Django templates |
| AJAX | XMLHttpRequest |
| Philosophy | **Function over form** - full user journey, simplified layout |

### AI & Scraping

| Component | Technology |
|-----------|------------|
| AI API | OpenRouter (configurable models) |
| Default Model | anthropic/claude-3.5-haiku |
| Recipe Scraping | recipe-scrapers library (575+ hosts supported) |
| HTTP Client | curl_cffi with AsyncSession (browser fingerprint spoofing) |
| Browser Profiles | chrome136, safari184, safari184_ios, firefox133 (use `chrome`, `safari`, `firefox` aliases for latest) |

---

## 4. Figma Design Analysis

### Screens Defined in Figma

#### 1. Profile Selector (`type: 'profile-selector'`)
- Large "Cookie" title in primary green
- "Who's cooking today?" subtitle
- Circular avatar buttons with profile colors
- Add profile button (dashed circle with +)
- Create profile form: name input, color picker (10 colors), create button

#### 2. Home Screen (`type: 'home'`)
- **Header** (left to right):
  - Burger menu icon (opens sidebar)
  - "Cookie" app title
  - Dark mode toggle (Sun/Moon icons)
  - Profile avatar (click to switch profiles)
- **Sidebar Navigation** (opens from burger menu):
  - "Cookie" branding + close button
  - Home (HomeIcon)
  - Favorites (Heart)
  - Collections (BookOpen)
  - Settings (SettingsIcon)
  - Slides in from left with animation, overlay backdrop
- Search bar: "Search recipes or paste a URL..."
- Toggle: "My Favorites" | "Discover"
- **Favorites view:**
  - Recently Viewed section (up to 6 recipes)
  - My Favorite Recipes grid
  - Empty state with "Discover Recipes" CTA
- **Discover view:**
  - "Discover New Recipes" heading
  - "AI-suggested recipes based on your preferences" subtitle
  - **Mixed feed** - combines results from all 3 AI search types:
    - Recipes similar to user's favorites
    - Recipes opposite/new to expand their horizons
    - Seasonal/holiday-relevant recipes for current date (worldwide holidays)
  - **Daily refresh** - new suggestions each day
  - Results displayed as unified grid (not categorized sections)
  - **New user behavior**: When user has no favorites/history, show only seasonal/holiday suggestions based on current date and famous holidays from around the world

#### 3. Search Results (`type: 'search', query: string`)
- Breadcrumb navigation
- Results count with query
- Source filter chips (All Sources, per-site filters with counts)
- Recipe grid
- Load more button with progress indicator (6 results per page)
- "End of results" indicator
- URL detection → "Import Recipe" card

#### 4. Recipe Detail (`type: 'recipe-detail'`)
- Hero image with gradient overlay
- Title and rating overlay (top-left)
- Action buttons (bottom-right): Favorite, Add to Collection, Remix, Cook!
- **Add to Collection dropdown** (appears on button click):
  - List of existing collections (click to add recipe)
  - Divider line
  - "Create New Collection" option (navigates to Collections screen, auto-adds recipe after creation)
- Collapsible meta info (collapsed by default on mobile): Prep time, Cook time, Servings adjuster, Unit toggle (Metric/Imperial)
- Tabs: Ingredients | Instructions | Nutrition | Cooking Tips
- Numbered lists for ingredients and instructions
- **Nutrition tab**: Shows scraped nutrition data with "per X servings" label
- **Cooking Tips tab**: AI-generated tips displayed as numbered list

#### 5. Play Mode (`type: 'play-mode'`)
- Full-screen cooking interface
- Progress bar at top showing step progress
- Step counter (Step X of Y)
- Current instruction in large text
- Previous/Next navigation buttons
- Exit button (X)
- **Quick Timer Actions**: +5min, +10min, +15min buttons
- **Smart Timer Suggestions**: Auto-detected from instruction text (e.g., "bake for 15 minutes")
- **AI Timer Labels**: Descriptive names generated from step content
- Timer panel with multiple simultaneous timers
- Timer controls: play/pause, reset, delete
- Completion notification via toast

#### 6. Favorites (`type: 'favorites'`)
- "Favorites" heading
- Recipe grid
- Empty state

#### 7. Collections (`type: 'collections'`)
- "Collections" heading
- Create Collection button (shows inline form)
- Collection cards with cover images and recipe counts
- Empty state

#### 8. Collection Detail (`type: 'collection-detail'`)
- Collection name and recipe count
- Delete Collection button with confirmation
- Recipe grid with remove buttons
- Empty state

#### 9. Settings (`type: 'settings'`)
- Four tabs: General | AI Prompts | Sources | Source Selectors

**General Tab:**
- Appearance: Dark/light toggle
- Profile Management: List profiles, delete option, "Current" badge
- Data Management: Clear Cache, Clear View History buttons
- OpenRouter API Key: Password input
- About: Version number, GitHub link (https://github.com/matthewdeaves/cookie.git)

**AI Prompts Tab:**
- Section header explaining prompts
- Ten prompt cards (all editable):
  1. Recipe Remix
  2. Serving Adjustment
  3. Tips Generation
  4. Discover from Favorites
  5. Discover Seasonal/Holiday
  6. Discover Try Something New
  7. Search Result Ranking
  8. Timer Naming
  9. Remix Suggestions
  10. CSS Selector Repair
- Each card shows:
  - Title and description
  - Edit button
  - Current prompt (read-only view)
  - Current model badge
- Edit mode:
  - Textarea for prompt
  - Model dropdown (8 models available)
  - Save/Cancel buttons

**Sources Tab:**
- "Recipe Sources" heading
- "X of 15 sources currently enabled" counter
- Enable All / Disable All bulk actions
- List of 15 sources with:
  - Source name and URL
  - "Active" badge when enabled
  - Toggle switch

**Source Selectors Tab:**
- "Search Source Selector Management" heading
- "Edit CSS selectors and test source connectivity" subheading
- For each of the 15 sources, a card showing:
  - Source name and host URL
  - Status indicator: green checkmark (working), red X (broken), gray ? (untested)
  - Editable "CSS Selector" text field (monospace font)
  - "Test" button (primary color)
  - "Last tested: [relative time]" in muted text
  - Warning badge if broken: "Failed X times - auto-disabled" (red)
- "Test All Sources" button at bottom

### Components from Figma Export

```
src/app/components/
├── Header.tsx              # App header with menu, title, dark mode, profile
├── RecipeCard.tsx          # Recipe card with image, title, time, rating, favorite, play
├── BreadcrumbNav.tsx       # Navigation breadcrumbs
├── ProfileAvatar.tsx       # Circular avatar with initials and color
├── EmptyState.tsx          # Empty state with icon, title, description, action
├── TimerWidget.tsx         # Individual timer with play/pause/reset/delete
├── AIRemixModal.tsx        # Modal for AI recipe remix with suggestions
└── ui/                     # Radix UI primitives (button, dialog, tabs, etc.)
```

### Color Palette (from theme.css)

**Light Mode:**
```css
--background: #faf9f7;       /* Warm off-white */
--foreground: #2d2520;       /* Dark brown */
--primary: #6b8e5f;          /* Sage green */
--secondary: #f4ede6;        /* Light cream */
--accent: #a84f5f;           /* Muted red/pink */
--muted: #e8e1d8;            /* Light tan */
--destructive: #c94545;      /* Red */
--star: #d97850;             /* Orange (for ratings) */
```

**Dark Mode (React only):**
```css
--background: #2a2220;       /* Dark brown */
--foreground: #f5ebe0;       /* Light cream */
--primary: #8aa879;          /* Lighter sage green */
--secondary: #3d3531;        /* Dark brown */
--accent: #c66d7a;           /* Lighter pink */
```

**Profile Colors:**
```javascript
['#d97850', '#8fae6f', '#c9956b', '#6b9dad', '#d16b6b',
 '#9d80b8', '#e6a05f', '#6bb8a5', '#c77a9e', '#7d9e6f']
```

---

## 5. Database Schema

### Core Models

```python
# core/models.py
class AppSettings(models.Model):
    """Singleton for app-wide configuration"""
    openrouter_api_key = models.CharField(max_length=500, blank=True)
    default_ai_model = models.CharField(max_length=100, default='anthropic/claude-3.5-haiku')

    class Meta:
        verbose_name_plural = "App Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)
```

### Profile Models

```python
# profiles/models.py
class Profile(models.Model):
    """Passwordless user profile - sessions last 12 hours"""
    name = models.CharField(max_length=100)
    avatar_color = models.CharField(max_length=7)  # Hex color
    theme = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    unit_preference = models.CharField(
        max_length=10,
        choices=[('metric', 'Metric'), ('imperial', 'Imperial')],
        default='metric'
    )  # Applied to all recipe views; uses AI or code conversion
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Recipe Models

The Recipe model supports **all fields from recipe-scrapers library**:

```python
# recipes/models.py
class Recipe(models.Model):
    """
    Scraped recipe data - supports full recipe-scrapers data model.
    See: https://github.com/hhursev/recipe-scrapers
    """
    # Source information (remixed recipes share source_url with original for cascade delete)
    source_url = models.URLField(max_length=2000, null=True, blank=True, db_index=True)
    canonical_url = models.URLField(max_length=2000, blank=True)
    host = models.CharField(max_length=255)  # e.g., "allrecipes.com"
    site_name = models.CharField(max_length=255, blank=True)  # e.g., "AllRecipes"

    # Core content
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Images (stored locally)
    image = models.ImageField(upload_to='recipe_images/', blank=True)
    image_url = models.URLField(max_length=2000, blank=True)  # Original URL for reference

    # Ingredients - supports both flat list and grouped formats
    ingredients = models.JSONField(default=list)  # ["2 cups flour", "1 tsp salt", ...]
    ingredient_groups = models.JSONField(default=list)  # [{"purpose": "For the dough", "ingredients": [...]}, ...]

    # Instructions - list of steps
    instructions = models.JSONField(default=list)  # ["Preheat oven...", "Mix flour...", ...]
    instructions_text = models.TextField(blank=True)  # Single string version if needed

    # Timing (stored in minutes)
    prep_time = models.PositiveIntegerField(null=True, blank=True)
    cook_time = models.PositiveIntegerField(null=True, blank=True)
    total_time = models.PositiveIntegerField(null=True, blank=True)

    # Servings/Yield
    yields = models.CharField(max_length=100, blank=True)  # "24 cookies", "4 servings"
    servings = models.PositiveIntegerField(null=True, blank=True)  # Parsed numeric value

    # Categorization
    category = models.CharField(max_length=100, blank=True)  # "Dessert", "Main Course"
    cuisine = models.CharField(max_length=100, blank=True)  # "Italian", "Mexican"
    cooking_method = models.CharField(max_length=100, blank=True)  # "Baking", "Grilling"
    keywords = models.JSONField(default=list)  # ["easy", "quick", "vegetarian"]
    dietary_restrictions = models.JSONField(default=list)  # ["vegan", "gluten-free"]

    # Equipment and extras
    equipment = models.JSONField(default=list)  # ["stand mixer", "baking sheet"]

    # Nutrition (scraped from source, displayed "per X servings")
    nutrition = models.JSONField(default=dict)  # {"calories": "250", "fat": "12g", ...}

    # Ratings (from source site)
    rating = models.FloatField(null=True, blank=True)  # 0-5 scale
    rating_count = models.PositiveIntegerField(null=True, blank=True)

    # Language
    language = models.CharField(max_length=10, blank=True)  # ISO code, e.g., "en"

    # Links (related recipes, etc.)
    links = models.JSONField(default=list)

    # AI-generated content (cached)
    ai_tips = models.JSONField(default=list, blank=True)

    # Remix tracking - remixes are independent recipes (no cascade delete)
    is_remix = models.BooleanField(default=False)
    remix_profile = models.ForeignKey(
        'profiles.Profile', on_delete=models.CASCADE, null=True, blank=True,
        related_name='remixes'
    )  # Only set for remixes; null for scraped recipes
    # For remixed recipes:
    # - source_url = null (independent, no cascade)
    # - host = "user-generated"
    # - site_name = "User Generated"
    # - remix_profile = the profile that created the remix
    # - Remixes are ONLY visible to the creating profile
    # - Remixes persist even if original recipe is deleted
    # Frontend displays "User Generated" badge instead of source site name

    # Timestamps
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['host']),
            models.Index(fields=['is_remix']),
            models.Index(fields=['scraped_at']),
        ]

    @property
    def has_ingredient_groups(self) -> bool:
        return bool(self.ingredient_groups)

    @property
    def step_count(self) -> int:
        return len(self.instructions)


class RecipeFavorite(models.Model):
    """Profile's favorite recipes"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['profile', 'recipe']
        ordering = ['-created_at']


class RecipeViewHistory(models.Model):
    """Track recipe views per profile"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='view_history')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['profile', 'recipe']
        ordering = ['-viewed_at']
```

### Collection Models

```python
# collections/models.py
class RecipeCollection(models.Model):
    """Named recipe collections"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['profile', 'name']
        ordering = ['-updated_at']


class RecipeCollectionItem(models.Model):
    """Recipes in a collection"""
    collection = models.ForeignKey(RecipeCollection, on_delete=models.CASCADE, related_name='items')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['collection', 'recipe']
        ordering = ['order', '-added_at']
```

### AI Models

```python
# ai/models.py
class AIPrompt(models.Model):
    """Configurable AI prompts - all 10 editable via Settings"""
    PROMPT_TYPES = [
        ('recipe_remix', 'Recipe Remix'),
        ('serving_adjustment', 'Serving Adjustment'),
        ('tips_generation', 'Tips Generation'),
        ('discover_favorites', 'Discover from Favorites'),
        ('discover_seasonal', 'Discover Seasonal/Holiday'),
        ('discover_new', 'Discover Try Something New'),
        ('search_ranking', 'Search Result Ranking'),
        ('timer_naming', 'Timer Naming'),
        ('remix_suggestions', 'Remix Suggestions'),
        ('selector_repair', 'CSS Selector Repair'),
    ]

    prompt_type = models.CharField(max_length=50, choices=PROMPT_TYPES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()  # Supports {placeholders}
    model = models.CharField(max_length=100, default='anthropic/claude-3.5-haiku')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AIDiscoverySuggestion(models.Model):
    """Cached AI discovery suggestions - refreshed daily"""
    SUGGESTION_TYPES = [
        ('favorites_based', 'Based on Favorites'),
        ('seasonal', 'Seasonal/Holiday'),
        ('try_new', 'Try Something New'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='ai_suggestions')
    suggestion_type = models.CharField(max_length=20, choices=SUGGESTION_TYPES)
    search_query = models.CharField(max_length=255)  # AI-generated search term
    title = models.CharField(max_length=200)  # Display title for the suggestion
    description = models.TextField()  # Why this was suggested
    context_data = models.JSONField(default=dict)  # Holiday info, etc.
    generated_date = models.DateField()  # Date this was generated (for daily refresh)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['profile', 'generated_date']),
        ]


class AIEnhancement(models.Model):
    """Cached AI enhancements for recipes (tips only - scaling is not persisted)"""
    ENHANCEMENT_TYPES = [
        ('cooking_tips', 'Cooking Tips'),
    ]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ai_enhancements')
    enhancement_type = models.CharField(max_length=30, choices=ENHANCEMENT_TYPES)
    data = models.JSONField()
    ai_model = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['recipe', 'enhancement_type']),
        ]
```

### Search Source Models

```python
# recipes/models.py (additional)
class SearchSource(models.Model):
    """
    Recipe search sources - 15 curated popular sites.
    Each has a search URL template and result parsing logic.
    Supports maintenance tracking for selector validation.
    """
    host = models.CharField(max_length=255, unique=True)  # e.g., "allrecipes.com"
    name = models.CharField(max_length=255)  # e.g., "AllRecipes"
    is_enabled = models.BooleanField(default=True)
    search_url_template = models.CharField(max_length=500)  # e.g., "https://allrecipes.com/search?q={query}"
    result_selector = models.CharField(max_length=255)  # CSS selector for recipe links
    logo_url = models.URLField(blank=True)  # Optional site logo

    # Maintenance tracking
    last_validated_at = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    needs_attention = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    @classmethod
    def get_enabled_sources(cls):
        return cls.objects.filter(is_enabled=True)

    def mark_success(self):
        """Called when a search successfully returns results"""
        from django.utils import timezone
        self.last_validated_at = timezone.now()
        self.consecutive_failures = 0
        self.save(update_fields=['last_validated_at', 'consecutive_failures'])

    def mark_failure(self):
        """Called when a search fails - auto-disable after 3 failures"""
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.is_enabled = False
            self.needs_attention = True
        self.save(update_fields=['consecutive_failures', 'is_enabled', 'needs_attention'])
```

---

## 6. API Design

### REST API Endpoints

```
# Profiles
GET    /api/profiles/                     # List all profiles
POST   /api/profiles/                     # Create profile
GET    /api/profiles/{id}/                # Get profile
PUT    /api/profiles/{id}/                # Update profile
DELETE /api/profiles/{id}/                # Delete profile
POST   /api/profiles/{id}/select/         # Set as current profile (session)

# Recipes
GET    /api/recipes/                      # List saved recipes (with filters)
POST   /api/recipes/scrape/               # Scrape recipe from URL → save with images
GET    /api/recipes/{id}/                 # Get recipe detail
DELETE /api/recipes/{id}/                 # Delete recipe
GET    /api/recipes/search/               # Search web (async, returns results to import)

# Favorites (current profile)
GET    /api/favorites/                    # List favorites
POST   /api/favorites/                    # Add favorite {recipe_id}
DELETE /api/favorites/{recipe_id}/        # Remove favorite

# Collections (current profile)
GET    /api/collections/                  # List collections
POST   /api/collections/                  # Create collection
GET    /api/collections/{id}/             # Get collection with recipes
PUT    /api/collections/{id}/             # Update collection
DELETE /api/collections/{id}/             # Delete collection
POST   /api/collections/{id}/recipes/     # Add recipe {recipe_id}
DELETE /api/collections/{id}/recipes/{recipe_id}/  # Remove recipe

# View History (current profile)
GET    /api/history/                      # Get recent recipes
DELETE /api/history/                      # Clear history
POST   /api/history/                      # Record view {recipe_id}

# AI Features
POST   /api/ai/remix/                     # Create recipe remix → saves NEW recipe
POST   /api/ai/remix-suggestions/         # Get AI-generated remix prompts for a recipe
POST   /api/ai/scale/                     # Scale ingredients (computed, not persisted)
POST   /api/ai/tips/                      # Get cooking tips (cached in AIEnhancement)
POST   /api/ai/timer-name/                # Generate timer label from step text
GET    /api/ai/discover/                  # Get AI suggestions for Discover (daily refresh)

# Settings
GET    /api/settings/                     # Get app settings (includes ai_available flag)
PUT    /api/settings/                     # Update settings
GET    /api/settings/prompts/             # List all 10 AI prompts
PUT    /api/settings/prompts/{type}/      # Update specific prompt
POST   /api/settings/test-api-key/        # Test OpenRouter connection
GET    /api/settings/ai-status/           # Check if AI is available (API key configured)

# Search Sources
GET    /api/sources/                      # List all 15 sources with status and selectors
GET    /api/sources/test/{host}/          # Test a source's selector (returns success/failure)
POST   /api/sources/test-all/             # Test all sources (returns batch results)
PUT    /api/sources/{host}/               # Update source (enabled, css_selector)
POST   /api/sources/enable-all/           # Enable all sources
POST   /api/sources/disable-all/          # Disable all sources
POST   /api/sources/{host}/suggest-selector/  # AI suggests CSS selector for broken source
```

---

## 7. Dual Interface Architecture

### Request Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Incoming Request                             │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DeviceDetectionMiddleware                         │
│                                                                      │
│  User-Agent matching:                                               │
│  - iPad.*OS 9                                                       │
│  - iPad.*OS 10                                                      │
│  - Other legacy patterns                                            │
│                                                                      │
│  Sets: request.is_legacy_device = True/False                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
         ┌──────────────────┐          ┌──────────────────┐
         │ Modern Browser   │          │ Legacy Device    │
         │ (is_legacy=False)│          │ (is_legacy=True) │
         └────────┬─────────┘          └────────┬─────────┘
                  │                             │
                  ▼                             ▼
         ┌──────────────────┐          ┌──────────────────┐
         │ React SPA Shell  │          │ Django Templates │
         │ (index.html)     │          │ (legacy/*.html)  │
         │                  │          │                  │
         │ Vite-built       │          │ ES5 JavaScript   │
         │ React + TS       │          │ Light theme only │
         │ Dark/Light mode  │          │ Function > Form  │
         └────────┬─────────┘          └────────┬─────────┘
                  │                             │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │        Same REST API         │
                  │         /api/*               │
                  │                              │
                  │  JSON responses for both     │
                  └──────────────────────────────┘
```

### Directory Structure (Single Environment)

```
cookie2/
├── cookie2/                        # Django project config
│   ├── settings.py                 # Single settings file (no dev/prod split)
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── core/
│   │   ├── models.py               # AppSettings
│   │   ├── middleware.py           # DeviceDetection, Profile
│   │   ├── views.py                # Settings API, health checks
│   │   └── api.py                  # Settings REST endpoints
│   │
│   ├── profiles/
│   │   ├── models.py               # Profile
│   │   ├── views.py                # Profile management
│   │   └── api.py                  # Profile REST endpoints
│   │
│   ├── recipes/
│   │   ├── models.py               # Recipe, Favorite, ViewHistory, SearchSource
│   │   ├── views.py                # Recipe views
│   │   ├── api.py                  # Recipe REST endpoints
│   │   └── services/
│   │       ├── scraper.py          # Recipe scraping with curl_cffi (async)
│   │       ├── search.py           # Multi-site search (async, parallel)
│   │       └── image.py            # Image download and storage
│   │
│   ├── collections/
│   │   ├── models.py               # RecipeCollection, RecipeCollectionItem
│   │   ├── views.py
│   │   └── api.py
│   │
│   └── ai/
│       ├── models.py               # AIPrompt, AIEnhancement, AIDiscoverySuggestion
│       ├── views.py
│       ├── api.py
│       └── services/
│           ├── openrouter.py       # OpenRouter API client
│           ├── remix.py            # Recipe remix logic
│           ├── scaling.py          # Ingredient scaling (on-the-fly)
│           ├── discover.py         # AI discovery suggestions
│           ├── ranking.py          # Search result ranking
│           ├── timer.py            # Timer naming
│           └── suggestions.py      # Remix suggestions
│
├── frontend/                       # React/Vite project
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                 # Main app with routing
│   │   ├── api/
│   │   │   └── client.ts           # API client with fetch
│   │   ├── hooks/
│   │   │   ├── useProfile.ts
│   │   │   ├── useRecipes.ts
│   │   │   └── useAI.ts
│   │   ├── components/             # From Figma export
│   │   │   ├── Header.tsx
│   │   │   ├── RecipeCard.tsx
│   │   │   ├── ProfileAvatar.tsx
│   │   │   ├── BreadcrumbNav.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── TimerWidget.tsx
│   │   │   ├── AIRemixModal.tsx
│   │   │   └── ui/
│   │   ├── screens/
│   │   │   ├── ProfileSelector.tsx
│   │   │   ├── Home.tsx
│   │   │   ├── Search.tsx
│   │   │   ├── RecipeDetail.tsx
│   │   │   ├── PlayMode.tsx
│   │   │   ├── Favorites.tsx
│   │   │   ├── Collections.tsx
│   │   │   ├── CollectionDetail.tsx
│   │   │   └── Settings.tsx
│   │   └── styles/
│   │       ├── index.css
│   │       ├── theme.css
│   │       └── tailwind.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── legacy/                         # iOS 9 frontend (function over form)
│   ├── templates/
│   │   ├── legacy/
│   │   │   ├── base.html           # Base template - LIGHT THEME ONLY
│   │   │   ├── profile_selector.html
│   │   │   ├── home.html
│   │   │   ├── search.html
│   │   │   ├── recipe_detail.html
│   │   │   ├── play_mode.html
│   │   │   ├── favorites.html
│   │   │   ├── collections.html
│   │   │   ├── collection_detail.html
│   │   │   └── settings.html
│   │   └── legacy/partials/
│   │       ├── header.html
│   │       ├── recipe_card.html
│   │       └── timer.html
│   ├── static/
│   │   └── legacy/
│   │       ├── js/
│   │       │   ├── app.js          # Main bootstrap (ES5)
│   │       │   ├── ajax.js         # XHR wrapper
│   │       │   ├── state.js        # Page state management
│   │       │   ├── router.js       # AJAX navigation
│   │       │   ├── timer.js        # Timer functionality (REQUIRED)
│   │       │   ├── toast.js        # Notifications
│   │       │   └── pages/
│   │       │       ├── home.js
│   │       │       ├── detail.js
│   │       │       ├── play.js
│   │       │       └── settings.js
│   │       └── css/
│   │           ├── base.css        # Light theme only
│   │           ├── components.css
│   │           ├── layout.css
│   │           └── play-mode.css
│
├── static/                         # Collected static files
├── media/                          # User uploads (recipe images)
├── templates/                      # Root templates
│   └── modern/
│       └── index.html              # React SPA shell
│
├── bin/
│   └── dev                         # Simple helper script to rebuild/restart
│
├── docker-compose.yml              # Single file, single environment
├── Dockerfile
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 8. AI Integration

### AI Fallback Behavior (No API Key)

When the OpenRouter API key is not configured or an API call fails:

**Frontend Behavior:**
- **HIDE all AI-dependent features** from the user
- Hide buttons: Remix, AI Refine (serving adjustment)
- Hide options: Discover tab suggestions, Timer AI naming
- Hide settings: AI Prompts tab content (show "API key required" message)
- Do NOT show errors inline - simply don't render the AI features

**Backend Behavior:**
- API endpoints return appropriate error response:
  ```json
  {"error": "ai_unavailable", "message": "OpenRouter API key not configured"}
  ```
- HTTP status: 503 Service Unavailable
- Features that require AI should not be callable without key

**No Fallback Mode:**
- Serving Adjustment does NOT fall back to frontend-only math
- All AI features are hidden, not degraded
- This ensures consistent user experience

### OpenRouter Configuration

**Supported Models (via OpenRouter - updated Jan 2026):**
```python
AVAILABLE_MODELS = [
    # Anthropic Claude (latest)
    ('anthropic/claude-3.5-haiku', 'Claude 3.5 Haiku (Fast)'),
    ('anthropic/claude-sonnet-4', 'Claude Sonnet 4'),
    ('anthropic/claude-opus-4', 'Claude Opus 4'),
    ('anthropic/claude-opus-4.5', 'Claude Opus 4.5'),
    # OpenAI GPT (latest)
    ('openai/gpt-4o', 'GPT-4o'),
    ('openai/gpt-4o-mini', 'GPT-4o Mini (Fast)'),
    ('openai/gpt-5-mini', 'GPT-5 Mini'),
    ('openai/o3-mini', 'o3 Mini (Reasoning)'),
    # Google Gemini (latest)
    ('google/gemini-2.5-pro-preview', 'Gemini 2.5 Pro'),
    ('google/gemini-2.5-flash-preview', 'Gemini 2.5 Flash (Fast)'),
]
```

### Default AI Prompts (All 10 Editable in Settings)

**1. Recipe Remix (`recipe_remix`):**
```
System: You are a culinary expert helping to remix recipes. Given a recipe and a user's modification request, create a complete new recipe. Consider dietary restrictions, ingredient substitutions, and cooking methods. Be specific and practical.

User Template: Original recipe: {recipe_title}
Ingredients: {ingredients}
Instructions: {instructions}
User request: {user_prompt}

Please provide a complete remixed recipe with:
- New creative title
- Modified ingredients list
- Updated instructions
- Brief description of changes made

Return as JSON: {"title": "", "ingredients": [], "instructions": [], "description": ""}
```

**2. Serving Adjustment (`serving_adjustment`):**
```
System: You are a precise culinary calculator. Adjust ingredient quantities proportionally based on the new serving size. Maintain proper ratios for baking recipes. Consider that some ingredients like salt and spices don't scale linearly. Return scaled ingredients in the requested unit system.

User Template: Recipe: {recipe_title}
Original servings: {original_servings}
Target servings: {target_servings}
Original ingredients: {ingredients}
Unit system: {unit_system}

Return a JSON array of scaled ingredients with any notes about non-linear scaling.
```

**3. Tips Generation (`tips_generation`):**
```
System: You are an experienced chef providing cooking tips. Generate 3-5 practical, actionable tips for this recipe. Focus on technique improvements, ingredient quality, timing, common mistakes to avoid, and serving suggestions. Keep tips concise.

User Template: Recipe: {recipe_title}
Ingredients: {ingredients}
Instructions: {instructions}

Return as JSON array of tip strings.
```

**4. Discover from Favorites (`discover_favorites`):**
```
System: You are a culinary recommendation engine. Based on the user's favorite recipes, generate a SEARCH TERM (not a recipe) that would help them discover similar recipes they might enjoy. Consider flavor profiles, cuisines, and cooking styles.

User Template: User's favorite recipes:
{favorite_recipes_summary}

Return a JSON object: {"search_query": "2-5 word search term", "title": "Display title", "description": "Why this was suggested"}
```

**5. Discover Seasonal/Holiday (`discover_seasonal`):**
```
System: You are a culinary advisor aware of seasonal and holiday cooking traditions worldwide. Based on the current date, identify any relevant holidays or seasonal occasions from ANY country and generate a SEARCH TERM for appropriate recipes.

User Template: Current date: {date}

Return a JSON object: {"search_query": "2-5 word search term", "title": "Display title", "description": "Holiday/season context", "context_data": {"holiday": "", "country": ""}}
```

**6. Discover Try Something New (`discover_new`):**
```
System: You are an adventurous culinary guide. Based on the user's cooking history, generate a SEARCH TERM that would help them discover recipes outside their comfort zone while still being achievable.

User Template: User's recent recipes:
{recent_recipes_summary}
Cuisines they've made: {known_cuisines}

Return a JSON object: {"search_query": "2-5 word search term", "title": "Display title", "description": "Why try this"}
```

**7. Search Ranking (`search_ranking`):**
```
System: You are a recipe relevance ranker. Given a user's search query and a list of recipe results, rank them by relevance. Consider query intent, recipe quality indicators, and match accuracy.

User Template: Search query: {query}
Results:
{results_list}

Return the recipe indices in order of relevance as a JSON array of integers.
```

**8. Timer Naming (`timer_naming`):**
```
System: You are a helpful cooking assistant. Given an instruction step and a timer duration, generate a short, descriptive label for the timer that captures what's being timed.

User Template: Instruction: {step_text}
Duration: {duration_minutes} minutes
Existing timers: {existing_timer_labels}

Return a JSON object: {"label": "Short descriptive label (2-4 words)"}

Examples:
- "Bake until golden" + 15 min → "Bake Pizza"
- "Simmer for 20 minutes" + 20 min → "Simmer Sauce"
- "Let rest" + 5 min → "Rest Meat"
```

**9. Remix Suggestions (`remix_suggestions`):**
```
System: You are a creative culinary advisor. Given a recipe, suggest 6 creative ways to remix or modify it. Consider dietary variations, flavor twists, cultural adaptations, and ingredient substitutions. Make suggestions specific to this recipe, not generic.

User Template: Recipe: {recipe_title}
Category: {category}
Cuisine: {cuisine}
Key ingredients: {key_ingredients}

Return a JSON array of 6 suggestion strings, each 3-8 words describing a specific modification.
```

**10. CSS Selector Repair (`selector_repair`):**
```
System: You are an expert web scraping engineer. Analyze HTML from a recipe search results page and identify the CSS selector that would select links to individual recipe pages. Look for patterns like article cards, recipe listings, or link grids.

User Template: Site: {site_name} ({host})
Previous selector (now broken): {old_selector}

HTML sample (first 5000 chars):
{html_sample}

Return a JSON object: {"suggestions": ["selector1", "selector2", "selector3"], "confidence": "high|medium|low", "notes": "explanation of the pattern found"}
```

---

## 9. Recipe Scraping & Search

### Async Scraper Service with curl_cffi

```python
# apps/recipes/services/scraper.py

import asyncio
import hashlib
from typing import Optional
from urllib.parse import urlparse

from curl_cffi import AsyncSession
from curl_cffi.requests.exceptions import RequestException
from recipe_scrapers import scrape_html
from django.core.files.base import ContentFile

class RecipeScraper:
    """
    Async recipe scraping with browser fingerprint spoofing.
    Uses curl_cffi AsyncSession for parallel requests.
    Downloads and stores images locally.
    """

    BROWSER_PROFILES = ['chrome', 'safari', 'firefox']  # Use aliases for latest versions
    DEFAULT_TIMEOUT = 30
    RATE_LIMIT_DELAY = 1.5  # seconds between requests per domain

    async def scrape_url(self, url: str) -> dict:
        """Scrape recipe from URL and save to database.

        Always creates a new Recipe record - no deduplication.
        Re-importing the same URL creates a separate recipe.
        """
        from .models import Recipe

        # Fetch with fingerprint spoofing
        html = await self._fetch_with_fingerprint(url)

        # Parse with recipe-scrapers (wild_mode for unsupported sites)
        scraper = scrape_html(html, org_url=url, supported_only=False)

        # Extract ALL data from scraper
        data = self._extract_full_recipe_data(scraper, url)

        # Download and store image locally
        if data.get('image_url'):
            data['image'] = await self._download_image(data['image_url'])

        # Create recipe
        recipe = await Recipe.objects.acreate(**data)

        return {'recipe': recipe, 'cached': False}

    async def _fetch_with_fingerprint(self, url: str) -> str:
        """Fetch URL with browser fingerprint spoofing, trying multiple profiles"""
        async with AsyncSession() as session:
            for profile in self.BROWSER_PROFILES:
                try:
                    response = await session.get(
                        url,
                        impersonate=profile,
                        timeout=self.DEFAULT_TIMEOUT,
                        headers={
                            'Accept-Language': 'en-US,en;q=0.9',
                        }
                    )
                    response.raise_for_status()
                    return response.text
                except RequestException:
                    continue

        raise Exception(f"Failed to fetch {url} with all browser profiles")

    def _extract_full_recipe_data(self, scraper, url: str) -> dict:
        """Extract all available fields from recipe-scrapers"""
        return {
            'source_url': url,
            'canonical_url': self._safe_call(scraper.canonical_url) or '',
            'host': urlparse(url).netloc,
            'site_name': self._safe_call(scraper.site_name) or '',
            'title': self._safe_call(scraper.title) or 'Untitled Recipe',
            'author': self._safe_call(scraper.author) or '',
            'description': self._safe_call(scraper.description) or '',
            'image_url': self._safe_call(scraper.image) or '',
            'ingredients': self._safe_call(scraper.ingredients) or [],
            'ingredient_groups': self._extract_ingredient_groups(scraper),
            'instructions': self._safe_call(scraper.instructions_list) or [],
            'instructions_text': self._safe_call(scraper.instructions) or '',
            'prep_time': self._safe_call(scraper.prep_time),
            'cook_time': self._safe_call(scraper.cook_time),
            'total_time': self._safe_call(scraper.total_time),
            'yields': self._safe_call(scraper.yields) or '',
            'servings': self._parse_servings(self._safe_call(scraper.yields)),
            'category': self._safe_call(scraper.category) or '',
            'cuisine': self._safe_call(scraper.cuisine) or '',
            'cooking_method': self._safe_call(scraper.cooking_method) or '',
            'keywords': self._safe_call(scraper.keywords) or [],
            'dietary_restrictions': self._safe_call(scraper.dietary_restrictions) or [],
            'equipment': self._safe_call(scraper.equipment) or [],
            'nutrition': self._safe_call(scraper.nutrients) or {},
            'rating': self._safe_call(scraper.ratings),
            'rating_count': self._safe_call(scraper.ratings_count),
            'language': self._safe_call(scraper.language) or '',
            'links': self._safe_call(scraper.links) or [],
        }

    def _extract_ingredient_groups(self, scraper) -> list:
        """Extract structured ingredient groups if available"""
        try:
            groups = scraper.ingredient_groups()
            return [
                {'purpose': g.purpose, 'ingredients': g.ingredients}
                for g in groups
            ]
        except Exception:
            return []

    def _safe_call(self, method):
        """Safely call scraper method, return None on failure"""
        try:
            return method() if callable(method) else method
        except Exception:
            return None

    def _parse_servings(self, yields_str: str) -> Optional[int]:
        """Parse numeric servings from yields string"""
        if not yields_str:
            return None
        import re
        match = re.search(r'\d+', yields_str)
        return int(match.group()) if match else None

    async def _download_image(self, url: str) -> ContentFile:
        """Download image and return as Django file"""
        async with AsyncSession(impersonate='chrome136') as session:
            response = await session.get(url, timeout=30)
            response.raise_for_status()

            # Determine extension from content type
            content_type = response.headers.get('content-type', '')
            ext = '.jpg'
            if 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            elif 'gif' in content_type:
                ext = '.gif'

            filename = hashlib.md5(url.encode()).hexdigest() + ext
            return ContentFile(response.content, name=filename)
```

### Async Multi-Site Search

```python
# apps/recipes/services/search.py

import asyncio
from typing import Dict, List
from curl_cffi import AsyncSession
from .models import SearchSource

class RecipeSearch:
    """Async multi-site recipe search using enabled sources"""

    MAX_CONCURRENT = 10
    RATE_LIMIT_DELAY = 1.5  # seconds between requests to same domain

    async def search(self, query: str, page: int = 1, per_page: int = 6) -> Dict:
        """Search enabled sites in parallel using async"""
        enabled_sources = await SearchSource.get_enabled_sources()

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        async with AsyncSession(impersonate='chrome136', timeout=30) as session:
            tasks = [
                self._search_site_with_limit(session, semaphore, source, query)
                for source in enabled_sources
            ]
            site_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and filter results
        results = []
        for site_result in site_results:
            if isinstance(site_result, Exception):
                continue
            results.extend(site_result)

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)

        # AI ranking (if enabled and API key configured)
        if await self._ai_ranking_enabled():
            unique_results = await self._rank_with_ai(query, unique_results)

        # Paginate
        total = len(unique_results)
        start = (page - 1) * per_page
        end = start + per_page

        return {
            'results': unique_results[start:end],
            'total': total,
            'page': page,
            'has_more': end < total,
            'sites': self._get_site_counts(unique_results)
        }

    async def _search_site_with_limit(
        self,
        session: AsyncSession,
        semaphore: asyncio.Semaphore,
        source: SearchSource,
        query: str
    ) -> List[Dict]:
        """Search a single site with rate limiting"""
        async with semaphore:
            return await self._search_site(session, source, query)

    async def _search_site(
        self,
        session: AsyncSession,
        source: SearchSource,
        query: str
    ) -> List[Dict]:
        """Fetch and parse search results from a single site"""
        try:
            url = source.search_url_template.format(query=query)
            response = await session.get(url)
            response.raise_for_status()

            # Parse results using site-specific selector
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select(source.result_selector)

            results = []
            for link in links[:10]:  # Limit to 10 per site
                href = link.get('href', '')
                if href and source.host in href:
                    results.append({
                        'url': href,
                        'title': link.get_text(strip=True),
                        'source': source.name,
                        'host': source.host,
                    })

            return results

        except Exception:
            return []
```

---

## 10. Search Sources Configuration

### 15 Curated Search Sources

These are the 15 recipe sites from the Figma design, based on popularity and reliability. CSS selectors need to be validated during implementation.

| # | Site | Host | Search URL Template | Result Selector |
|---|------|------|---------------------|-----------------|
| 1 | AllRecipes | allrecipes.com | `https://www.allrecipes.com/search?q={query}` | TBD - validate during dev |
| 2 | BBC Good Food | bbcgoodfood.com | `https://www.bbcgoodfood.com/search?q={query}` | TBD - validate during dev |
| 3 | BBC Food | bbc.co.uk/food | `https://www.bbc.co.uk/food/search?q={query}` | TBD - validate during dev |
| 4 | Bon Appétit | bonappetit.com | `https://www.bonappetit.com/search?q={query}` | TBD - validate during dev |
| 5 | Budget Bytes | budgetbytes.com | `https://www.budgetbytes.com/?s={query}` | TBD - validate during dev |
| 6 | Delish | delish.com | `https://www.delish.com/search/?q={query}` | TBD - validate during dev |
| 7 | Epicurious | epicurious.com | `https://www.epicurious.com/search?q={query}` | TBD - validate during dev |
| 8 | Food Network | foodnetwork.com | `https://www.foodnetwork.com/search/{query}-` | TBD - validate during dev |
| 9 | Food52 | food52.com | `https://food52.com/recipes/search?q={query}` | TBD - validate during dev |
| 10 | Jamie Oliver | jamieoliver.com | `https://www.jamieoliver.com/search/?s={query}` | TBD - validate during dev |
| 11 | Tasty | tasty.co | `https://tasty.co/search?q={query}` | TBD - validate during dev |
| 12 | Serious Eats | seriouseats.com | `https://www.seriouseats.com/search?q={query}` | TBD - validate during dev |
| 13 | Simply Recipes | simplyrecipes.com | `https://www.simplyrecipes.com/search?q={query}` | TBD - validate during dev |
| 14 | Taste of Home | tasteofhome.com | `https://www.tasteofhome.com/search/?q={query}` | TBD - validate during dev |
| 15 | The Kitchn | thekitchn.com | `https://www.thekitchn.com/search?q={query}` | TBD - validate during dev |

### Source Management

- **15 curated sites** are available (not the full 575+ from recipe-scrapers)
- **All 15 enabled by default**
- **Settings → Sources tab** shows all sources with on/off toggles
- **Bulk actions**: Enable All / Disable All buttons
- When a source is disabled, it's excluded from search but saved recipes remain
- CSS selectors need validation during development using curl_cffi

### Selector Maintenance Strategy

Since recipe sites frequently update their HTML structure, selectors need ongoing maintenance:

1. **AI-powered auto-repair (PRIMARY)** - When a selector fails, AI analyzes the HTML and suggests a replacement:
   - Fetches current search page with test query
   - AI identifies recipe link patterns in HTML structure
   - Auto-updates the selector in SearchSource model
   - Logs the change for review
   - Falls back to disable if AI cannot find valid selector
2. **In-app UI** - Settings → Source Selectors tab lets users edit selectors and test connectivity
3. **Test endpoint** - `/api/sources/test/{host}/` runs a test search and reports success/failure
4. **Individual testing** - "Test" button per source for quick validation
5. **Bulk testing** - "Test All Sources" button tests all 15 sources
6. **Auto-disable** - If AI repair fails 3+ times, source is automatically disabled
7. **Status tracking** - Visual indicators (✓ working, ✗ broken, ? untested) with timestamps
8. **Django admin backup** - Full selector editing also available via `/admin/` for bulk operations

### Search Result Parsing

Each source has a CSS selector for extracting recipe links from search results:

```python
# apps/recipes/services/search.py

async def _parse_search_results(self, html: str, source: SearchSource) -> List[Dict]:
    """Parse search results using site-specific CSS selector"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    results = []
    for element in soup.select(source.result_selector)[:10]:
        href = element.get('href', '')

        # Handle relative URLs
        if href.startswith('/'):
            href = f"https://{source.host}{href}"

        # Only include URLs from this host
        if source.host in href or href.startswith('/'):
            results.append({
                'url': href,
                'title': element.get_text(strip=True),
                'source': source.name,
                'host': source.host,
            })

    return results
```

### Data Migration

On first run, a data migration will:
1. Create SearchSource records for each of the 15 sites
2. Set all 15 as enabled by default
3. Include the search URL template (selectors TBD during implementation)

---

## 11. Serving Adjustment Architecture

### Design Decision: AI-Only, On-the-Fly (Not Persisted)

Serving adjustment **requires AI** and is **not saved** to the database.

**Rationale:**
- AI provides intelligent scaling (non-linear for spices, baking ratios)
- Users frequently adjust servings while cooking (4→6→8→4)
- Saving each adjustment would bloat the database
- Original recipe data should remain pristine
- When AI is unavailable, serving adjustment is hidden entirely

### Implementation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    User Adjusts Servings                             │
│                    (4 servings → 8 servings)                         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 AI Scaling (Required)                                │
│                                                                      │
│  - Calls POST /api/ai/scale/                                        │
│  - AI handles:                                                       │
│    - Proportional scaling for most ingredients                      │
│    - Non-linear scaling (salt, spices don't double)                 │
│    - Baking ratios (precise for chemistry)                          │
│    - Unit conversions (metric/imperial)                              │
│  - Returns scaled ingredients                                        │
│  - NOT persisted to database                                         │
│  - Cached in memory for current view only                            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 Feature Hidden When:                                 │
│                                                                      │
│  - No API key configured                                            │
│  - Recipe has no servings value (null) - can't scale without base   │
│  - No fallback to simple math                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Comparison with Recipe Remix

| Aspect | Serving Adjustment | Recipe Remix |
|--------|-------------------|--------------|
| **Persisted?** | No | Yes (new Recipe record) |
| **Changes title?** | No | Yes (new creative title) |
| **Changes instructions?** | No | Yes |
| **Shows in favorites?** | No | Yes (as separate recipe) |
| **Use case** | Cooking now, need more/less | Want a variation to keep |

---

## 12. Play Mode Features

### Smart Timer Features

Play mode includes intelligent timer functionality:

#### 1. Quick Timer Actions
- +5 min, +10 min, +15 min preset buttons
- One-click timer creation
- Multiple simultaneous timers

#### 2. AI Timer Naming
When a timer is created:
1. Current step text is sent to `/api/ai/timer-name/`
2. AI generates a descriptive label based on context
3. Label is used instead of generic "Timer 1"

**Examples:**
- Step: "Bake until golden brown" + 15 min → "Bake Pizza"
- Step: "Simmer on low heat" + 20 min → "Simmer Sauce"
- Step: "Let the dough rest" + 10 min → "Rest Dough"

#### 3. Smart Timer Suggestions (Auto-Detection)
Parse instruction text for time mentions and suggest timers:

**Detection Patterns:**
- "for X minutes" / "for X mins"
- "X minute(s)" / "X min(s)"
- "about X minutes"
- "approximately X minutes"

**UI:**
- When time detected in current step, show suggestion badge
- "Add 15 min timer" button appears automatically
- Click to create timer with AI-generated label

**Implementation:**
```python
import re

TIME_PATTERNS = [
    r'for\s+(\d+)\s*(?:minutes?|mins?)',
    r'(\d+)\s*(?:minutes?|mins?)',
    r'about\s+(\d+)\s*(?:minutes?|mins?)',
    r'approximately\s+(\d+)\s*(?:minutes?|mins?)',
]

def extract_time_from_step(step_text: str) -> Optional[int]:
    """Extract time in minutes from instruction text"""
    for pattern in TIME_PATTERNS:
        match = re.search(pattern, step_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None
```

#### 4. Timer Widget Features
- Countdown display (MM:SS)
- Play/Pause toggle
- Reset to original duration
- Delete timer
- Progress bar
- Completion toast notification
- **Audio alert**: Default browser notification sound (no custom audio files)

---

## 13. Build Order

### Phase 1: Foundation
**Goal:** Django project with database and Docker running

1. Django project setup with single `settings.py`
2. Docker + docker-compose (single environment, hot reload)
3. nginx configuration
4. Database models: AppSettings, Profile
5. Profile API endpoints
6. Device detection middleware
7. Basic URL routing
8. Helper script (`bin/dev`)

### Phase 2: Recipe Core
**Goal:** Recipe scraping and storage working

9. Recipe model with full recipe-scrapers fields
10. SearchSource model with 15 curated sites (data migration)
11. Async scraper service with curl_cffi
12. Image download and local storage
13. Recipe API endpoints (scrape, list, detail, delete)
14. Async multi-site search service
15. Search API endpoint with source filtering

### Phase 3: User Features + Theme Sync Tooling
**Goal:** Favorites, collections, history working; theme sync ready for frontends

16. RecipeFavorite model and API
17. RecipeCollection model and API
18. RecipeViewHistory model and API
19. Profile-based data isolation
20. Figma theme sync tooling (see FIGMA_TOOLING.md Phase 1)
    - `tooling/` directory structure
    - `bin/figma-sync-theme` script
    - Theme mapping JSON

### Phase 4: Profile Selector (Both Frontends)
**Goal:** Profile selection working on both interfaces

21. Vite/React project setup with Tailwind v4, theme.css from Figma
22. React: API client with fetch
23. React: Profile selector screen
24. Legacy: Base template and CSS (light theme only)
25. Legacy: ES5 JavaScript modules (ajax, state, router)
26. Legacy: Profile selector screen

### Phase 5: Home & Search (Both Frontends)
**Goal:** Home screen and search working on both interfaces

27. React: Home screen with search bar
28. React: Favorites/Discover toggle
29. React: Basic recipe card component
30. React: Dark/light theme toggle
31. Legacy: Home screen with search bar
32. Legacy: Favorites/Discover toggle
33. Legacy: Recipe card partial
34. React: Search results with source filters and pagination
35. Legacy: Search results with source filters

### Phase 6: Recipe Detail & Play Mode (Both Frontends)
**Goal:** Recipe viewing and cooking mode on both interfaces

36. React: Recipe detail screen with tabs (Ingredients, Instructions, Nutrition, Tips)
37. React: Serving adjustment UI (AI-powered)
38. React: Play mode with smart timers
39. Legacy: Recipe detail screen with tabs
40. Legacy: Serving adjustment UI
41. Legacy: Play mode with timers

### Phase 7: Collections & Favorites (Both Frontends)
**Goal:** Recipe organization on both interfaces

42. React: Favorites screen
43. React: Collections screens (list, detail, create)
44. Legacy: Favorites screen
45. Legacy: Collections screens

### Phase 8: AI Integration
**Goal:** All 10 AI features working

46. OpenRouter service
47. AIPrompt model with 10 default prompts (data migration)
48. React: AI Prompts settings UI (all 10 editable)
49. React: Recipe remix feature with AI suggestions modal
50. Legacy: AI Prompts settings UI
51. Legacy: Recipe remix feature
52. Tips generation (cached in AIEnhancement)
53. Discover AI suggestions (3 types, daily refresh)
54. Search result ranking
55. Timer naming
56. Remix suggestions
57. Selector repair (AI-powered auto-fix)

### Phase 9: Settings & Polish (Both Frontends)
**Goal:** Production-ready

58. React: Settings screen (General, AI Prompts, Sources tabs)
59. Legacy: Settings screen (all tabs)
60. Error handling and edge cases
61. Loading states and skeletons (React) / Loading indicators (Legacy)
62. Toast notifications
63. Testing with pytest (unit + integration using Django test client)
64. Final cross-browser/device testing

---

## 14. Design Maintenance Workflow

### CRITICAL: Figma is the Source of Truth

The Figma export in `/home/matt/cookie2/Cookie Recipe App Design/` defines the design. When updated:

1. **Fresh exports replace the entire directory** - Don't merge, replace completely
2. **Design changes are authoritative** - If Figma says it, the app does it
3. **Implementation adapts to design** - Not the other way around

### Figma → Code Update Process

```
1. Designer updates Figma
        │
        ▼
2. Export via Figma Make (replaces entire directory):
   /home/matt/cookie2/Cookie Recipe App Design/
        │
        ▼
3. Tell Claude Code to update Cookie 2
        │
        ▼
4. Claude compares export with current code:
   - Identifies new/changed components
   - Identifies style changes (theme.css)
   - Identifies new screens or features
        │
        ▼
5. Claude updates:
   a. React components (from Figma export)
   b. Tailwind/CSS (from theme.css)
   c. Legacy CSS (manual translation, light theme only)
   d. Legacy templates (feature parity, simplified layout)
        │
        ▼
6. Test both interfaces:
   - Modern browser
   - iOS 9 iPad
```

### Repeatable Update Checklist

When a new Figma export arrives:

- [ ] Compare `src/styles/theme.css` for color/spacing changes
- [ ] Compare `src/app/App.tsx` for new screens or screen changes
- [ ] Compare `src/app/components/*.tsx` for component updates
- [ ] Update React components to match new export
- [ ] Update legacy CSS (light theme values only from theme.css)
- [ ] Update legacy templates for feature parity
- [ ] Run both interfaces and verify visually
- [ ] Document any new features that need backend work

### Component Mapping

| Figma Export | React | Legacy |
|--------------|-------|--------|
| `src/app/App.tsx` | Screens in `frontend/src/screens/` | Django templates |
| `src/app/components/*.tsx` | `frontend/src/components/` | Template partials + JS |
| `src/styles/theme.css` | `frontend/src/styles/theme.css` | `legacy/static/css/base.css` (light only) |
| State management | React useState | Cookie.state (ES5) |
| API calls | fetch + hooks | XMLHttpRequest |

### Legacy Translation Rules

| Modern (React/ES6+) | Legacy (ES5) |
|---------------------|--------------|
| `const/let` | `var` |
| Arrow functions | `function() {}` |
| Template literals | String concatenation |
| `async/await` | Callbacks |
| `fetch()` | `XMLHttpRequest` |
| Destructuring | Manual property access |
| Spread operator | `Object.assign()` |
| Classes | Prototypes |
| Modules | IIFE + global namespace |
| Dark mode | Light theme only |

---

## 15. Cookie 1 Lessons Learned

### What Worked Well

1. **Passwordless profiles** - Perfect for kitchen/family use
2. **recipe-scrapers library** - Supports 563 hosts
3. **curl_cffi for fingerprint spoofing** - Bypasses bot detection
4. **Session-based auth** - Simple, long-lived sessions
5. **Play mode for cooking** - Step-by-step is intuitive
6. **Timers with audio** - Essential for cooking
7. **Per-profile data isolation** - Clean separation
8. **Rate limiting** - 1.5s between requests per domain prevents blocking

### What to Improve

1. **Frontend complexity** - ES5-only was painful, dual interface is better
2. **Code organization** - Monolithic App.tsx → proper screen components
3. **Image handling** - Proxy was a workaround, storing locally is better
4. **AI integration** - Was bolted on, now first-class citizen
5. **State management** - Was scattered, now centralized
6. **Testing** - Minimal in Cookie 1, comprehensive in Cookie 2
7. **Environment complexity** - Multiple configs → single environment
8. **Sync scraping** - Was slow, async is much faster

### iOS 9 Compatibility Checklist

- [ ] ES5 only (no const/let, arrow functions, template literals)
- [ ] XMLHttpRequest (no fetch)
- [ ] Flexbox with -webkit prefixes (no CSS Grid)
- [ ] Light theme only (no CSS custom properties)
- [ ] Touch targets minimum 44px
- [ ] Font size 16px+ for inputs (prevent zoom)
- [ ] -webkit-overflow-scrolling: touch
- [ ] AudioContext on user gesture only
- [ ] No async/await
- [ ] Polyfills: Element.closest(), Element.matches()

---

## 16. AI Development Tooling

Tools to make AI feature development, testing, and debugging easier.

### Directory Structure

```
cookie2/
├── bin/
│   ├── ai-prompt-test      # Test prompts in isolation
│   ├── ai-context-preview  # Preview context sent to AI
│   └── ai-prompts          # Export/import/reset prompts
├── tooling/
│   ├── ai-schemas.json     # JSON schemas for AI responses
│   └── lib/
│       └── ai_validator.py # Response validation logic
```

### 16.1 Prompt Testing Tool

**`bin/ai-prompt-test`** - Test prompts without running the full application.

```bash
# Test a single prompt with sample data
./bin/ai-prompt-test recipe_remix --recipe="Chocolate Chip Cookies" --user-prompt="Make it vegan"

# Test with specific model
./bin/ai-prompt-test recipe_remix --model=openai/gpt-4o-mini

# Compare output across multiple models
./bin/ai-prompt-test recipe_remix --compare-models

# Validate response against schema
./bin/ai-prompt-test timer_naming --validate-schema

# Show token count and timing
./bin/ai-prompt-test tips_generation --metrics
```

**Sample Inputs:**
The tool includes sample inputs for each prompt type to enable quick testing.

### 16.2 AI Response Schema Validation

All 10 AI prompts return JSON. Define expected schemas to catch malformed responses.

**`tooling/ai-schemas.json`:**

```json
{
  "version": "1.0.0",
  "schemas": {
    "recipe_remix": {
      "type": "object",
      "required": ["title", "ingredients", "instructions", "description"],
      "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "ingredients": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "instructions": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "description": {"type": "string", "maxLength": 500}
      }
    },
    "serving_adjustment": {
      "type": "object",
      "required": ["ingredients"],
      "properties": {
        "ingredients": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "array", "items": {"type": "string"}}
      }
    },
    "tips_generation": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 3,
      "maxItems": 5
    },
    "discover_favorites": {
      "type": "object",
      "required": ["search_query", "title", "description"],
      "properties": {
        "search_query": {"type": "string", "minLength": 2, "maxLength": 50},
        "title": {"type": "string", "maxLength": 100},
        "description": {"type": "string", "maxLength": 300}
      }
    },
    "discover_seasonal": {
      "type": "object",
      "required": ["search_query", "title", "description"],
      "properties": {
        "search_query": {"type": "string", "minLength": 2, "maxLength": 50},
        "title": {"type": "string", "maxLength": 100},
        "description": {"type": "string", "maxLength": 300},
        "context_data": {
          "type": "object",
          "properties": {
            "holiday": {"type": "string"},
            "country": {"type": "string"}
          }
        }
      }
    },
    "discover_new": {
      "type": "object",
      "required": ["search_query", "title", "description"],
      "properties": {
        "search_query": {"type": "string", "minLength": 2, "maxLength": 50},
        "title": {"type": "string", "maxLength": 100},
        "description": {"type": "string", "maxLength": 300}
      }
    },
    "search_ranking": {
      "type": "array",
      "items": {"type": "integer", "minimum": 0}
    },
    "timer_naming": {
      "type": "object",
      "required": ["label"],
      "properties": {
        "label": {"type": "string", "minLength": 1, "maxLength": 30}
      }
    },
    "remix_suggestions": {
      "type": "array",
      "items": {"type": "string", "minLength": 3, "maxLength": 50},
      "minItems": 6,
      "maxItems": 6
    },
    "selector_repair": {
      "type": "object",
      "required": ["suggestions", "confidence"],
      "properties": {
        "suggestions": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "notes": {"type": "string", "maxLength": 500}
      }
    }
  }
}
```

**Validation in OpenRouter Service:**

```python
# ai/services/openrouter.py

import json
import jsonschema
from django.conf import settings

class AIResponseValidationError(Exception):
    """Raised when AI response doesn't match expected schema"""
    pass

def validate_response(prompt_type: str, response_data: dict | list) -> None:
    """
    Validate AI response against expected schema.
    Raises AIResponseValidationError if validation fails.
    """
    schemas = load_ai_schemas()
    schema = schemas.get(prompt_type)

    if not schema:
        return  # No schema defined, skip validation

    try:
        jsonschema.validate(response_data, schema)
    except jsonschema.ValidationError as e:
        raise AIResponseValidationError(
            f"AI response for {prompt_type} failed validation: {e.message}"
        )
```

### 16.3 AI Debug Logging

Optional request/response logging controlled by Django's `DEBUG` setting.
Logging is enabled in development (`DEBUG=True`) and disabled in production.

**Model Addition:**

```python
# ai/models.py

class AIRequestLog(models.Model):
    """
    Debug log for AI requests.
    Only populated when Django DEBUG=True (development mode).
    Useful for debugging prompt issues and replaying requests.
    """
    prompt_type = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    system_prompt = models.TextField()
    user_prompt = models.TextField()
    response_raw = models.TextField()
    response_parsed = models.JSONField(null=True, blank=True)
    parse_error = models.TextField(blank=True)
    validation_error = models.TextField(blank=True)
    tokens_in = models.PositiveIntegerField(null=True, blank=True)
    tokens_out = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField()
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['prompt_type', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]
        ordering = ['-created_at']

    @classmethod
    def cleanup_old_logs(cls, days: int = 7):
        """Delete logs older than N days"""
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        cls.objects.filter(created_at__lt=cutoff).delete()
```

**Logging in OpenRouter Service:**

```python
# ai/services/openrouter.py

from django.conf import settings as django_settings

async def call_openrouter(prompt: AIPrompt, context: dict) -> dict:
    """Call OpenRouter API with optional debug logging"""
    from .models import AIRequestLog

    start_time = time.time()

    # Build prompts
    system_prompt = prompt.system_prompt
    user_prompt = prompt.user_prompt_template.format(**context)

    try:
        response = await _make_openrouter_request(prompt.model, system_prompt, user_prompt)
        parsed = json.loads(response['content'])
        validate_response(prompt.prompt_type, parsed)

        # Log in development mode
        if django_settings.DEBUG:
            await AIRequestLog.objects.acreate(
                prompt_type=prompt.prompt_type,
                model=prompt.model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_raw=response['content'],
                response_parsed=parsed,
                tokens_in=response.get('usage', {}).get('prompt_tokens'),
                tokens_out=response.get('usage', {}).get('completion_tokens'),
                latency_ms=int((time.time() - start_time) * 1000),
                success=True,
            )

        return parsed

    except Exception as e:
        # Always log failures in development mode
        if django_settings.DEBUG:
            await AIRequestLog.objects.acreate(
                prompt_type=prompt.prompt_type,
                model=prompt.model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_raw=str(e),
                parse_error=str(e) if isinstance(e, json.JSONDecodeError) else '',
                validation_error=str(e) if isinstance(e, AIResponseValidationError) else '',
                latency_ms=int((time.time() - start_time) * 1000),
                success=False,
            )
        raise
```

### 16.4 Context Preview Tool

**`bin/ai-context-preview`** - See exactly what data will be sent to AI.

```bash
# Preview context for Discover calls
./bin/ai-context-preview discover_favorites --profile=1

# Preview search ranking context
./bin/ai-context-preview search_ranking --query="chocolate cookies" --results=10

# Show estimated token count
./bin/ai-context-preview discover_new --profile=1 --show-tokens
```

Useful for debugging when AI responses seem off - lets you see what context it received.

### 16.5 Prompt Export/Import Tool

**`bin/ai-prompts`** - Manage prompts outside the database.

```bash
# Export all prompts to YAML (for version control)
./bin/ai-prompts export > prompts.yaml

# Import prompts (updates existing, creates missing)
./bin/ai-prompts import < prompts.yaml

# Reset specific prompt to default
./bin/ai-prompts reset recipe_remix

# Reset all prompts to defaults
./bin/ai-prompts reset --all

# Show diff between current and default
./bin/ai-prompts diff

# List all prompts with their models
./bin/ai-prompts list
```

**Export Format (YAML):**

```yaml
version: "1.0"
exported_at: "2026-01-07T14:30:00Z"
prompts:
  recipe_remix:
    name: "Recipe Remix"
    description: "Creates new recipe variations based on user input"
    model: "anthropic/claude-3.5-haiku"
    system_prompt: |
      You are a culinary expert helping to remix recipes...
    user_prompt_template: |
      Original recipe: {recipe_title}
      Ingredients: {ingredients}
      ...
  timer_naming:
    name: "Timer Naming"
    # ...
```

### 16.6 AI-Assisted Selector Repair

When CSS selectors break, AI can analyze HTML and suggest fixes.

**API Endpoint Addition:**

```
POST /api/sources/{host}/suggest-selector/   # AI suggests new CSS selector
```

**Implementation:**

```python
# recipes/services/selector_repair.py

async def suggest_selector(source: SearchSource) -> list[str]:
    """
    Use AI to analyze HTML and suggest CSS selectors for recipe links.

    1. Fetch current search page from source
    2. Send HTML sample to AI
    3. Return suggested selectors
    """
    # Fetch sample HTML
    html = await fetch_search_page(source, query="chocolate chip cookies")

    prompt = f"""
    Analyze this HTML from {source.name} ({source.host}) search results page.
    The previous selector was: {source.result_selector}

    Identify the CSS selector that would select links to individual recipe pages.
    Look for patterns in the HTML structure.

    Return JSON: {{"suggestions": ["selector1", "selector2", "selector3"], "confidence": "high|medium|low", "notes": "explanation"}}

    HTML sample (first 5000 chars):
    {html[:5000]}
    """

    response = await call_ai_for_selector(prompt)
    return response['suggestions']
```

**Frontend Integration:**

In Settings → Source Selectors tab, add "Suggest Fix" button for broken sources that calls this endpoint and populates the selector field with suggestions.

### 16.7 Caching Strategy for AI Features

| Feature | Caching Strategy |
|---------|------------------|
| **AI Tips** | Saved to `Recipe.ai_tips` field permanently. Never expires. Only regenerated when creating a remix recipe. |
| **Discover Suggestions** | Stored in `AIDiscoverySuggestion` model. Refreshed daily per profile. Old suggestions deleted on refresh. |
| **Serving Adjustment** | Not cached. Computed on-the-fly each request. |
| **Search Ranking** | Not cached. Applied per search session. |
| **Timer Naming** | Not cached. Generated per timer creation. |
| **Remix Suggestions** | Not cached. Generated fresh when opening remix modal. |

---

## 17. Error Handling Strategy

### Philosophy

- **Log errors to application logs** - All errors logged with full context for debugging
- **Return appropriate HTTP error codes** - Clients receive structured error responses
- **Frontend displays generic messages** - Users see "Something went wrong" without technical details
- **No silent failures** - All errors are logged, none swallowed

### AI Error Handling

```python
# ai/services/openrouter.py

import logging

logger = logging.getLogger(__name__)

class AIError(Exception):
    """Base class for AI errors"""
    pass

class AIUnavailableError(AIError):
    """API key not configured or OpenRouter unreachable"""
    pass

class AIResponseError(AIError):
    """AI returned invalid/unparseable response"""
    pass

async def call_openrouter(prompt: AIPrompt, context: dict) -> dict:
    """
    Call OpenRouter API.

    Raises:
        AIUnavailableError: If API key missing or service unreachable
        AIResponseError: If response is invalid or fails schema validation
    """
    settings = await AppSettings.objects.afirst()

    if not settings or not settings.openrouter_api_key:
        logger.warning("AI request attempted without API key configured")
        raise AIUnavailableError("OpenRouter API key not configured")

    try:
        response = await _make_request(...)
        parsed = json.loads(response['content'])
        validate_response(prompt.prompt_type, parsed)
        return parsed

    except httpx.HTTPError as e:
        logger.error(f"OpenRouter API error for {prompt.prompt_type}: {e}")
        raise AIUnavailableError(f"OpenRouter API unreachable: {e}")

    except json.JSONDecodeError as e:
        logger.error(f"AI response parse error for {prompt.prompt_type}: {e}")
        raise AIResponseError(f"Invalid JSON response: {e}")

    except AIResponseValidationError as e:
        logger.error(f"AI response validation failed for {prompt.prompt_type}: {e}")
        raise AIResponseError(str(e))
```

### API Error Responses

```python
# core/views.py

from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """Custom error responses for API endpoints"""

    # Handle AI errors
    if isinstance(exc, AIUnavailableError):
        logger.error(f"AI unavailable: {exc}", exc_info=True)
        return Response(
            {"error": "ai_unavailable", "message": "AI features temporarily unavailable"},
            status=503
        )

    if isinstance(exc, AIResponseError):
        logger.error(f"AI response error: {exc}", exc_info=True)
        return Response(
            {"error": "ai_error", "message": "AI processing failed"},
            status=500
        )

    # Handle scraping errors
    if isinstance(exc, ScrapingError):
        logger.error(f"Scraping failed: {exc}", exc_info=True)
        return Response(
            {"error": "scraping_failed", "message": "Could not fetch recipe"},
            status=502
        )

    # Default handling
    return exception_handler(exc, context)
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200` | Success | Normal responses |
| `201` | Created | Recipe scraped, profile created |
| `400` | Bad Request | Invalid input data |
| `404` | Not Found | Recipe/profile doesn't exist |
| `422` | Unprocessable | Valid format but can't process (e.g., unsupported recipe site) |
| `500` | Server Error | Unexpected errors (logged, investigated) |
| `502` | Bad Gateway | External service failed (scraping failed) |
| `503` | Service Unavailable | AI unavailable (no API key or service down) |

### Frontend Error Display

```typescript
// frontend/src/api/client.ts

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    // Log for debugging but show generic message to user
    console.error('API Error:', error);

    // Show toast with user-friendly message
    if (response.status === 503) {
      toast.error('This feature is temporarily unavailable');
    } else if (response.status >= 500) {
      toast.error('Something went wrong. Please try again.');
    } else if (response.status === 404) {
      toast.error('Not found');
    } else {
      toast.error('Request failed. Please try again.');
    }

    throw new APIError(response.status, error);
  }

  return response.json();
}
```

---

## 18. Background Task Architecture

### Current Approach: Asyncio

For Cookie 2's use cases, **asyncio with Django async views** is sufficient:

- **Multi-site search** - `asyncio.gather()` for parallel HTTP requests
- **Recipe scraping** - Single async operation with curl_cffi
- **Image downloads** - Async during scrape

No separate worker process or message queue needed for initial release.

### Implementation

```python
# recipes/services/search.py

import asyncio
from curl_cffi import AsyncSession

class RecipeSearch:
    MAX_CONCURRENT = 10

    async def search(self, query: str, page: int = 1) -> dict:
        """Search enabled sites in parallel using asyncio"""
        sources = await SearchSource.get_enabled_sources()

        # Semaphore limits concurrent requests
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        async with AsyncSession(impersonate='chrome') as session:
            tasks = [
                self._search_with_limit(session, semaphore, source, query)
                for source in sources
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions, log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Search failed for {sources[i].name}: {result}")
            else:
                valid_results.extend(result)

        return self._paginate(valid_results, page)
```

### Future: If Persistent Queuing Needed

If we later need scheduled tasks (e.g., nightly AI discovery refresh, periodic selector validation), add **Huey**:

```bash
pip install huey
```

**Why Huey:**
- Lightweight (single file can use SQLite backend)
- Simple API
- Works well with Django
- Supports scheduling, retries, priorities
- No Redis required (can use SQLite for small deployments)

**Future Consideration:**
Django 6.0 introduces `django.tasks` - a built-in task API. When upgrading to Django 6.x, evaluate migrating to the built-in solution.

---

## 19. API Architecture Notes

### Rate Limiting (Future Implementation)

The API should be architected to support rate limiting when needed. Current approach:

**Recommended Library:** `django-ratelimit`

```bash
pip install django-ratelimit
```

**Architecture Preparation:**
- All API views use class-based views (easy to add decorators)
- User/profile identification available in request context
- Rate limit headers can be added to responses

**Example (for future implementation):**

```python
from django_ratelimit.decorators import ratelimit

class RecipeSearchView(APIView):
    @ratelimit(key='ip', rate='30/m', block=True)
    def get(self, request):
        # Search implementation
        pass

class AIRemixView(APIView):
    @ratelimit(key='ip', rate='10/m', block=True)  # Stricter for AI
    def post(self, request):
        # Remix implementation
        pass
```

**Rate Limit Strategy (when implemented):**

| Endpoint Category | Suggested Limit | Rationale |
|-------------------|-----------------|-----------|
| Read operations | 60/min | Normal browsing |
| Search | 30/min | Prevents scraping abuse |
| Recipe scrape | 10/min | Heavy operation |
| AI features | 10/min | Cost control |
| Profile operations | 20/min | Low risk |

**Not Implementing Now:**
- Single-user/family app, abuse unlikely
- Add when/if needed
- Architecture supports easy addition

---

## Appendix: Quick Reference

### Key File Locations

| Purpose | Modern | Legacy |
|---------|--------|--------|
| Entry point | `frontend/src/main.tsx` | `legacy/templates/legacy/base.html` |
| Theme | `frontend/src/styles/theme.css` | `legacy/static/legacy/css/base.css` |
| Components | `frontend/src/components/` | `legacy/templates/legacy/partials/` |
| API client | `frontend/src/api/client.ts` | `legacy/static/legacy/js/ajax.js` |
| Screens | `frontend/src/screens/` | `legacy/templates/legacy/*.html` |

### Docker Commands

```bash
# Start development environment
docker-compose up -d

# Rebuild after dependency changes
docker-compose up -d --build

# View logs
docker-compose logs -f

# Run Django management commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Helper script
./bin/dev start
./bin/dev restart
./bin/dev logs
```

### Environment Variables (.env)

```bash
# Required
SECRET_KEY=your-secret-key-here
OPENROUTER_API_KEY=your-openrouter-key  # Optional, can set in UI

# Optional
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
```
