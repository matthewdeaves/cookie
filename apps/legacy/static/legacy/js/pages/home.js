/**
 * Home page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.home = (function() {
    'use strict';

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
        // Logout/switch profile button
        var logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                window.location.href = '/legacy/';
            });
        }

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
    }

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
        });
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
            btn.classList.remove('active');
            // Update the heart icon to outline
            var svg = btn.querySelector('svg');
            if (svg) {
                svg.setAttribute('fill', 'none');
            }
            Cookie.toast.success('Removed from favorites');

            // If on home page, remove the card from view
            var card = btn.closest('.recipe-card');
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(function() {
                    card.remove();
                    // Check if favorites section is now empty
                    checkEmptyFavorites();
                }, 200);
            }
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
