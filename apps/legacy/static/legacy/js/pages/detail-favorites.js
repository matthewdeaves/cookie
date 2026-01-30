/**
 * Recipe Detail page - Favorites module (ES5, iOS 9 compatible)
 * Handles favorite button toggling.
 */
(function() {
    'use strict';

    function init() {
        var favoriteBtn = document.getElementById('favorite-btn');
        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', handleFavoriteClick);
        }
    }

    function handleFavoriteClick() {
        var btn = document.getElementById('favorite-btn');
        var isActive = btn.classList.contains('active');

        if (isActive) {
            removeFavorite(btn);
        } else {
            addFavorite(btn);
        }
    }

    function addFavorite(btn) {
        var state = Cookie.pages.detail.getState();

        Cookie.ajax.post('/api/favorites/', { recipe_id: state.recipeId }, function(err) {
            if (err) {
                Cookie.toast.error('Failed to add to favorites');
                return;
            }
            btn.classList.add('active');
            var svg = btn.querySelector('svg');
            if (svg) {
                svg.setAttribute('fill', 'currentColor');
            }
            btn.setAttribute('title', 'Remove from favorites');
            Cookie.toast.success('Added to favorites');
        });
    }

    function removeFavorite(btn) {
        var state = Cookie.pages.detail.getState();

        Cookie.ajax.delete('/api/favorites/' + state.recipeId + '/', function(err) {
            if (err) {
                Cookie.toast.error('Failed to remove from favorites');
                return;
            }
            btn.classList.remove('active');
            var svg = btn.querySelector('svg');
            if (svg) {
                svg.setAttribute('fill', 'none');
            }
            btn.setAttribute('title', 'Add to favorites');
            Cookie.toast.success('Removed from favorites');
        });
    }

    // Register with core module
    Cookie.pages.detail.registerFeature('favorites', {
        init: init
    });
})();
