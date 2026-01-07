/**
 * Favorites page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.favorites = (function() {
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
        // Favorite buttons
        var favoriteBtns = document.querySelectorAll('.recipe-card-favorite');
        for (var i = 0; i < favoriteBtns.length; i++) {
            favoriteBtns[i].addEventListener('click', handleFavoriteClick);
        }
    }

    /**
     * Handle favorite button click (unfavorite)
     */
    function handleFavoriteClick(e) {
        e.preventDefault();
        e.stopPropagation();

        var btn = e.currentTarget;
        var recipeId = btn.getAttribute('data-recipe-id');

        removeFavorite(recipeId, btn);
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

            // Animate and remove the card
            var card = btn.closest('.recipe-card');
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                card.style.transition = 'opacity 0.2s, transform 0.2s';
                setTimeout(function() {
                    card.remove();
                    updateCount();
                    checkEmpty();
                }, 200);
            }

            Cookie.toast.success('Removed from favorites');
        });
    }

    /**
     * Update the count display
     */
    function updateCount() {
        var cards = document.querySelectorAll('.recipe-card');
        var countEl = document.querySelector('.text-muted');
        if (countEl) {
            var count = cards.length;
            countEl.textContent = count + ' recipe' + (count !== 1 ? 's' : '');
        }
    }

    /**
     * Check if page should show empty state
     */
    function checkEmpty() {
        var cards = document.querySelectorAll('.recipe-card');
        if (cards.length === 0) {
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
        document.addEventListener('DOMContentLoaded', Cookie.pages.favorites.init);
    } else {
        Cookie.pages.favorites.init();
    }
})();
