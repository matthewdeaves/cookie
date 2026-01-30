/**
 * Settings page - Prompts tab (ES5, iOS 9 compatible)
 * Handles AI prompt editing and configuration.
 */
(function() {
    'use strict';

    function init() {
        var promptCards = document.querySelectorAll('.prompt-card');
        for (var i = 0; i < promptCards.length; i++) {
            setupPromptCard(promptCards[i]);
        }
    }

    function setupPromptCard(card) {
        var promptType = card.getAttribute('data-prompt-type');
        var content = card.querySelector('.prompt-content');
        var editForm = card.querySelector('.prompt-edit-form');
        var expandBtn = card.querySelector('[data-action="toggle-expand"]');
        var editBtn = card.querySelector('[data-action="edit"]');
        var cancelBtn = card.querySelector('[data-action="cancel"]');
        var saveBtn = card.querySelector('[data-action="save"]');
        var iconExpand = card.querySelector('.icon-expand');
        var iconCollapse = card.querySelector('.icon-collapse');
        var statusBtn = card.querySelector('.btn-status');

        var isExpanded = false;
        var isEditing = false;

        // Toggle expand
        expandBtn.addEventListener('click', function() {
            if (isEditing) return;

            isExpanded = !isExpanded;
            if (isExpanded) {
                content.classList.remove('hidden');
                iconExpand.classList.add('hidden');
                iconCollapse.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
                iconExpand.classList.remove('hidden');
                iconCollapse.classList.add('hidden');
            }
        });

        // Edit button
        editBtn.addEventListener('click', function() {
            isEditing = true;
            content.classList.add('hidden');
            editForm.classList.remove('hidden');
            expandBtn.classList.add('hidden');
            editBtn.classList.add('hidden');
        });

        // Cancel edit
        cancelBtn.addEventListener('click', function() {
            isEditing = false;
            editForm.classList.add('hidden');
            expandBtn.classList.remove('hidden');
            editBtn.classList.remove('hidden');
            if (isExpanded) {
                content.classList.remove('hidden');
            }
        });

        // Status toggle
        statusBtn.addEventListener('click', function() {
            var currentValue = statusBtn.getAttribute('data-value') === 'true';
            var newValue = !currentValue;

            statusBtn.setAttribute('data-value', newValue ? 'true' : 'false');
            statusBtn.textContent = newValue ? 'Active' : 'Disabled';

            if (newValue) {
                statusBtn.classList.remove('btn-status-disabled');
                statusBtn.classList.add('btn-status-active');
            } else {
                statusBtn.classList.remove('btn-status-active');
                statusBtn.classList.add('btn-status-disabled');
            }
        });

        // Save prompt
        saveBtn.addEventListener('click', function() {
            var systemPrompt = card.querySelector('[data-field="system_prompt"]').value;
            var userPromptTemplate = card.querySelector('[data-field="user_prompt_template"]').value;
            var model = card.querySelector('[data-field="model"]').value;
            var isActive = statusBtn.getAttribute('data-value') === 'true';

            var saveBtnText = saveBtn.querySelector('.save-btn-text');
            saveBtn.disabled = true;
            saveBtnText.textContent = 'Saving...';

            Cookie.ajax.put('/api/ai/prompts/' + promptType, {
                system_prompt: systemPrompt,
                user_prompt_template: userPromptTemplate,
                model: model,
                is_active: isActive
            }, function(err, result) {
                saveBtn.disabled = false;
                saveBtnText.textContent = 'Save Changes';

                if (err) {
                    Cookie.toast.error('Failed to save prompt');
                    return;
                }

                Cookie.toast.success('Prompt saved successfully');

                // Update the read-only view
                var promptTexts = content.querySelectorAll('.prompt-text');
                if (promptTexts[0]) promptTexts[0].textContent = systemPrompt;
                if (promptTexts[1]) promptTexts[1].textContent = userPromptTemplate;

                // Update the model badge
                var modelBadge = card.querySelector('.model-badge');
                if (modelBadge) modelBadge.textContent = model;

                // Update the disabled badge
                var promptName = card.querySelector('.prompt-name');
                var disabledBadge = card.querySelector('.prompt-disabled-badge');
                if (isActive) {
                    if (disabledBadge) disabledBadge.remove();
                } else {
                    if (!disabledBadge) {
                        var badge = document.createElement('span');
                        badge.className = 'prompt-disabled-badge';
                        badge.textContent = 'Disabled';
                        promptName.appendChild(badge);
                    }
                }

                // Close edit form
                isEditing = false;
                editForm.classList.add('hidden');
                expandBtn.classList.remove('hidden');
                editBtn.classList.remove('hidden');
                if (isExpanded) {
                    content.classList.remove('hidden');
                }
            });
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('prompts', {
        init: init
    });
})();
