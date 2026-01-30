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
        state.selectedRemixSuggestion = null;
        state.remixSuggestions = [];
        state.isCreatingRemix = false;

        var customInput = document.getElementById('remix-custom-input');
        if (customInput) {
            customInput.value = '';
        }

        updateRemixCreateButton();
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

        if (state.selectedRemixSuggestion === suggestion) {
            state.selectedRemixSuggestion = null;
            chip.classList.remove('active');
        } else {
            var prevActive = document.querySelector('.remix-chip.active');
            if (prevActive) {
                prevActive.classList.remove('active');
            }

            state.selectedRemixSuggestion = suggestion;
            chip.classList.add('active');

            var customInput = document.getElementById('remix-custom-input');
            if (customInput) {
                customInput.value = '';
            }
        }

        updateRemixCreateButton();
    }

    function handleRemixCustomInput() {
        var state = Cookie.pages.detail.getState();
        var customInput = document.getElementById('remix-custom-input');
        if (customInput && customInput.value.trim()) {
            state.selectedRemixSuggestion = null;
            var activeChip = document.querySelector('.remix-chip.active');
            if (activeChip) {
                activeChip.classList.remove('active');
            }
        }
        updateRemixCreateButton();
    }

    function getRemixModification() {
        var state = Cookie.pages.detail.getState();
        var customInput = document.getElementById('remix-custom-input');
        if (customInput && customInput.value.trim()) {
            return customInput.value.trim();
        }
        return state.selectedRemixSuggestion;
    }

    function updateRemixCreateButton() {
        var state = Cookie.pages.detail.getState();
        var createBtn = document.getElementById('remix-create-btn');
        if (createBtn) {
            var modification = getRemixModification();
            createBtn.disabled = !modification || state.isCreatingRemix;
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
