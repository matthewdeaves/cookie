/**
 * Home page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.home = (function() {
    'use strict';

    // State
    var discoverLoaded = false;
    var discoverLoading = false;

    /**
     * Initialize the page
     */
    function init() {
        setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Search form submission
        var searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                var searchInput = document.getElementById('search-input');
                if (searchInput && !searchInput.value.trim()) {
                    e.preventDefault();
                }
            });
        }

        // Tab toggle buttons
        var tabBtns = document.querySelectorAll('.tab-toggle-btn');
        for (var i = 0; i < tabBtns.length; i++) {
            tabBtns[i].addEventListener('click', handleTabClick);
        }

        // Favorite buttons
        var favoriteBtns = document.querySelectorAll('.recipe-card-favorite');
        for (var j = 0; j < favoriteBtns.length; j++) {
            favoriteBtns[j].addEventListener('click', handleFavoriteClick);
        }

        // Discover button (in empty state)
        var discoverBtn = document.getElementById('discover-btn');
        if (discoverBtn) {
            discoverBtn.addEventListener('click', function() {
                document.getElementById('search-input').focus();
            });
        }

        // Discover refresh button
        var refreshBtn = document.getElementById('discover-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                loadDiscoverSuggestions(true);
            });
        }

        // Discover retry button (in error state)
        var retryBtn = document.getElementById('discover-retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', function() {
                loadDiscoverSuggestions(true);
            });
        }

        // Discover view favorites button (in no suggestions state)
        var viewFavoritesBtn = document.getElementById('discover-view-favorites-btn');
        if (viewFavoritesBtn) {
            viewFavoritesBtn.addEventListener('click', function() {
                // Switch to favorites tab
                var favoritesTabBtn = document.querySelector('.tab-toggle-btn[data-tab="favorites"]');
                if (favoritesTabBtn) {
                    favoritesTabBtn.click();
                }
            });
        }
    }

    /**
     * Handle tab click
     */
    function handleTabClick(e) {
        var btn = e.currentTarget;
        var tabName = btn.getAttribute('data-tab');

        // Update button states
        var allBtns = document.querySelectorAll('.tab-toggle-btn');
        for (var i = 0; i < allBtns.length; i++) {
            allBtns[i].classList.remove('active');
        }
        btn.classList.add('active');

        // Update tab content visibility
        var allTabs = document.querySelectorAll('.tab-content');
        for (var j = 0; j < allTabs.length; j++) {
            allTabs[j].classList.add('hidden');
        }

        var targetTab = document.getElementById('tab-' + tabName);
        if (targetTab) {
            targetTab.classList.remove('hidden');
        }

        // Load discover suggestions when tab is clicked (if AI available and not already loaded)
        if (tabName === 'discover' && !discoverLoaded && !discoverLoading) {
            var discoverTab = document.getElementById('tab-discover');
            var aiAvailable = discoverTab && discoverTab.getAttribute('data-ai-available') === 'true';
            if (aiAvailable) {
                loadDiscoverSuggestions(false);
            }
        }
    }

    /**
     * Hide all empty states
     */
    function hideAllEmptyStates() {
        var emptyNoApi = document.getElementById('discover-empty-no-api');
        var emptyError = document.getElementById('discover-empty-error');
        var emptyNone = document.getElementById('discover-empty-none');
        if (emptyNoApi) emptyNoApi.classList.add('hidden');
        if (emptyError) emptyError.classList.add('hidden');
        if (emptyNone) emptyNone.classList.add('hidden');
    }

    /**
     * Load discover suggestions from API
     */
    function loadDiscoverSuggestions(forceRefresh) {
        var discoverTab = document.getElementById('tab-discover');
        if (!discoverTab) return;

        var profileId = discoverTab.getAttribute('data-profile-id');
        if (!profileId) return;

        var loadingEl = document.getElementById('discover-loading');
        var contentEl = document.getElementById('discover-content');

        // Show loading state
        discoverLoading = true;
        if (loadingEl) loadingEl.classList.remove('hidden');
        if (contentEl) contentEl.classList.add('hidden');
        hideAllEmptyStates();

        // Add spinning animation to refresh button if refreshing
        var refreshBtn = document.getElementById('discover-refresh-btn');
        var refreshIcon = refreshBtn ? refreshBtn.querySelector('.refresh-icon') : null;
        if (forceRefresh && refreshIcon) {
            refreshIcon.classList.add('animate-spin');
        }

        var url = '/api/ai/discover/' + profileId + '/' + (forceRefresh ? '?refresh=true' : '');
        Cookie.ajax.get(url, function(err, data) {
            discoverLoading = false;

            // Remove spinning animation
            if (refreshIcon) {
                refreshIcon.classList.remove('animate-spin');
            }

            if (loadingEl) loadingEl.classList.add('hidden');

            if (err) {
                // Show error state
                var emptyError = document.getElementById('discover-empty-error');
                if (emptyError) emptyError.classList.remove('hidden');
                discoverLoaded = false;
                return;
            }

            if (!data || !data.suggestions || data.suggestions.length === 0) {
                // Show "no suggestions" state
                var emptyNone = document.getElementById('discover-empty-none');
                if (emptyNone) emptyNone.classList.remove('hidden');
                discoverLoaded = false;
                return;
            }

            // Render suggestions
            renderSuggestions(data.suggestions);
            if (contentEl) contentEl.classList.remove('hidden');
            discoverLoaded = true;
        });
    }

    /**
     * Render suggestion cards
     */
    function renderSuggestions(suggestions) {
        var container = document.getElementById('discover-suggestions');
        if (!container) return;

        Cookie.utils.setHtml(container, '');

        for (var i = 0; i < suggestions.length; i++) {
            var suggestion = suggestions[i];
            var card = createSuggestionCard(suggestion);
            container.appendChild(card);
        }
    }

    /**
     * Create a suggestion card element
     */
    function createSuggestionCard(suggestion) {
        var card = document.createElement('button');
        card.type = 'button';
        card.className = 'discover-card';
        card.setAttribute('data-search-query', suggestion.search_query);

        // Type label
        var typeLabel = getTypeLabel(suggestion.type);

        Cookie.utils.setHtml(card,
            '<div class="discover-card-header">' +
                '<svg class="discover-card-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                    '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path>' +
                '</svg>' +
                '<span class="discover-card-type">' + typeLabel + '</span>' +
            '</div>' +
            '<h3 class="discover-card-title">' + Cookie.utils.escapeHtml(suggestion.title) + '</h3>' +
            '<p class="discover-card-description">' + Cookie.utils.escapeHtml(suggestion.description) + '</p>' +
            '<div class="discover-card-search">' +
                '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                    '<circle cx="11" cy="11" r="8"></circle>' +
                    '<line x1="21" y1="21" x2="16.65" y2="16.65"></line>' +
                '</svg>' +
                '<span>Search: ' + Cookie.utils.escapeHtml(suggestion.search_query) + '</span>' +
            '</div>');

        card.addEventListener('click', function() {
            var query = this.getAttribute('data-search-query');
            if (query) {
                window.location.href = '/legacy/search/?q=' + encodeURIComponent(query);
            }
        });

        return card;
    }

    /**
     * Get display label for suggestion type
     */
    function getTypeLabel(type) {
        switch (type) {
            case 'favorites':
                return 'Based on Favorites';
            case 'seasonal':
                return 'Seasonal';
            case 'new':
                return 'Try Something New';
            default:
                return type;
        }
    }

    // Use shared utility: Cookie.utils.escapeHtml

    /**
     * Handle favorite button click
     */
    function handleFavoriteClick(e) {
        e.preventDefault();
        e.stopPropagation();

        var btn = e.currentTarget;
        var recipeId = btn.getAttribute('data-recipe-id');
        var isActive = btn.classList.contains('active');

        if (isActive) {
            // Remove from favorites
            removeFavorite(recipeId, btn);
        } else {
            // Add to favorites
            addFavorite(recipeId, btn);
        }
    }

    /**
     * Add recipe to favorites
     */
    function addFavorite(recipeId, btn) {
        Cookie.ajax.post('/api/favorites/', { recipe_id: parseInt(recipeId, 10) }, function(err) {
            if (err) {
                Cookie.toast.error('Failed to add to favorites');
                return;
            }
            btn.classList.add('active');
            // Update the heart icon to filled
            var svg = btn.querySelector('svg');
            if (svg) {
                svg.setAttribute('fill', 'currentColor');
            }
            Cookie.toast.success('Added to favorites');

            // Add card to favorites section on home page
            addCardToFavorites(btn);
        });
    }

    /**
     * Clone a recipe card into the favorites section on the home page.
     */
    function addCardToFavorites(btn) {
        var sourceCard = btn.closest('.recipe-card');
        if (!sourceCard) return;

        var favoritesTab = document.getElementById('tab-favorites');
        if (!favoritesTab) return;

        // Find or create the favorites grid
        var favGrid = favoritesTab.querySelector('.section:last-child .recipe-grid');
        var emptyState = favoritesTab.querySelector('.section:last-child .empty-state');

        if (!favGrid) {
            // Replace empty state with a grid
            if (emptyState) {
                favGrid = document.createElement('div');
                favGrid.className = 'recipe-grid';
                emptyState.parentNode.replaceChild(favGrid, emptyState);
            } else {
                return;
            }
        }

        // Check if card already exists in favorites
        var existingCard = favGrid.querySelector('.recipe-card[data-recipe-id="' + sourceCard.getAttribute('data-recipe-id') + '"]');
        if (existingCard) return;

        // Clone the card and ensure favorite button is active
        var clone = sourceCard.cloneNode(true);
        var cloneFavBtn = clone.querySelector('.recipe-card-favorite');
        if (cloneFavBtn) {
            cloneFavBtn.classList.add('active');
            var cloneSvg = cloneFavBtn.querySelector('svg');
            if (cloneSvg) {
                cloneSvg.setAttribute('fill', 'currentColor');
            }
            cloneFavBtn.addEventListener('click', handleFavoriteClick);
        }

        // Animate in
        clone.style.opacity = '0';
        clone.style.transform = 'scale(0.9)';
        favGrid.insertBefore(clone, favGrid.firstChild);
        // Force reflow then animate
        clone.offsetHeight;
        clone.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        clone.style.opacity = '1';
        clone.style.transform = 'scale(1)';

        // Update the "View All" count
        updateFavoritesCount(1);
    }

    /**
     * Update the favorites "View All (N)" count.
     */
    function updateFavoritesCount(delta) {
        var link = document.querySelector('#tab-favorites .section-header .section-link');
        if (!link) return;
        var match = link.textContent.match(/\((\d+)\)/);
        if (match) {
            var count = parseInt(match[1], 10) + delta;
            link.textContent = 'View All (' + count + ')';
        }
    }

    /**
     * Remove recipe from favorites
     */
    function removeFavorite(recipeId, btn) {
        Cookie.ajax.delete('/api/favorites/' + recipeId + '/', function(err) {
            if (err) {
                Cookie.toast.error('Failed to remove from favorites');
                return;
            }
            Cookie.toast.success('Removed from favorites');

            // Update ALL heart buttons for this recipe (recently viewed + favorites)
            var allBtns = document.querySelectorAll('.recipe-card-favorite[data-recipe-id="' + recipeId + '"]');
            for (var i = 0; i < allBtns.length; i++) {
                allBtns[i].classList.remove('active');
                var svg = allBtns[i].querySelector('svg');
                if (svg) {
                    svg.setAttribute('fill', 'none');
                }
            }

            // Remove the card from the favorites grid (not recently viewed)
            var favGrid = document.querySelector('#tab-favorites .section:last-child .recipe-grid');
            if (favGrid) {
                var favCard = favGrid.querySelector('.recipe-card[data-recipe-id="' + recipeId + '"]');
                if (favCard) {
                    favCard.style.opacity = '0';
                    favCard.style.transform = 'scale(0.9)';
                    setTimeout(function() {
                        favCard.remove();
                        checkEmptyFavorites();
                    }, 200);
                }
            }

            updateFavoritesCount(-1);
        });
    }

    /**
     * Check if favorites section should show empty state
     */
    function checkEmptyFavorites() {
        var favoritesSection = document.querySelector('#tab-favorites .section:last-child');
        if (!favoritesSection) return;

        var cards = favoritesSection.querySelectorAll('.recipe-card');
        if (cards.length === 0) {
            // Reload page to show empty state
            window.location.reload();
        }
    }

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.home.init);
    } else {
        Cookie.pages.home.init();
    }
})();
