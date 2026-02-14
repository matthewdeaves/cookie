/**
 * Recipe Detail page - Remix module (ES5, iOS 9 compatible)
 * Handles remix modal, suggestions, and creation.
 */
(function() {
    'use strict';

    function init() {
        setupRemixButton();
        setupRemixModal();
        setupRemixInputs();
    }

    function setupRemixButton() {
        var remixBtn = document.getElementById('remix-btn');
        if (remixBtn) {
            remixBtn.addEventListener('click', handleRemixClick);
        }
    }

    function handleRemixClick() {
        var modal = document.getElementById('remix-modal');
        if (modal) {
            modal.classList.remove('hidden');
            resetRemixModal();
            loadRemixSuggestions();
        }
    }

    function setupRemixModal() {
        var remixModalClose = document.getElementById('remix-modal-close');
        if (remixModalClose) {
            remixModalClose.addEventListener('click', closeRemixModal);
        }

        var remixModal = document.getElementById('remix-modal');
        if (remixModal) {
            remixModal.addEventListener('click', function(e) {
                if (e.target === remixModal) {
                    closeRemixModal();
                }
            });
        }
    }

    function closeRemixModal() {
        var state = Cookie.pages.detail.getState();
        if (state.isCreatingRemix) return;

        var modal = document.getElementById('remix-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function setupRemixInputs() {
        var remixCustomInput = document.getElementById('remix-custom-input');
        if (remixCustomInput) {
            remixCustomInput.addEventListener('input', handleRemixCustomInput);
        }

        var remixCreateBtn = document.getElementById('remix-create-btn');
        if (remixCreateBtn) {
            remixCreateBtn.addEventListener('click', handleRemixCreate);
        }
    }

    function resetRemixModal() {
        var state = Cookie.pages.detail.getState();
        state.selectedRemixSuggestions = [];
        state.remixSuggestions = [];
        state.isCreatingRemix = false;

        var customInput = document.getElementById('remix-custom-input');
        if (customInput) {
            customInput.value = '';
        }

        updateRemixCreateButton();
        updateSelectionCount();
    }

    function loadRemixSuggestions() {
        var state = Cookie.pages.detail.getState();
        var suggestionsContainer = document.getElementById('remix-suggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = '<div class="remix-loading"><div class="spinner"></div><span>Generating suggestions...</span></div>';

        Cookie.ajax.post('/api/ai/remix-suggestions', { recipe_id: state.recipeId }, function(err, response) {
            if (err) {
                var errorInfo = Cookie.aiError.handleError(err, 'Failed to load suggestions');
                suggestionsContainer.innerHTML = '<p class="remix-error">' + errorInfo.message + '</p>';
                Cookie.aiError.showError(err, 'Failed to load suggestions');
                if (Cookie.aiError.shouldHideFeatures(err)) {
                    closeRemixModal();
                    Cookie.aiError.hideAIFeatures();
                }
                return;
            }

            state.remixSuggestions = response.suggestions || [];
            renderRemixSuggestions();
        });
    }

    function renderRemixSuggestions() {
        var state = Cookie.pages.detail.getState();
        var suggestionsContainer = document.getElementById('remix-suggestions');
        if (!suggestionsContainer) return;

        if (state.remixSuggestions.length === 0) {
            suggestionsContainer.innerHTML = '<p class="remix-error">No suggestions available</p>';
            return;
        }

        var html = '';
        for (var i = 0; i < state.remixSuggestions.length; i++) {
            var suggestion = state.remixSuggestions[i];
            html += '<button type="button" class="remix-chip" data-suggestion="' + Cookie.utils.escapeHtml(suggestion) + '">' + Cookie.utils.escapeHtml(suggestion) + '</button>';
        }
        suggestionsContainer.innerHTML = html;

        var chips = suggestionsContainer.querySelectorAll('.remix-chip');
        for (var j = 0; j < chips.length; j++) {
            chips[j].addEventListener('click', handleRemixChipClick);
        }
    }

    function handleRemixChipClick(e) {
        var state = Cookie.pages.detail.getState();
        var chip = e.currentTarget;
        var suggestion = chip.getAttribute('data-suggestion');

        // Initialize array if needed
        if (!state.selectedRemixSuggestions) {
            state.selectedRemixSuggestions = [];
        }

        // Check if already selected
        var index = -1;
        for (var i = 0; i < state.selectedRemixSuggestions.length; i++) {
            if (state.selectedRemixSuggestions[i] === suggestion) {
                index = i;
                break;
            }
        }

        if (index !== -1) {
            // Remove if already selected
            state.selectedRemixSuggestions.splice(index, 1);
            chip.classList.remove('active');
        } else {
            // Add to selection (limit to 4)
            if (state.selectedRemixSuggestions.length >= 4) {
                Cookie.toast.info('You can select up to 4 modifications');
                return;
            }
            state.selectedRemixSuggestions.push(suggestion);
            chip.classList.add('active');

            // Clear custom input when selecting suggestions
            var customInput = document.getElementById('remix-custom-input');
            if (customInput) {
                customInput.value = '';
            }
        }

        updateRemixCreateButton();
        updateSelectionCount();
    }

    function handleRemixCustomInput() {
        var state = Cookie.pages.detail.getState();
        var customInput = document.getElementById('remix-custom-input');
        if (customInput && customInput.value.trim()) {
            // Clear all selected suggestions when typing custom input
            state.selectedRemixSuggestions = [];
            var activeChips = document.querySelectorAll('.remix-chip.active');
            for (var i = 0; i < activeChips.length; i++) {
                activeChips[i].classList.remove('active');
            }
            updateSelectionCount();
        }
        updateRemixCreateButton();
    }

    function getRemixModification() {
        var state = Cookie.pages.detail.getState();
        var customInput = document.getElementById('remix-custom-input');
        if (customInput && customInput.value.trim()) {
            return customInput.value.trim();
        }
        // Join multiple selections with " AND "
        if (state.selectedRemixSuggestions && state.selectedRemixSuggestions.length > 0) {
            if (state.selectedRemixSuggestions.length === 1) {
                return state.selectedRemixSuggestions[0];
            }
            return state.selectedRemixSuggestions.join(' AND ');
        }
        return null;
    }

    function updateSelectionCount() {
        var state = Cookie.pages.detail.getState();
        var countEl = document.getElementById('remix-selection-count');
        if (countEl) {
            var count = state.selectedRemixSuggestions ? state.selectedRemixSuggestions.length : 0;
            if (count > 0) {
                countEl.textContent = count + ' selected';
                countEl.classList.remove('hidden');
            } else {
                countEl.classList.add('hidden');
            }
        }
    }

    function updateRemixCreateButton() {
        var state = Cookie.pages.detail.getState();
        var createBtn = document.getElementById('remix-create-btn');
        if (createBtn) {
            var modification = getRemixModification();
            createBtn.disabled = !modification || state.isCreatingRemix;
        }

        // Update button text to show how many selected
        var btnText = document.getElementById('remix-btn-text');
        if (btnText && !state.isCreatingRemix) {
            var count = state.selectedRemixSuggestions ? state.selectedRemixSuggestions.length : 0;
            var customInput = document.getElementById('remix-custom-input');
            var hasCustom = customInput && customInput.value.trim();
            if (hasCustom) {
                btnText.textContent = 'Create Remix';
            } else if (count > 1) {
                btnText.textContent = 'Create Remix (' + count + ' mods)';
            } else {
                btnText.textContent = 'Create Remix';
            }
        }
    }

    function handleRemixCreate() {
        var state = Cookie.pages.detail.getState();
        var modification = getRemixModification();
        if (!modification || state.isCreatingRemix) return;

        var modal = document.getElementById('remix-modal');
        var profileId = modal ? parseInt(modal.getAttribute('data-profile-id'), 10) : null;
        if (!profileId) {
            Cookie.toast.error('Profile not found');
            return;
        }

        state.isCreatingRemix = true;
        updateRemixCreateButton();

        var btnText = document.getElementById('remix-btn-text');
        if (btnText) {
            btnText.textContent = 'Creating Remix...';
        }

        Cookie.ajax.post('/api/ai/remix', {
            recipe_id: state.recipeId,
            modification: modification,
            profile_id: profileId
        }, function(err, response) {
            state.isCreatingRemix = false;

            if (err) {
                updateRemixCreateButton();
                if (btnText) {
                    btnText.textContent = 'Create Remix';
                }
                Cookie.aiError.showError(err, 'Failed to create remix');
                if (Cookie.aiError.shouldHideFeatures(err)) {
                    closeRemixModal();
                    Cookie.aiError.hideAIFeatures();
                }
                return;
            }

            Cookie.toast.success('Created "' + response.title + '"');
            closeRemixModal();

            window.location.href = '/legacy/recipe/' + response.id + '/';
        });
    }

    // Register with core module
    Cookie.pages.detail.registerFeature('remix', {
        init: init
    });
})();
