/**
 * Settings page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.settings = (function() {
    'use strict';

    // DOM Elements
    var apiKeyInput;
    var testKeyBtn;
    var saveKeyBtn;
    var testKeyText;
    var saveKeyText;
    var tabBtns;
    var tabApi;
    var tabPrompts;

    /**
     * Initialize the page
     */
    function init() {
        apiKeyInput = document.getElementById('api-key-input');
        testKeyBtn = document.getElementById('test-key-btn');
        saveKeyBtn = document.getElementById('save-key-btn');
        testKeyText = document.getElementById('test-key-text');
        saveKeyText = document.getElementById('save-key-text');
        tabBtns = document.querySelectorAll('.tab-toggle-btn');
        tabApi = document.getElementById('tab-api');
        tabPrompts = document.getElementById('tab-prompts');

        setupTabSwitching();
        setupApiKeyHandlers();
        setupPromptCards();
    }

    /**
     * Setup tab switching
     */
    function setupTabSwitching() {
        for (var i = 0; i < tabBtns.length; i++) {
            tabBtns[i].addEventListener('click', handleTabClick);
        }
    }

    /**
     * Handle tab click
     */
    function handleTabClick(e) {
        var btn = e.currentTarget;
        var tab = btn.getAttribute('data-tab');

        // Update active tab button
        for (var i = 0; i < tabBtns.length; i++) {
            tabBtns[i].classList.remove('active');
        }
        btn.classList.add('active');

        // Show/hide tab content
        if (tab === 'api') {
            tabApi.classList.remove('hidden');
            tabPrompts.classList.add('hidden');
        } else {
            tabApi.classList.add('hidden');
            tabPrompts.classList.remove('hidden');
        }
    }

    /**
     * Setup API key handlers
     */
    function setupApiKeyHandlers() {
        apiKeyInput.addEventListener('input', updateApiKeyButtons);
        testKeyBtn.addEventListener('click', handleTestKey);
        saveKeyBtn.addEventListener('click', handleSaveKey);
    }

    /**
     * Enable/disable API key buttons based on input
     */
    function updateApiKeyButtons() {
        var hasValue = apiKeyInput.value.trim().length > 0;
        testKeyBtn.disabled = !hasValue;
        saveKeyBtn.disabled = !hasValue;
    }

    /**
     * Handle test API key button click
     */
    function handleTestKey() {
        var apiKey = apiKeyInput.value.trim();
        if (!apiKey) return;

        testKeyBtn.disabled = true;
        testKeyText.textContent = 'Testing...';

        Cookie.ajax.post('/api/ai/test-api-key', { api_key: apiKey }, function(err, result) {
            testKeyBtn.disabled = false;
            testKeyText.textContent = 'Test Key';

            if (err) {
                Cookie.toast.error('Failed to test API key');
                return;
            }

            if (result.success) {
                Cookie.toast.success(result.message);
            } else {
                Cookie.toast.error(result.message);
            }
        });
    }

    /**
     * Handle save API key button click
     */
    function handleSaveKey() {
        var apiKey = apiKeyInput.value.trim();
        if (!apiKey) return;

        saveKeyBtn.disabled = true;
        saveKeyText.textContent = 'Saving...';

        Cookie.ajax.post('/api/ai/save-api-key', { api_key: apiKey }, function(err, result) {
            saveKeyBtn.disabled = false;
            saveKeyText.textContent = 'Save Key';

            if (err) {
                Cookie.toast.error('Failed to save API key');
                return;
            }

            if (result.success) {
                Cookie.toast.success(result.message);
                apiKeyInput.value = '';
                // Reload page to update status
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            } else {
                Cookie.toast.error(result.message);
            }
        });
    }

    /**
     * Setup prompt card handlers
     */
    function setupPromptCards() {
        var promptCards = document.querySelectorAll('.prompt-card');

        for (var i = 0; i < promptCards.length; i++) {
            setupPromptCard(promptCards[i]);
        }
    }

    /**
     * Setup a single prompt card
     */
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

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.settings.init);
    } else {
        Cookie.pages.settings.init();
    }
})();
