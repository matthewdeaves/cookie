/**
 * Recipe Detail page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.detail = (function() {
    'use strict';

    var recipeId;
    var profileId;
    var currentServings;
    var originalServings;
    var selectedRemixSuggestion = null;
    var remixSuggestions = [];
    var isCreatingRemix = false;
    var isScaling = false;
    var isGeneratingTips = false;
    var scaledIngredients = null;
    var scaledInstructions = null;
    var scalingNotes = [];
    var adjustedTimes = null;  // {prep: int|null, cook: int|null, total: int|null}

    // Tips polling state
    var tipsPollingState = {
        isPolling: false,
        pollInterval: null,
        pollStartTime: null
    };
    var TIPS_POLL_INTERVAL = 3000;  // 3 seconds
    var TIPS_MAX_POLL_DURATION = 30000;  // 30 seconds
    var TIPS_RECENT_THRESHOLD = 60000;  // 60 seconds

    /**
     * Initialize the page
     */
    function init() {
        var pageEl = document.querySelector('[data-page="recipe-detail"]');
        if (!pageEl) return;

        recipeId = parseInt(pageEl.getAttribute('data-recipe-id'), 10);
        profileId = parseInt(pageEl.getAttribute('data-profile-id'), 10);

        setupEventListeners();

        // Check if we should poll for tips (recently imported recipe with no tips)
        var scrapedAt = pageEl.getAttribute('data-scraped-at');
        var hasTips = pageEl.getAttribute('data-has-tips') === 'true';

        if (scrapedAt && !hasTips) {
            // iOS 9 Safari compatible date parsing
            // Convert "2026-01-09T09:18:29.135626+00:00" to Safari-parseable format
            var scrapedDate = new Date(scrapedAt
                .replace('T', ' ')              // Replace T with space
                .replace(/\.\d+/, '')           // Remove microseconds (.135626)
                .replace(/[+-]\d{2}:\d{2}$/, '') // Remove timezone (+00:00 or -05:00)
                .replace('Z', '')               // Remove Z suffix if present
                .replace(/-/g, '/'));           // Convert dashes to slashes for Safari
            var recipeAge = Date.now() - scrapedDate.getTime();

            if (!isNaN(recipeAge) && recipeAge < TIPS_RECENT_THRESHOLD) {
                startTipsPolling();
            }
        }
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

        // Generate tips button
        var generateTipsBtn = document.getElementById('generate-tips-btn');
        if (generateTipsBtn) {
            generateTipsBtn.addEventListener('click', function() {
                handleGenerateTips(false);
            });
        }

        // Regenerate tips button
        var regenerateTipsBtn = document.getElementById('regenerate-tips-btn');
        if (regenerateTipsBtn) {
            regenerateTipsBtn.addEventListener('click', function() {
                handleGenerateTips(true);
            });
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

        // QA-046: Auto-generate tips when viewing Tips tab for old recipes without tips
        if (tabName === 'tips') {
            var pageEl = document.querySelector('[data-page="recipe-detail"]');
            var aiAvailable = pageEl && pageEl.getAttribute('data-ai-available') === 'true';
            var hasTips = document.querySelectorAll('.tips-list .tip-item').length > 0;

            if (aiAvailable && !hasTips && !isGeneratingTips && !tipsPollingState.isPolling) {
                handleGenerateTips(false);
            }
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
        if (isScaling) return;

        var newServings = Math.max(1, currentServings + delta);
        if (newServings === currentServings) return;

        currentServings = newServings;
        updateServingDisplay();
        updateServingButtons();

        // If returning to original, reset scaled data
        if (newServings === originalServings) {
            scaledIngredients = null;
            scaledInstructions = null;
            scalingNotes = [];
            adjustedTimes = null;
            renderOriginalIngredients();
            renderOriginalTimes();
            return;
        }

        // Call AI API to scale ingredients
        scaleIngredients(newServings);
    }

    /**
     * Scale ingredients via AI API
     */
    function scaleIngredients(targetServings) {
        if (!profileId) {
            Cookie.toast.error('Profile not found');
            return;
        }

        isScaling = true;
        updateServingButtons();
        updateServingDisplay();

        Cookie.ajax.post('/api/ai/scale', {
            recipe_id: recipeId,
            target_servings: targetServings,
            profile_id: profileId,
            unit_system: 'metric'
        }, function(err, response) {
            isScaling = false;
            updateServingButtons();
            updateServingDisplay();

            if (err) {
                Cookie.toast.error('Failed to scale ingredients');
                // Revert to original
                currentServings = originalServings;
                updateServingDisplay();
                return;
            }

            scaledIngredients = response.ingredients;
            scaledInstructions = response.instructions || [];
            scalingNotes = response.notes || [];
            adjustedTimes = {
                prep: response.prep_time_adjusted,
                cook: response.cook_time_adjusted,
                total: response.total_time_adjusted
            };
            renderScaledIngredients();
            renderScaledInstructions();
            renderAdjustedTimes();

            if (scalingNotes.length > 0) {
                Cookie.toast.info(scalingNotes[0]);
            }
        });
    }

    /**
     * Render original ingredients
     */
    function renderOriginalIngredients() {
        // Hide scaling notes in tips tab
        var notesContainer = document.getElementById('scaling-notes');
        if (notesContainer) {
            notesContainer.classList.add('hidden');
        }

        // Show original ingredients by removing scaled class
        var ingredientItems = document.querySelectorAll('.ingredient-item');
        for (var i = 0; i < ingredientItems.length; i++) {
            ingredientItems[i].classList.remove('scaled');
        }

        // Show original text, hide scaled text
        var originalTexts = document.querySelectorAll('.ingredient-text-original');
        var scaledTexts = document.querySelectorAll('.ingredient-text-scaled');

        for (var j = 0; j < originalTexts.length; j++) {
            originalTexts[j].classList.remove('hidden');
        }
        for (var k = 0; k < scaledTexts.length; k++) {
            scaledTexts[k].classList.add('hidden');
        }

        // Also reset instructions
        renderOriginalInstructions();
    }

    /**
     * Render original instructions (reset from scaled)
     */
    function renderOriginalInstructions() {
        var instructionItems = document.querySelectorAll('.instruction-item');
        for (var i = 0; i < instructionItems.length; i++) {
            instructionItems[i].classList.remove('scaled');
        }

        // Show original text, hide scaled text
        var originalTexts = document.querySelectorAll('.instruction-text-original');
        var scaledTexts = document.querySelectorAll('.instruction-text-scaled');

        for (var j = 0; j < originalTexts.length; j++) {
            originalTexts[j].classList.remove('hidden');
        }
        for (var k = 0; k < scaledTexts.length; k++) {
            scaledTexts[k].classList.add('hidden');
        }

        // Hide scaled indicator
        var indicator = document.querySelector('.instructions-scaled-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }

    /**
     * Render scaled instructions
     */
    function renderScaledInstructions() {
        if (!scaledInstructions || scaledInstructions.length === 0) return;

        var instructionItems = document.querySelectorAll('.instruction-item');

        for (var i = 0; i < instructionItems.length && i < scaledInstructions.length; i++) {
            var item = instructionItems[i];
            var textEl = item.querySelector('.instruction-text');

            if (textEl) {
                // Store original if not already stored
                if (!textEl.classList.contains('has-scaled')) {
                    textEl.classList.add('has-scaled', 'instruction-text-original');

                    // Create scaled text element
                    var scaledEl = document.createElement('p');
                    scaledEl.className = 'instruction-text instruction-text-scaled hidden';
                    textEl.parentNode.insertBefore(scaledEl, textEl.nextSibling);
                }

                // Update scaled text
                var scaledTextEl = item.querySelector('.instruction-text-scaled');
                if (scaledTextEl) {
                    scaledTextEl.textContent = scaledInstructions[i];
                    scaledTextEl.classList.remove('hidden');
                }

                // Hide original
                var origTextEl = item.querySelector('.instruction-text-original');
                if (origTextEl) {
                    origTextEl.classList.add('hidden');
                }

                item.classList.add('scaled');
            }
        }

        // Show scaled indicator
        var tabContent = document.getElementById('tab-instructions');
        if (tabContent) {
            var indicator = tabContent.querySelector('.instructions-scaled-indicator');
            if (!indicator) {
                indicator = document.createElement('p');
                indicator.className = 'instructions-scaled-indicator scaled-notice';
                indicator.textContent = 'Instructions adjusted for ' + currentServings + ' servings';
                tabContent.insertBefore(indicator, tabContent.firstChild);
            } else {
                indicator.textContent = 'Instructions adjusted for ' + currentServings + ' servings';
                indicator.classList.remove('hidden');
            }
        }
    }

    /**
     * Format minutes as readable time
     */
    function formatTime(minutes) {
        if (!minutes) return null;
        if (minutes < 60) return minutes + ' min';
        var hours = Math.floor(minutes / 60);
        var mins = minutes % 60;
        return mins > 0 ? hours + 'h ' + mins + 'm' : hours + 'h';
    }

    /**
     * Render adjusted cooking times
     */
    function renderAdjustedTimes() {
        if (!adjustedTimes) return;

        var timeTypes = ['prep', 'cook', 'total'];
        for (var i = 0; i < timeTypes.length; i++) {
            var type = timeTypes[i];
            var adjusted = adjustedTimes[type];
            if (!adjusted) continue;

            var el = document.querySelector('[data-time-type="' + type + '"]');
            if (el) {
                var valueEl = el.querySelector('.time-value');
                if (valueEl) {
                    // Get original minutes from data attribute (set in template)
                    var originalMinutesAttr = el.getAttribute('data-original-minutes');
                    var originalMinutes = originalMinutesAttr ? parseInt(originalMinutesAttr, 10) : null;
                    var adjustedMinutes = parseInt(adjusted, 10);
                    var adjustedFormatted = formatTime(adjustedMinutes);

                    // Only show "(was X)" if time actually changed
                    // Compare integers if we have original minutes, otherwise times are equal (no attr = stale cache)
                    var timeChanged = (originalMinutes !== null) && (adjustedMinutes !== originalMinutes);

                    if (timeChanged) {
                        var originalFormatted = formatTime(originalMinutes);
                        valueEl.innerHTML = adjustedFormatted + ' <span class="time-was">(was ' + originalFormatted + ')</span>';
                        valueEl.classList.add('time-adjusted');
                    } else {
                        // Time unchanged - just show the value, no "(was X)"
                        valueEl.textContent = adjustedFormatted;
                        valueEl.classList.remove('time-adjusted');
                    }
                }
            }
        }
    }

    /**
     * Render original cooking times
     */
    function renderOriginalTimes() {
        var timeTypes = ['prep', 'cook', 'total'];
        for (var i = 0; i < timeTypes.length; i++) {
            var type = timeTypes[i];
            var el = document.querySelector('[data-time-type="' + type + '"]');
            if (el) {
                var valueEl = el.querySelector('.time-value');
                if (valueEl && valueEl.getAttribute('data-original')) {
                    valueEl.textContent = valueEl.getAttribute('data-original');
                    valueEl.classList.remove('time-adjusted');
                }
            }
        }
    }

    /**
     * Render scaled ingredients
     */
    function renderScaledIngredients() {
        if (!scaledIngredients) return;

        // Get ingredient list (flat list, not groups for now)
        var ingredientItems = document.querySelectorAll('.ingredient-item');

        for (var i = 0; i < ingredientItems.length && i < scaledIngredients.length; i++) {
            var item = ingredientItems[i];
            var textEl = item.querySelector('.ingredient-text');

            if (textEl) {
                // Store original if not already stored
                if (!textEl.classList.contains('has-scaled')) {
                    var originalText = textEl.textContent;
                    textEl.classList.add('has-scaled', 'ingredient-text-original');

                    // Create scaled text element
                    var scaledEl = document.createElement('span');
                    scaledEl.className = 'ingredient-text-scaled hidden';
                    textEl.parentNode.insertBefore(scaledEl, textEl.nextSibling);
                }

                // Update scaled text
                var scaledTextEl = item.querySelector('.ingredient-text-scaled');
                if (scaledTextEl) {
                    scaledTextEl.textContent = scaledIngredients[i];
                    scaledTextEl.classList.remove('hidden');
                }

                // Hide original
                var origTextEl = item.querySelector('.ingredient-text-original');
                if (origTextEl) {
                    origTextEl.classList.add('hidden');
                }

                item.classList.add('scaled');
            }
        }

        // Show scaling notes in tips tab
        renderScalingNotes();
    }

    /**
     * Render scaling notes in tips tab
     */
    function renderScalingNotes() {
        var notesContainer = document.getElementById('scaling-notes');
        var tabTips = document.getElementById('tab-tips');

        if (!tabTips) return;

        // Create or update notes container in tips tab
        if (!notesContainer) {
            notesContainer = document.createElement('div');
            notesContainer.id = 'scaling-notes';
            notesContainer.className = 'scaling-notes';
            // Insert at the beginning of tips content
            var tipsContent = document.getElementById('tips-content');
            if (tipsContent) {
                tipsContent.insertBefore(notesContainer, tipsContent.firstChild);
            }
        }

        if (scalingNotes.length > 0) {
            var notesHtml = '<h4 class="scaling-notes-title"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg> Scaling Notes</h4><ul class="scaling-notes-list">';
            for (var j = 0; j < scalingNotes.length; j++) {
                notesHtml += '<li>' + escapeHtml(scalingNotes[j]) + '</li>';
            }
            notesHtml += '</ul>';
            notesContainer.innerHTML = notesHtml;
            notesContainer.classList.remove('hidden');
        } else {
            notesContainer.classList.add('hidden');
        }
    }

    /**
     * Update serving display
     */
    function updateServingDisplay() {
        var valueEl = document.querySelector('.serving-value');
        if (valueEl) {
            if (isScaling) {
                valueEl.textContent = '...';
            } else {
                valueEl.textContent = currentServings;
            }
        }

        // Show scaled indicator
        var adjuster = document.querySelector('.serving-adjuster');
        if (adjuster) {
            if (scaledIngredients && currentServings !== originalServings) {
                if (!adjuster.querySelector('.serving-scaled-indicator')) {
                    var indicator = document.createElement('span');
                    indicator.className = 'serving-scaled-indicator';
                    indicator.textContent = '(scaled from ' + originalServings + ')';
                    adjuster.appendChild(indicator);
                }
            } else {
                var existingIndicator = adjuster.querySelector('.serving-scaled-indicator');
                if (existingIndicator) {
                    existingIndicator.remove();
                }
            }
        }
    }

    /**
     * Update serving buttons (enable/disable)
     */
    function updateServingButtons() {
        var decreaseBtn = document.querySelector('.serving-decrease');
        var increaseBtn = document.querySelector('.serving-increase');

        if (decreaseBtn) {
            decreaseBtn.disabled = currentServings <= 1 || isScaling;
        }
        if (increaseBtn) {
            increaseBtn.disabled = isScaling;
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

    /**
     * Start polling for tips (for recently imported recipes)
     */
    function startTipsPolling() {
        if (tipsPollingState.isPolling) return;

        tipsPollingState.isPolling = true;
        tipsPollingState.pollStartTime = Date.now();

        // Show loading state with polling message
        var tipsContent = document.getElementById('tips-content');
        var tipsLoading = document.getElementById('tips-loading');
        var tipsSubtext = document.getElementById('tips-loading-subtext');

        if (tipsContent) {
            tipsContent.classList.add('hidden');
        }
        if (tipsLoading) {
            tipsLoading.classList.remove('hidden');
        }
        if (tipsSubtext) {
            tipsSubtext.classList.remove('hidden');
        }

        // Start polling interval
        tipsPollingState.pollInterval = setInterval(function() {
            var elapsed = Date.now() - tipsPollingState.pollStartTime;

            // Stop if we've been polling too long
            if (elapsed > TIPS_MAX_POLL_DURATION) {
                stopTipsPolling(true);
                return;
            }

            // Poll for recipe data
            Cookie.ajax.get('/api/recipes/' + recipeId + '/', function(error, data) {
                if (error) {
                    // Ignore errors, will retry on next interval
                    return;
                }

                if (data && data.ai_tips && data.ai_tips.length > 0) {
                    // Tips are ready! Render them
                    renderTips(data.ai_tips);
                    stopTipsPolling(false);
                }
            });
        }, TIPS_POLL_INTERVAL);
    }

    /**
     * Stop polling for tips
     */
    function stopTipsPolling(showEmptyState) {
        if (tipsPollingState.pollInterval) {
            clearInterval(tipsPollingState.pollInterval);
            tipsPollingState.pollInterval = null;
        }
        tipsPollingState.isPolling = false;

        var tipsLoading = document.getElementById('tips-loading');
        var tipsSubtext = document.getElementById('tips-loading-subtext');

        if (tipsLoading) {
            tipsLoading.classList.add('hidden');
        }
        if (tipsSubtext) {
            tipsSubtext.classList.add('hidden');
        }

        // If timed out, show the empty state
        if (showEmptyState) {
            var tipsContent = document.getElementById('tips-content');
            if (tipsContent) {
                tipsContent.classList.remove('hidden');
            }
        }
    }

    /**
     * Handle generate/regenerate tips button click
     */
    function handleGenerateTips(regenerate) {
        if (isGeneratingTips) return;

        isGeneratingTips = true;

        // Show loading state
        var tipsContent = document.getElementById('tips-content');
        var tipsLoading = document.getElementById('tips-loading');

        if (tipsContent) {
            tipsContent.classList.add('hidden');
        }
        if (tipsLoading) {
            tipsLoading.classList.remove('hidden');
        }

        Cookie.ajax.post('/api/ai/tips', {
            recipe_id: recipeId,
            regenerate: regenerate || false
        }, function(err, response) {
            isGeneratingTips = false;

            if (err) {
                // Show content again on error
                if (tipsContent) {
                    tipsContent.classList.remove('hidden');
                }
                if (tipsLoading) {
                    tipsLoading.classList.add('hidden');
                }
                Cookie.toast.error('Failed to generate tips');
                return;
            }

            // Render tips
            renderTips(response.tips);

            Cookie.toast.success(regenerate ? 'Tips regenerated!' : 'Tips generated!');
        });
    }

    /**
     * Render tips list
     */
    function renderTips(tips) {
        var tipsContent = document.getElementById('tips-content');
        var tipsLoading = document.getElementById('tips-loading');

        if (tipsLoading) {
            tipsLoading.classList.add('hidden');
        }

        if (!tipsContent) return;

        if (!tips || tips.length === 0) {
            tipsContent.innerHTML = '<p class="empty-text">No tips available for this recipe.</p>';
            tipsContent.classList.remove('hidden');
            return;
        }

        var html = '<ol class="tips-list">';
        for (var i = 0; i < tips.length; i++) {
            html += '<li class="tip-item">';
            html += '<span class="tip-number">' + (i + 1) + '</span>';
            html += '<p class="tip-text">' + escapeHtml(tips[i]) + '</p>';
            html += '</li>';
        }
        html += '</ol>';

        // Add regenerate button
        html += '<div class="tips-regenerate">';
        html += '<button type="button" id="regenerate-tips-btn" class="btn btn-secondary">Regenerate Tips</button>';
        html += '</div>';

        tipsContent.innerHTML = html;
        tipsContent.classList.remove('hidden');

        // Re-bind regenerate button event listener
        var regenerateBtn = document.getElementById('regenerate-tips-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', function() {
                handleGenerateTips(true);
            });
        }
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
