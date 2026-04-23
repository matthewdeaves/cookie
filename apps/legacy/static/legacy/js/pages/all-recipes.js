/**
 * All Recipes page filter (ES5, iOS 9 compatible)
 */
(function() {
    'use strict';

    var filterInput = document.getElementById('recipe-filter');
    var clearBtn = document.getElementById('clear-filter-btn');
    var recipeGrid = document.getElementById('recipe-grid');
    var recipeCount = document.getElementById('recipe-count');
    var noResults = document.getElementById('no-results');

    if (!filterInput || !recipeGrid) return;

    var cards = recipeGrid.querySelectorAll('.recipe-card');
    var totalCount = parseInt(recipeCount.getAttribute('data-total'), 10) || cards.length;

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
        var query = filterInput.value.toLowerCase().trim();
        var visibleCount = 0;

        if (clearBtn) {
            if (query) {
                clearBtn.classList.remove('hidden');
            } else {
                clearBtn.classList.add('hidden');
            }
        }

        for (var i = 0; i < cards.length; i++) {
            var card = cards[i];
            var title = (card.getAttribute('data-title') || '').toLowerCase();
            var host = (card.getAttribute('data-host') || '').toLowerCase();

            if (!query || title.indexOf(query) !== -1 || host.indexOf(query) !== -1) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
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

    filterInput.addEventListener('input', filterRecipes);

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            filterInput.value = '';
            filterRecipes();
            filterInput.focus();
        });
    }
})();
