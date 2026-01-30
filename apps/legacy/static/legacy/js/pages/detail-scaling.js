/**
 * Recipe Detail page - Scaling module (ES5, iOS 9 compatible)
 * Handles serving adjustment and ingredient/instruction scaling.
 */
(function() {
    'use strict';

    function init() {
        var servingAdjuster = document.querySelector('.serving-adjuster');
        if (servingAdjuster) {
            var state = Cookie.pages.detail.getState();
            state.originalServings = parseInt(servingAdjuster.getAttribute('data-original-servings'), 10);
            state.currentServings = state.originalServings;

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
    }

    function adjustServings(delta) {
        var state = Cookie.pages.detail.getState();
        if (state.isScaling) return;

        var newServings = Math.max(1, state.currentServings + delta);
        if (newServings === state.currentServings) return;

        state.currentServings = newServings;
        updateServingDisplay();
        updateServingButtons();

        if (newServings === state.originalServings) {
            state.scaledIngredients = null;
            state.scaledInstructions = null;
            state.scalingNotes = [];
            state.adjustedTimes = null;
            renderOriginalIngredients();
            renderOriginalTimes();
            return;
        }

        scaleIngredients(newServings);
    }

    function scaleIngredients(targetServings) {
        var state = Cookie.pages.detail.getState();

        if (!state.profileId) {
            Cookie.toast.error('Profile not found');
            return;
        }

        state.isScaling = true;
        updateServingButtons();
        updateServingDisplay();

        Cookie.ajax.post('/api/ai/scale', {
            recipe_id: state.recipeId,
            target_servings: targetServings,
            profile_id: state.profileId,
            unit_system: 'metric'
        }, function(err, response) {
            state.isScaling = false;
            updateServingButtons();
            updateServingDisplay();

            if (err) {
                Cookie.aiError.showError(err, 'Failed to scale ingredients');
                if (Cookie.aiError.shouldHideFeatures(err)) {
                    Cookie.aiError.hideAIFeatures();
                }
                state.currentServings = state.originalServings;
                updateServingDisplay();
                return;
            }

            state.scaledIngredients = response.ingredients;
            state.scaledInstructions = response.instructions || [];
            state.scalingNotes = response.notes || [];
            state.adjustedTimes = {
                prep: response.prep_time_adjusted,
                cook: response.cook_time_adjusted,
                total: response.total_time_adjusted
            };
            renderScaledIngredients();
            renderScaledInstructions();
            renderAdjustedTimes();

            if (state.scalingNotes.length > 0) {
                Cookie.toast.info(state.scalingNotes[0]);
            }
        });
    }

    function renderOriginalIngredients() {
        var notesContainer = document.getElementById('scaling-notes');
        if (notesContainer) {
            notesContainer.classList.add('hidden');
        }

        var ingredientItems = document.querySelectorAll('.ingredient-item');
        for (var i = 0; i < ingredientItems.length; i++) {
            ingredientItems[i].classList.remove('scaled');
        }

        var originalTexts = document.querySelectorAll('.ingredient-text-original');
        var scaledTexts = document.querySelectorAll('.ingredient-text-scaled');

        for (var j = 0; j < originalTexts.length; j++) {
            originalTexts[j].classList.remove('hidden');
        }
        for (var k = 0; k < scaledTexts.length; k++) {
            scaledTexts[k].classList.add('hidden');
        }

        renderOriginalInstructions();
    }

    function renderOriginalInstructions() {
        var instructionItems = document.querySelectorAll('.instruction-item');
        for (var i = 0; i < instructionItems.length; i++) {
            instructionItems[i].classList.remove('scaled');
        }

        var originalTexts = document.querySelectorAll('.instruction-text-original');
        var scaledTexts = document.querySelectorAll('.instruction-text-scaled');

        for (var j = 0; j < originalTexts.length; j++) {
            originalTexts[j].classList.remove('hidden');
        }
        for (var k = 0; k < scaledTexts.length; k++) {
            scaledTexts[k].classList.add('hidden');
        }

        var indicator = document.querySelector('.instructions-scaled-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }

    function renderScaledInstructions() {
        var state = Cookie.pages.detail.getState();
        if (!state.scaledInstructions || state.scaledInstructions.length === 0) return;

        var instructionItems = document.querySelectorAll('.instruction-item');

        for (var i = 0; i < instructionItems.length && i < state.scaledInstructions.length; i++) {
            var item = instructionItems[i];
            var textEl = item.querySelector('.instruction-text');

            if (textEl) {
                if (!textEl.classList.contains('has-scaled')) {
                    textEl.classList.add('has-scaled', 'instruction-text-original');

                    var scaledEl = document.createElement('p');
                    scaledEl.className = 'instruction-text instruction-text-scaled hidden';
                    textEl.parentNode.insertBefore(scaledEl, textEl.nextSibling);
                }

                var scaledTextEl = item.querySelector('.instruction-text-scaled');
                if (scaledTextEl) {
                    scaledTextEl.textContent = state.scaledInstructions[i];
                    scaledTextEl.classList.remove('hidden');
                }

                var origTextEl = item.querySelector('.instruction-text-original');
                if (origTextEl) {
                    origTextEl.classList.add('hidden');
                }

                item.classList.add('scaled');
            }
        }

        var tabContent = document.getElementById('tab-instructions');
        if (tabContent) {
            var indicator = tabContent.querySelector('.instructions-scaled-indicator');
            if (!indicator) {
                indicator = document.createElement('p');
                indicator.className = 'instructions-scaled-indicator scaled-notice';
                indicator.textContent = 'Instructions adjusted for ' + state.currentServings + ' servings';
                tabContent.insertBefore(indicator, tabContent.firstChild);
            } else {
                indicator.textContent = 'Instructions adjusted for ' + state.currentServings + ' servings';
                indicator.classList.remove('hidden');
            }
        }
    }

    function renderAdjustedTimes() {
        var state = Cookie.pages.detail.getState();
        if (!state.adjustedTimes) return;

        var timeTypes = ['prep', 'cook', 'total'];
        for (var i = 0; i < timeTypes.length; i++) {
            var type = timeTypes[i];
            var adjusted = state.adjustedTimes[type];
            if (!adjusted) continue;

            var el = document.querySelector('[data-time-type="' + type + '"]');
            if (el) {
                var valueEl = el.querySelector('.time-value');
                if (valueEl) {
                    var originalMinutesAttr = el.getAttribute('data-original-minutes');
                    var originalMinutes = originalMinutesAttr ? parseInt(originalMinutesAttr, 10) : null;
                    var adjustedMinutes = parseInt(adjusted, 10);
                    var adjustedFormatted = Cookie.utils.formatTime(adjustedMinutes);

                    var timeChanged = (originalMinutes !== null) && (adjustedMinutes !== originalMinutes);

                    if (timeChanged) {
                        var originalFormatted = Cookie.utils.formatTime(originalMinutes);
                        valueEl.innerHTML = adjustedFormatted + ' <span class="time-was">(was ' + originalFormatted + ')</span>';
                        valueEl.classList.add('time-adjusted');
                    } else {
                        valueEl.textContent = adjustedFormatted;
                        valueEl.classList.remove('time-adjusted');
                    }
                }
            }
        }
    }

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

    function renderScaledIngredients() {
        var state = Cookie.pages.detail.getState();
        if (!state.scaledIngredients) return;

        var ingredientItems = document.querySelectorAll('.ingredient-item');

        for (var i = 0; i < ingredientItems.length && i < state.scaledIngredients.length; i++) {
            var item = ingredientItems[i];
            var textEl = item.querySelector('.ingredient-text');

            if (textEl) {
                if (!textEl.classList.contains('has-scaled')) {
                    textEl.classList.add('has-scaled', 'ingredient-text-original');

                    var scaledEl = document.createElement('span');
                    scaledEl.className = 'ingredient-text-scaled hidden';
                    textEl.parentNode.insertBefore(scaledEl, textEl.nextSibling);
                }

                var scaledTextEl = item.querySelector('.ingredient-text-scaled');
                if (scaledTextEl) {
                    scaledTextEl.textContent = state.scaledIngredients[i];
                    scaledTextEl.classList.remove('hidden');
                }

                var origTextEl = item.querySelector('.ingredient-text-original');
                if (origTextEl) {
                    origTextEl.classList.add('hidden');
                }

                item.classList.add('scaled');
            }
        }

        renderScalingNotes();
    }

    function renderScalingNotes() {
        var state = Cookie.pages.detail.getState();
        var notesContainer = document.getElementById('scaling-notes');
        var tabTips = document.getElementById('tab-tips');

        if (!tabTips) return;

        if (!notesContainer) {
            notesContainer = document.createElement('div');
            notesContainer.id = 'scaling-notes';
            notesContainer.className = 'scaling-notes';
            var tipsContent = document.getElementById('tips-content');
            if (tipsContent) {
                tipsContent.insertBefore(notesContainer, tipsContent.firstChild);
            }
        }

        if (state.scalingNotes.length > 0) {
            var notesHtml = '<h4 class="scaling-notes-title"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg> Scaling Notes</h4><ul class="scaling-notes-list">';
            for (var j = 0; j < state.scalingNotes.length; j++) {
                notesHtml += '<li>' + Cookie.utils.escapeHtml(state.scalingNotes[j]) + '</li>';
            }
            notesHtml += '</ul>';
            notesContainer.innerHTML = notesHtml;
            notesContainer.classList.remove('hidden');
        } else {
            notesContainer.classList.add('hidden');
        }
    }

    function updateServingDisplay() {
        var state = Cookie.pages.detail.getState();
        var valueEl = document.querySelector('.serving-value');
        if (valueEl) {
            if (state.isScaling) {
                valueEl.textContent = '...';
            } else {
                valueEl.textContent = state.currentServings;
            }
        }

        var adjuster = document.querySelector('.serving-adjuster');
        if (adjuster) {
            if (state.scaledIngredients && state.currentServings !== state.originalServings) {
                if (!adjuster.querySelector('.serving-scaled-indicator')) {
                    var indicator = document.createElement('span');
                    indicator.className = 'serving-scaled-indicator';
                    indicator.textContent = '(scaled from ' + state.originalServings + ')';
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

    function updateServingButtons() {
        var state = Cookie.pages.detail.getState();
        var decreaseBtn = document.querySelector('.serving-decrease');
        var increaseBtn = document.querySelector('.serving-increase');

        if (decreaseBtn) {
            decreaseBtn.disabled = state.currentServings <= 1 || state.isScaling;
        }
        if (increaseBtn) {
            increaseBtn.disabled = state.isScaling;
        }
    }

    // Register with core module
    Cookie.pages.detail.registerFeature('scaling', {
        init: init
    });
})();
