/**
 * Settings page - Prompts tab (ES5, iOS 9 compatible)
 * Handles AI prompt editing and configuration.
 */
(function() {
    'use strict';

    /**
     * Update prompt card UI after successful save
     */
    function updateCardAfterSave(card, data, closeEditFn) {
        var content = card.querySelector('.prompt-content');
        var promptTexts = content.querySelectorAll('.prompt-text');
        if (promptTexts[0]) promptTexts[0].textContent = data.systemPrompt;
        if (promptTexts[1]) promptTexts[1].textContent = data.userPromptTemplate;

        var modelBadge = card.querySelector('.model-badge');
        if (modelBadge) modelBadge.textContent = data.model;

        var promptName = card.querySelector('.prompt-name');
        var disabledBadge = card.querySelector('.prompt-disabled-badge');
        if (data.isActive) {
            if (disabledBadge) disabledBadge.remove();
        } else if (!disabledBadge) {
            var badge = document.createElement('span');
            badge.className = 'prompt-disabled-badge';
            badge.textContent = 'Disabled';
            promptName.appendChild(badge);
        }

        closeEditFn();
    }

    /**
     * Handle prompt save API call
     */
    function savePrompt(card, promptType, statusBtn, saveBtn, closeEditFn) {
        var data = {
            systemPrompt: card.querySelector('[data-field="system_prompt"]').value,
            userPromptTemplate: card.querySelector('[data-field="user_prompt_template"]').value,
            model: card.querySelector('[data-field="model"]').value,
            isActive: statusBtn.getAttribute('data-value') === 'true'
        };

        var saveBtnText = saveBtn.querySelector('.save-btn-text');
        saveBtn.disabled = true;
        saveBtnText.textContent = 'Saving...';

        Cookie.ajax.put('/api/ai/prompts/' + promptType, {
            system_prompt: data.systemPrompt,
            user_prompt_template: data.userPromptTemplate,
            model: data.model,
            is_active: data.isActive
        }, function(err) {
            saveBtn.disabled = false;
            saveBtnText.textContent = 'Save Changes';
            if (err) { Cookie.toast.error('Failed to save prompt'); return; }
            Cookie.toast.success('Prompt saved successfully');
            updateCardAfterSave(card, data, closeEditFn);
        });
    }

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

        function closeEdit() {
            isEditing = false;
            editForm.classList.add('hidden');
            expandBtn.classList.remove('hidden');
            editBtn.classList.remove('hidden');
            if (isExpanded) content.classList.remove('hidden');
        }

        expandBtn.addEventListener('click', function() {
            if (isEditing) return;
            isExpanded = !isExpanded;
            content.classList.toggle('hidden', !isExpanded);
            iconExpand.classList.toggle('hidden', isExpanded);
            iconCollapse.classList.toggle('hidden', !isExpanded);
        });

        editBtn.addEventListener('click', function() {
            isEditing = true;
            content.classList.add('hidden');
            editForm.classList.remove('hidden');
            expandBtn.classList.add('hidden');
            editBtn.classList.add('hidden');
        });

        cancelBtn.addEventListener('click', closeEdit);

        statusBtn.addEventListener('click', function() {
            var newValue = statusBtn.getAttribute('data-value') !== 'true';
            statusBtn.setAttribute('data-value', newValue ? 'true' : 'false');
            statusBtn.textContent = newValue ? 'Active' : 'Disabled';
            statusBtn.classList.toggle('btn-status-disabled', !newValue);
            statusBtn.classList.toggle('btn-status-active', newValue);
        });

        saveBtn.addEventListener('click', function() {
            savePrompt(card, promptType, statusBtn, saveBtn, closeEdit);
        });
    }

    Cookie.pages.settings.registerTab('prompts', { init: init });
})();
