/**
 * All Recipes page — filter + delete (ES5, iOS 9 compatible)
 */
(function() {
    'use strict';

    var filterInput = document.getElementById('recipe-filter');
    var clearBtn = document.getElementById('clear-filter-btn');
    var recipeGrid = document.getElementById('recipe-grid');
    var recipeCount = document.getElementById('recipe-count');
    var noResults = document.getElementById('no-results');

    if (!recipeGrid) return;

    // Wrappers are used for filter (carry title/host attrs) and delete
    var wrappers = recipeGrid.querySelectorAll('.recipe-card-wrapper');
    var totalCount = wrappers.length;
    if (recipeCount) {
        totalCount = parseInt(recipeCount.getAttribute('data-total'), 10) || totalCount;
    }

    function updateCountText(query, visibleCount) {
        if (!recipeCount) return;
        var suffix = totalCount !== 1 ? 's' : '';
        if (query) {
            recipeCount.textContent = visibleCount + ' of ' + totalCount + ' recipe' + suffix;
        } else {
            recipeCount.textContent = totalCount + ' recipe' + suffix;
        }
    }

    function filterRecipes() {
        if (!filterInput) return;
        var query = filterInput.value.toLowerCase().trim();
        var visibleCount = 0;

        if (clearBtn) {
            if (query) {
                clearBtn.classList.remove('hidden');
            } else {
                clearBtn.classList.add('hidden');
            }
        }

        for (var i = 0; i < wrappers.length; i++) {
            var wrapper = wrappers[i];
            // Data attrs are on the inner .recipe-card link
            var card = wrapper.querySelector('.recipe-card');
            var title = card ? (card.getAttribute('data-title') || '').toLowerCase() : '';
            var host = card ? (card.getAttribute('data-host') || '').toLowerCase() : '';

            if (!query || title.indexOf(query) !== -1 || host.indexOf(query) !== -1) {
                wrapper.style.display = '';
                visibleCount++;
            } else {
                wrapper.style.display = 'none';
            }
        }

        updateCountText(query, visibleCount);

        if (noResults) {
            if (visibleCount === 0 && query) {
                noResults.classList.remove('hidden');
                recipeGrid.classList.add('hidden');
            } else {
                noResults.classList.add('hidden');
                recipeGrid.classList.remove('hidden');
            }
        }
    }

    if (filterInput) {
        filterInput.addEventListener('input', filterRecipes);
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            filterInput.value = '';
            filterRecipes();
            filterInput.focus();
        });
    }

    // Delete recipe — two-tap confirm pattern (tap once → confirm state, tap again to delete)
    var pendingDeleteId = null;
    var pendingDeleteBtn = null;
    var pendingDeleteTimer = null;

    function clearPendingDelete() {
        if (pendingDeleteBtn) {
            pendingDeleteBtn.classList.remove('recipe-card-delete-confirm');
            pendingDeleteBtn.setAttribute('title', 'Delete recipe');
        }
        pendingDeleteId = null;
        pendingDeleteBtn = null;
        clearTimeout(pendingDeleteTimer);
    }

    recipeGrid.addEventListener('click', function(e) {
        var btn = null;
        var target = e.target;

        // Walk up to find the delete button (handles SVG child clicks)
        while (target && target !== recipeGrid) {
            if (target.getAttribute && target.getAttribute('data-delete-recipe')) {
                btn = target;
                break;
            }
            target = target.parentNode;
        }

        if (!btn) {
            // Click outside a delete button — clear pending state
            clearPendingDelete();
            return;
        }

        e.preventDefault();
        e.stopPropagation();

        var recipeId = btn.getAttribute('data-delete-recipe');

        if (pendingDeleteId === recipeId) {
            // Second tap — confirmed, delete it
            clearPendingDelete();
            var wrapper = btn.parentNode;
            var title = wrapper ? (wrapper.getAttribute('data-recipe-title') || 'Recipe') : 'Recipe';

            Cookie.ajax.delete('/api/recipes/' + recipeId + '/', function(err) {
                if (err) {
                    Cookie.toast.error('Failed to delete recipe');
                    return;
                }
                if (wrapper && wrapper.parentNode) {
                    wrapper.parentNode.removeChild(wrapper);
                }
                totalCount = Math.max(0, totalCount - 1);
                filterRecipes();
                Cookie.toast.success('"' + title + '" deleted');
            });
        } else {
            // First tap — enter confirm state
            clearPendingDelete();
            pendingDeleteId = recipeId;
            pendingDeleteBtn = btn;
            btn.classList.add('recipe-card-delete-confirm');
            btn.setAttribute('title', 'Tap again to confirm delete');
            pendingDeleteTimer = setTimeout(clearPendingDelete, 2500);
        }
    });

})();
