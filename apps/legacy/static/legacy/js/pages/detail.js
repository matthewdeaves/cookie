/**
 * Recipe Detail page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.detail = (function() {
    'use strict';

    var recipeId;
    var currentServings;
    var originalServings;
    var selectedRemixSuggestion = null;
    var remixSuggestions = [];
    var isCreatingRemix = false;

    /**
     * Initialize the page
     */
    function init() {
        var pageEl = document.querySelector('[data-page="recipe-detail"]');
        if (!pageEl) return;

        recipeId = parseInt(pageEl.getAttribute('data-recipe-id'), 10);
        setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Back button
        var backBtn = document.getElementById('back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', handleBack);
        }

        // Meta section toggle
        var metaToggle = document.getElementById('meta-toggle');
        if (metaToggle) {
            metaToggle.addEventListener('click', handleMetaToggle);
        }

        // Tab buttons
        var tabs = document.querySelectorAll('.tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].addEventListener('click', handleTabClick);
        }

        // Favorite button
        var favoriteBtn = document.getElementById('favorite-btn');
        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', handleFavoriteClick);
        }

        // Collection button
        var collectionBtn = document.getElementById('collection-btn');
        if (collectionBtn) {
            collectionBtn.addEventListener('click', handleCollectionClick);
        }

        // Cook button
        var cookBtn = document.getElementById('cook-btn');
        if (cookBtn) {
            cookBtn.addEventListener('click', handleCookClick);
        }

        // Collection modal close
        var modalClose = document.getElementById('modal-close');
        if (modalClose) {
            modalClose.addEventListener('click', closeCollectionModal);
        }

        // Create collection button
        var createCollectionBtn = document.getElementById('create-collection-btn');
        if (createCollectionBtn) {
            createCollectionBtn.addEventListener('click', openCreateCollectionModal);
        }

        // Create collection modal close
        var createModalClose = document.getElementById('create-modal-close');
        if (createModalClose) {
            createModalClose.addEventListener('click', closeCreateCollectionModal);
        }

        // Collection options
        var collectionOptions = document.querySelectorAll('.collection-option');
        for (var j = 0; j < collectionOptions.length; j++) {
            collectionOptions[j].addEventListener('click', handleCollectionOptionClick);
        }

        // Create collection form
        var createForm = document.getElementById('create-collection-form');
        if (createForm) {
            createForm.addEventListener('submit', handleCreateCollection);
        }

        // Modal overlay click to close
        var collectionModal = document.getElementById('collection-modal');
        if (collectionModal) {
            collectionModal.addEventListener('click', function(e) {
                if (e.target === collectionModal) {
                    closeCollectionModal();
                }
            });
        }

        var createCollectionModal = document.getElementById('create-collection-modal');
        if (createCollectionModal) {
            createCollectionModal.addEventListener('click', function(e) {
                if (e.target === createCollectionModal) {
                    closeCreateCollectionModal();
                }
            });
        }

        // Serving adjuster
        var servingAdjuster = document.querySelector('.serving-adjuster');
        if (servingAdjuster) {
            originalServings = parseInt(servingAdjuster.getAttribute('data-original-servings'), 10);
            currentServings = originalServings;

            var decreaseBtn = servingAdjuster.querySelector('.serving-decrease');
            var increaseBtn = servingAdjuster.querySelector('.serving-increase');

            if (decreaseBtn) {
                decreaseBtn.addEventListener('click', function() {
                    adjustServings(-1);
                });
            }
            if (increaseBtn) {
                increaseBtn.addEventListener('click', function() {
                    adjustServings(1);
                });
            }

            updateServingButtons();
        }

        // Remix button
        var remixBtn = document.getElementById('remix-btn');
        if (remixBtn) {
            remixBtn.addEventListener('click', handleRemixClick);
        }

        // Remix modal close
        var remixModalClose = document.getElementById('remix-modal-close');
        if (remixModalClose) {
            remixModalClose.addEventListener('click', closeRemixModal);
        }

        // Remix modal overlay click to close
        var remixModal = document.getElementById('remix-modal');
        if (remixModal) {
            remixModal.addEventListener('click', function(e) {
                if (e.target === remixModal) {
                    closeRemixModal();
                }
            });
        }

        // Remix custom input
        var remixCustomInput = document.getElementById('remix-custom-input');
        if (remixCustomInput) {
            remixCustomInput.addEventListener('input', handleRemixCustomInput);
        }

        // Remix create button
        var remixCreateBtn = document.getElementById('remix-create-btn');
        if (remixCreateBtn) {
            remixCreateBtn.addEventListener('click', handleRemixCreate);
        }
    }

    /**
     * Handle back button click
     */
    function handleBack() {
        // Go back to previous page, or home if no history
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/legacy/home/';
        }
    }

    /**
     * Handle meta section toggle
     */
    function handleMetaToggle() {
        var toggle = document.getElementById('meta-toggle');
        var content = document.getElementById('meta-content');
        var chevron = document.getElementById('meta-chevron');

        if (content.classList.contains('hidden')) {
            content.classList.remove('hidden');
            toggle.classList.remove('collapsed');
            chevron.style.transform = 'rotate(0deg)';
        } else {
            content.classList.add('hidden');
            toggle.classList.add('collapsed');
            chevron.style.transform = 'rotate(180deg)';
        }
    }

    /**
     * Handle tab click
     */
    function handleTabClick(e) {
        var btn = e.currentTarget;
        var tabName = btn.getAttribute('data-tab');

        // Update button states
        var allTabs = document.querySelectorAll('.tab');
        for (var i = 0; i < allTabs.length; i++) {
            allTabs[i].classList.remove('active');
        }
        btn.classList.add('active');

        // Update tab content visibility
        var allContents = document.querySelectorAll('.tab-content');
        for (var j = 0; j < allContents.length; j++) {
            allContents[j].classList.add('hidden');
        }

        var targetContent = document.getElementById('tab-' + tabName);
        if (targetContent) {
            targetContent.classList.remove('hidden');
        }
    }

    /**
     * Handle favorite button click
     */
    function handleFavoriteClick() {
        var btn = document.getElementById('favorite-btn');
        var isActive = btn.classList.contains('active');

        if (isActive) {
            removeFavorite(btn);
        } else {
            addFavorite(btn);
        }
    }

    /**
     * Add to favorites
     */
    function addFavorite(btn) {
        Cookie.ajax.post('/api/favorites/', { recipe_id: recipeId }, function(err) {
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

    /**
     * Remove from favorites
     */
    function removeFavorite(btn) {
        Cookie.ajax.delete('/api/favorites/' + recipeId + '/', function(err) {
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

    /**
     * Handle collection button click
     */
    function handleCollectionClick() {
        var modal = document.getElementById('collection-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    /**
     * Close collection modal
     */
    function closeCollectionModal() {
        var modal = document.getElementById('collection-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Open create collection modal
     */
    function openCreateCollectionModal() {
        closeCollectionModal();
        var modal = document.getElementById('create-collection-modal');
        if (modal) {
            modal.classList.remove('hidden');
            var nameInput = document.getElementById('collection-name');
            if (nameInput) {
                nameInput.value = '';
                nameInput.focus();
            }
        }
    }

    /**
     * Close create collection modal
     */
    function closeCreateCollectionModal() {
        var modal = document.getElementById('create-collection-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Handle collection option click
     */
    function handleCollectionOptionClick(e) {
        var btn = e.currentTarget;
        var collectionId = parseInt(btn.getAttribute('data-collection-id'), 10);

        addToCollection(collectionId);
    }

    /**
     * Add recipe to collection
     */
    function addToCollection(collectionId) {
        Cookie.ajax.post('/api/collections/' + collectionId + '/recipes/', { recipe_id: recipeId }, function(err) {
            if (err) {
                if (err.message && err.message.indexOf('already') !== -1) {
                    Cookie.toast.error('Recipe already in collection');
                } else {
                    Cookie.toast.error('Failed to add to collection');
                }
                return;
            }
            closeCollectionModal();
            Cookie.toast.success('Added to collection');
        });
    }

    /**
     * Handle create collection form submit
     */
    function handleCreateCollection(e) {
        e.preventDefault();

        var nameInput = document.getElementById('collection-name');
        var name = nameInput ? nameInput.value.trim() : '';

        if (!name) {
            Cookie.toast.error('Please enter a collection name');
            return;
        }

        // Create collection then add recipe
        Cookie.ajax.post('/api/collections/', { name: name }, function(err, collection) {
            if (err) {
                Cookie.toast.error('Failed to create collection');
                return;
            }

            // Add recipe to new collection
            Cookie.ajax.post('/api/collections/' + collection.id + '/recipes/', { recipe_id: recipeId }, function(err2) {
                if (err2) {
                    Cookie.toast.error('Collection created but failed to add recipe');
                    closeCreateCollectionModal();
                    return;
                }

                closeCreateCollectionModal();
                Cookie.toast.success('Created collection and added recipe');

                // Add new collection to the list in the modal
                var collectionList = document.querySelector('.collection-list');
                if (collectionList) {
                    var newBtn = document.createElement('button');
                    newBtn.type = 'button';
                    newBtn.className = 'collection-option';
                    newBtn.setAttribute('data-collection-id', collection.id);
                    newBtn.textContent = collection.name;
                    newBtn.addEventListener('click', handleCollectionOptionClick);
                    collectionList.appendChild(newBtn);
                }
            });
        });
    }

    /**
     * Handle cook button click
     */
    function handleCookClick() {
        // Navigate to play mode (to be implemented in Session B)
        window.location.href = '/legacy/recipe/' + recipeId + '/play/';
    }

    /**
     * Adjust servings
     */
    function adjustServings(delta) {
        var newServings = Math.max(1, currentServings + delta);
        if (newServings === currentServings) return;

        currentServings = newServings;
        updateServingDisplay();
        updateServingButtons();

        // TODO: In Phase 8, call AI API to adjust ingredient quantities
        Cookie.toast.info('Serving adjustment will be AI-powered in Phase 8');
    }

    /**
     * Update serving display
     */
    function updateServingDisplay() {
        var valueEl = document.querySelector('.serving-value');
        if (valueEl) {
            valueEl.textContent = currentServings;
        }
    }

    /**
     * Update serving buttons (enable/disable)
     */
    function updateServingButtons() {
        var decreaseBtn = document.querySelector('.serving-decrease');
        if (decreaseBtn) {
            decreaseBtn.disabled = currentServings <= 1;
        }
    }

    /**
     * Handle remix button click
     */
    function handleRemixClick() {
        var modal = document.getElementById('remix-modal');
        if (modal) {
            modal.classList.remove('hidden');
            resetRemixModal();
            loadRemixSuggestions();
        }
    }

    /**
     * Close remix modal
     */
    function closeRemixModal() {
        if (isCreatingRemix) return;

        var modal = document.getElementById('remix-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Reset remix modal state
     */
    function resetRemixModal() {
        selectedRemixSuggestion = null;
        remixSuggestions = [];
        isCreatingRemix = false;

        var customInput = document.getElementById('remix-custom-input');
        if (customInput) {
            customInput.value = '';
        }

        updateRemixCreateButton();
    }

    /**
     * Load remix suggestions from API
     */
    function loadRemixSuggestions() {
        var suggestionsContainer = document.getElementById('remix-suggestions');
        if (!suggestionsContainer) return;

        // Show loading state
        suggestionsContainer.innerHTML = '<div class="remix-loading"><div class="spinner"></div><span>Generating suggestions...</span></div>';

        Cookie.ajax.post('/api/ai/remix-suggestions', { recipe_id: recipeId }, function(err, response) {
            if (err) {
                suggestionsContainer.innerHTML = '<p class="remix-error">Failed to load suggestions</p>';
                Cookie.toast.error('Failed to load suggestions');
                return;
            }

            remixSuggestions = response.suggestions || [];
            renderRemixSuggestions();
        });
    }

    /**
     * Render remix suggestions as chips
     */
    function renderRemixSuggestions() {
        var suggestionsContainer = document.getElementById('remix-suggestions');
        if (!suggestionsContainer) return;

        if (remixSuggestions.length === 0) {
            suggestionsContainer.innerHTML = '<p class="remix-error">No suggestions available</p>';
            return;
        }

        var html = '';
        for (var i = 0; i < remixSuggestions.length; i++) {
            var suggestion = remixSuggestions[i];
            html += '<button type="button" class="remix-chip" data-suggestion="' + escapeHtml(suggestion) + '">' + escapeHtml(suggestion) + '</button>';
        }
        suggestionsContainer.innerHTML = html;

        // Add click listeners
        var chips = suggestionsContainer.querySelectorAll('.remix-chip');
        for (var j = 0; j < chips.length; j++) {
            chips[j].addEventListener('click', handleRemixChipClick);
        }
    }

    /**
     * Handle remix chip click
     */
    function handleRemixChipClick(e) {
        var chip = e.currentTarget;
        var suggestion = chip.getAttribute('data-suggestion');

        // Toggle selection
        if (selectedRemixSuggestion === suggestion) {
            selectedRemixSuggestion = null;
            chip.classList.remove('active');
        } else {
            // Deselect previous
            var prevActive = document.querySelector('.remix-chip.active');
            if (prevActive) {
                prevActive.classList.remove('active');
            }

            selectedRemixSuggestion = suggestion;
            chip.classList.add('active');

            // Clear custom input when selecting a chip
            var customInput = document.getElementById('remix-custom-input');
            if (customInput) {
                customInput.value = '';
            }
        }

        updateRemixCreateButton();
    }

    /**
     * Handle remix custom input change
     */
    function handleRemixCustomInput() {
        var customInput = document.getElementById('remix-custom-input');
        if (customInput && customInput.value.trim()) {
            // Deselect any chip
            selectedRemixSuggestion = null;
            var activeChip = document.querySelector('.remix-chip.active');
            if (activeChip) {
                activeChip.classList.remove('active');
            }
        }
        updateRemixCreateButton();
    }

    /**
     * Get current remix modification
     */
    function getRemixModification() {
        var customInput = document.getElementById('remix-custom-input');
        if (customInput && customInput.value.trim()) {
            return customInput.value.trim();
        }
        return selectedRemixSuggestion;
    }

    /**
     * Update remix create button state
     */
    function updateRemixCreateButton() {
        var createBtn = document.getElementById('remix-create-btn');
        if (createBtn) {
            var modification = getRemixModification();
            createBtn.disabled = !modification || isCreatingRemix;
        }
    }

    /**
     * Handle remix create button click
     */
    function handleRemixCreate() {
        var modification = getRemixModification();
        if (!modification || isCreatingRemix) return;

        var modal = document.getElementById('remix-modal');
        var profileId = modal ? parseInt(modal.getAttribute('data-profile-id'), 10) : null;
        if (!profileId) {
            Cookie.toast.error('Profile not found');
            return;
        }

        isCreatingRemix = true;
        updateRemixCreateButton();

        // Update button text
        var btnText = document.getElementById('remix-btn-text');
        if (btnText) {
            btnText.textContent = 'Creating Remix...';
        }

        Cookie.ajax.post('/api/ai/remix', {
            recipe_id: recipeId,
            modification: modification,
            profile_id: profileId
        }, function(err, response) {
            isCreatingRemix = false;

            if (err) {
                updateRemixCreateButton();
                if (btnText) {
                    btnText.textContent = 'Create Remix';
                }
                Cookie.toast.error('Failed to create remix');
                return;
            }

            Cookie.toast.success('Created "' + response.title + '"');
            closeRemixModal();

            // Navigate to new recipe
            window.location.href = '/legacy/recipe/' + response.id + '/';
        });
    }

    /**
     * Escape HTML characters
     */
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.detail.init);
    } else {
        Cookie.pages.detail.init();
    }
})();
