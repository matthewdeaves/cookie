/**
 * Settings page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.settings = (function() {
    'use strict';

    // DOM Elements - General tab
    var apiKeyInput;
    var testKeyBtn;
    var saveKeyBtn;
    var testKeyText;
    var saveKeyText;

    // DOM Elements - Tabs
    var tabBtns;
    var tabGeneral;
    var tabPrompts;
    var tabSources;
    var tabSelectors;

    // DOM Elements - Sources tab
    var sourcesCounter;
    var sourcesList;
    var enableAllBtn;
    var disableAllBtn;

    // DOM Elements - Selectors tab
    var selectorsList;
    var testAllBtn;
    var testAllText;

    // DOM Elements - Users tab
    var tabUsers;
    var profilesList;
    var profileCount;
    var deleteModal;
    var deleteProfileInfo;
    var deleteDataSummary;
    var confirmDeleteBtn;
    var deleteBtnText;

    // DOM Elements - Danger Zone tab
    var tabDanger;
    var resetModalStep1;
    var resetModalStep2;
    var resetDataSummary;
    var resetConfirmInput;
    var confirmResetBtn;
    var resetBtnText;

    // Data
    var sources = [];
    var profiles = [];
    var currentProfileId = null;
    var pendingDeleteId = null;
    var resetPreview = null;

    /**
     * Initialize the page
     */
    function init() {
        // General tab elements
        apiKeyInput = document.getElementById('api-key-input');
        testKeyBtn = document.getElementById('test-key-btn');
        saveKeyBtn = document.getElementById('save-key-btn');
        testKeyText = document.getElementById('test-key-text');
        saveKeyText = document.getElementById('save-key-text');

        // Tab elements
        tabBtns = document.querySelectorAll('.tab-toggle-btn');
        tabGeneral = document.getElementById('tab-general');
        tabPrompts = document.getElementById('tab-prompts');
        tabSources = document.getElementById('tab-sources');
        tabSelectors = document.getElementById('tab-selectors');

        // Sources tab elements
        sourcesCounter = document.getElementById('sources-counter');
        sourcesList = document.getElementById('sources-list');
        enableAllBtn = document.getElementById('enable-all-btn');
        disableAllBtn = document.getElementById('disable-all-btn');

        // Selectors tab elements
        selectorsList = document.getElementById('selectors-list');
        testAllBtn = document.getElementById('test-all-btn');
        testAllText = document.getElementById('test-all-text');

        // Users tab elements
        tabUsers = document.getElementById('tab-users');
        profilesList = document.getElementById('profiles-list');
        profileCount = document.getElementById('profile-count');
        deleteModal = document.getElementById('delete-profile-modal');
        deleteProfileInfo = document.getElementById('delete-profile-info');
        deleteDataSummary = document.getElementById('delete-data-summary');
        confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        deleteBtnText = document.getElementById('delete-btn-text');

        // Danger Zone tab elements
        tabDanger = document.getElementById('tab-danger');
        resetModalStep1 = document.getElementById('reset-modal-step1');
        resetModalStep2 = document.getElementById('reset-modal-step2');
        resetDataSummary = document.getElementById('reset-data-summary');
        resetConfirmInput = document.getElementById('reset-confirm-input');
        confirmResetBtn = document.getElementById('confirm-reset-btn');
        resetBtnText = document.getElementById('reset-btn-text');

        // Get current profile ID from session (passed via data attribute)
        var pageElement = document.querySelector('[data-page="settings"]');
        if (pageElement && pageElement.getAttribute('data-profile-id')) {
            currentProfileId = parseInt(pageElement.getAttribute('data-profile-id'), 10);
        }

        setupTabSwitching();
        setupApiKeyHandlers();
        setupPromptCards();
        setupSourcesTab();
        setupSelectorsTab();
        setupDangerZoneTab();

        // Load sources data
        loadSources();
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

        // Hide all tabs
        tabGeneral.classList.add('hidden');
        tabPrompts.classList.add('hidden');
        tabSources.classList.add('hidden');
        tabSelectors.classList.add('hidden');
        tabUsers.classList.add('hidden');
        tabDanger.classList.add('hidden');

        // Show selected tab
        if (tab === 'general') {
            tabGeneral.classList.remove('hidden');
        } else if (tab === 'prompts') {
            tabPrompts.classList.remove('hidden');
        } else if (tab === 'sources') {
            tabSources.classList.remove('hidden');
        } else if (tab === 'selectors') {
            tabSelectors.classList.remove('hidden');
        } else if (tab === 'users') {
            tabUsers.classList.remove('hidden');
            // Load profiles when users tab is shown
            if (profiles.length === 0) {
                loadProfiles();
            }
        } else if (tab === 'danger') {
            tabDanger.classList.remove('hidden');
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

    /**
     * Setup sources tab handlers
     */
    function setupSourcesTab() {
        enableAllBtn.addEventListener('click', function() {
            bulkToggleSources(true);
        });

        disableAllBtn.addEventListener('click', function() {
            bulkToggleSources(false);
        });
    }

    /**
     * Load sources from API
     */
    function loadSources() {
        Cookie.ajax.get('/api/sources/', function(err, result) {
            if (err) {
                sourcesList.innerHTML = '<div class="error-placeholder">Failed to load sources</div>';
                selectorsList.innerHTML = '<div class="error-placeholder">Failed to load sources</div>';
                return;
            }

            sources = result;
            renderSources();
            renderSelectors();
            updateSourcesCounter();
        });
    }

    /**
     * Update sources counter
     */
    function updateSourcesCounter() {
        var enabled = 0;
        for (var i = 0; i < sources.length; i++) {
            if (sources[i].is_enabled) enabled++;
        }
        sourcesCounter.textContent = enabled + ' of ' + sources.length + ' sources currently enabled';
    }

    /**
     * Render sources list
     */
    function renderSources() {
        var html = '';

        for (var i = 0; i < sources.length; i++) {
            var source = sources[i];
            var enabledClass = source.is_enabled ? 'source-enabled' : 'source-disabled';
            var activeBadge = source.is_enabled ? '<span class="source-active-badge">Active</span>' : '';
            var toggleIcon = source.is_enabled
                ? '<svg class="toggle-icon toggle-on" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><rect x="1" y="5" width="22" height="14" rx="7" ry="7"></rect><circle cx="16" cy="12" r="4" fill="var(--background)"></circle></svg>'
                : '<svg class="toggle-icon toggle-off" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="5" width="22" height="14" rx="7" ry="7"></rect><circle cx="8" cy="12" r="3"></circle></svg>';

            html += '<div class="source-item ' + enabledClass + '" data-source-id="' + source.id + '">';
            html += '  <div class="source-info">';
            html += '    <div class="source-name-row">';
            html += '      <span class="source-name">' + escapeHtml(source.name) + '</span>';
            html += '      ' + activeBadge;
            html += '    </div>';
            html += '    <span class="source-host">' + escapeHtml(source.host) + '</span>';
            html += '  </div>';
            html += '  <button type="button" class="btn-toggle" data-action="toggle-source" data-source-id="' + source.id + '">';
            html += '    ' + toggleIcon;
            html += '  </button>';
            html += '</div>';
        }

        sourcesList.innerHTML = html;

        // Attach event listeners
        var toggleBtns = sourcesList.querySelectorAll('[data-action="toggle-source"]');
        for (var i = 0; i < toggleBtns.length; i++) {
            toggleBtns[i].addEventListener('click', handleToggleSource);
        }
    }

    /**
     * Handle toggle source click
     */
    function handleToggleSource(e) {
        var btn = e.currentTarget;
        var sourceId = parseInt(btn.getAttribute('data-source-id'), 10);

        btn.disabled = true;

        Cookie.ajax.post('/api/sources/' + sourceId + '/toggle/', {}, function(err, result) {
            btn.disabled = false;

            if (err) {
                Cookie.toast.error('Failed to toggle source');
                return;
            }

            // Update local data
            for (var i = 0; i < sources.length; i++) {
                if (sources[i].id === sourceId) {
                    sources[i].is_enabled = result.is_enabled;
                    break;
                }
            }

            renderSources();
            renderSelectors();
            updateSourcesCounter();
        });
    }

    /**
     * Bulk toggle sources
     */
    function bulkToggleSources(enable) {
        enableAllBtn.disabled = true;
        disableAllBtn.disabled = true;

        Cookie.ajax.post('/api/sources/bulk-toggle/', { enable: enable }, function(err, result) {
            enableAllBtn.disabled = false;
            disableAllBtn.disabled = false;

            if (err) {
                Cookie.toast.error('Failed to update sources');
                return;
            }

            // Update local data
            for (var i = 0; i < sources.length; i++) {
                sources[i].is_enabled = enable;
            }

            renderSources();
            renderSelectors();
            updateSourcesCounter();
            Cookie.toast.success(enable ? 'All sources enabled' : 'All sources disabled');
        });
    }

    /**
     * Setup selectors tab handlers
     */
    function setupSelectorsTab() {
        testAllBtn.addEventListener('click', handleTestAllSources);
    }

    /**
     * Render selectors list
     */
    function renderSelectors() {
        var html = '';

        for (var i = 0; i < sources.length; i++) {
            var source = sources[i];
            var status = getSourceStatus(source);
            var statusIcon = getStatusIcon(status);
            var lastTested = formatRelativeTime(source.last_validated_at);
            var failureWarning = source.consecutive_failures >= 3
                ? '<p class="selector-failure-warning">Failed ' + source.consecutive_failures + ' times - auto-disabled</p>'
                : '';

            html += '<div class="selector-item" data-source-id="' + source.id + '">';
            html += '  <div class="selector-header">';
            html += '    <div class="selector-info">';
            html += '      <div class="selector-name-row">';
            html += '        <span class="selector-name">' + escapeHtml(source.name) + '</span>';
            html += '        ' + statusIcon;
            html += '      </div>';
            html += '      <span class="selector-host">' + escapeHtml(source.host) + '</span>';
            html += '      ' + failureWarning;
            html += '    </div>';
            html += '    <div class="selector-actions">';
            html += '      <span class="selector-last-tested">Last tested: ' + lastTested + '</span>';
            html += '      <button type="button" class="btn btn-secondary btn-sm" data-action="test-source" data-source-id="' + source.id + '">';
            html += '        <span class="btn-icon-wrapper">';
            html += '          <svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
            html += '          <span class="test-btn-text">Test</span>';
            html += '        </span>';
            html += '      </button>';
            html += '    </div>';
            html += '  </div>';
            html += '  <div class="selector-field">';
            html += '    <label class="selector-label">CSS Selector</label>';
            html += '    <div class="selector-input-row" data-source-id="' + source.id + '">';
            html += '      <code class="selector-value">' + escapeHtml(source.result_selector || '(none)') + '</code>';
            html += '      <button type="button" class="btn btn-edit btn-sm" data-action="edit-selector" data-source-id="' + source.id + '">Edit</button>';
            html += '    </div>';
            html += '    <div class="selector-edit-row hidden" data-source-id="' + source.id + '">';
            html += '      <input type="text" class="input input-mono" value="' + escapeHtml(source.result_selector || '') + '" data-field="selector">';
            html += '      <button type="button" class="btn btn-secondary btn-sm" data-action="cancel-edit" data-source-id="' + source.id + '">Cancel</button>';
            html += '      <button type="button" class="btn btn-primary btn-sm" data-action="save-selector" data-source-id="' + source.id + '">Save</button>';
            html += '    </div>';
            html += '  </div>';
            html += '</div>';
        }

        selectorsList.innerHTML = html;

        // Attach event listeners
        var testBtns = selectorsList.querySelectorAll('[data-action="test-source"]');
        for (var i = 0; i < testBtns.length; i++) {
            testBtns[i].addEventListener('click', handleTestSource);
        }

        var editBtns = selectorsList.querySelectorAll('[data-action="edit-selector"]');
        for (var i = 0; i < editBtns.length; i++) {
            editBtns[i].addEventListener('click', handleEditSelector);
        }

        var cancelBtns = selectorsList.querySelectorAll('[data-action="cancel-edit"]');
        for (var i = 0; i < cancelBtns.length; i++) {
            cancelBtns[i].addEventListener('click', handleCancelEditSelector);
        }

        var saveBtns = selectorsList.querySelectorAll('[data-action="save-selector"]');
        for (var i = 0; i < saveBtns.length; i++) {
            saveBtns[i].addEventListener('click', handleSaveSelector);
        }
    }

    /**
     * Get source status
     */
    function getSourceStatus(source) {
        if (!source.last_validated_at) return 'untested';
        if (source.needs_attention || source.consecutive_failures >= 3) return 'broken';
        return 'working';
    }

    /**
     * Get status icon HTML
     */
    function getStatusIcon(status) {
        if (status === 'working') {
            return '<svg class="status-icon status-working" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
        } else if (status === 'broken') {
            return '<svg class="status-icon status-broken" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
        } else {
            return '<svg class="status-icon status-untested" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
        }
    }

    /**
     * Format relative time
     */
    function formatRelativeTime(dateStr) {
        if (!dateStr) return 'Never';
        var date = new Date(dateStr);
        var now = new Date();
        var diffMs = now.getTime() - date.getTime();
        var diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return diffMins + 'm ago';
        var diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return diffHours + 'h ago';
        var diffDays = Math.floor(diffHours / 24);
        return diffDays + 'd ago';
    }

    /**
     * Handle test source click
     */
    function handleTestSource(e) {
        var btn = e.currentTarget;
        var sourceId = parseInt(btn.getAttribute('data-source-id'), 10);
        var btnText = btn.querySelector('.test-btn-text');

        btn.disabled = true;
        btnText.textContent = 'Testing...';

        Cookie.ajax.post('/api/sources/' + sourceId + '/test/', {}, function(err, result) {
            btn.disabled = false;
            btnText.textContent = 'Test';

            if (err) {
                Cookie.toast.error('Failed to test source');
                return;
            }

            if (result.success) {
                Cookie.toast.success(result.message);
            } else {
                Cookie.toast.error(result.message);
            }

            // Reload sources to get updated status
            loadSources();
        });
    }

    /**
     * Handle test all sources click
     */
    function handleTestAllSources() {
        testAllBtn.disabled = true;
        testAllText.textContent = 'Testing...';

        Cookie.ajax.post('/api/sources/test-all/', {}, function(err, result) {
            testAllBtn.disabled = false;
            testAllText.textContent = 'Test All Sources';

            if (err) {
                Cookie.toast.error('Failed to test sources');
                return;
            }

            Cookie.toast.success('Tested ' + result.tested + ' sources: ' + result.passed + ' passed, ' + result.failed + ' failed');

            // Reload sources to get updated status
            loadSources();
        });
    }

    /**
     * Handle edit selector click
     */
    function handleEditSelector(e) {
        var sourceId = e.currentTarget.getAttribute('data-source-id');
        var inputRow = selectorsList.querySelector('.selector-input-row[data-source-id="' + sourceId + '"]');
        var editRow = selectorsList.querySelector('.selector-edit-row[data-source-id="' + sourceId + '"]');

        inputRow.classList.add('hidden');
        editRow.classList.remove('hidden');
    }

    /**
     * Handle cancel edit selector click
     */
    function handleCancelEditSelector(e) {
        var sourceId = e.currentTarget.getAttribute('data-source-id');
        var inputRow = selectorsList.querySelector('.selector-input-row[data-source-id="' + sourceId + '"]');
        var editRow = selectorsList.querySelector('.selector-edit-row[data-source-id="' + sourceId + '"]');

        editRow.classList.add('hidden');
        inputRow.classList.remove('hidden');
    }

    /**
     * Handle save selector click
     */
    function handleSaveSelector(e) {
        var btn = e.currentTarget;
        var sourceId = parseInt(btn.getAttribute('data-source-id'), 10);
        var editRow = selectorsList.querySelector('.selector-edit-row[data-source-id="' + sourceId + '"]');
        var input = editRow.querySelector('[data-field="selector"]');
        var newSelector = input.value;

        btn.disabled = true;
        btn.textContent = 'Saving...';

        Cookie.ajax.put('/api/sources/' + sourceId + '/selector/', { result_selector: newSelector }, function(err, result) {
            btn.disabled = false;
            btn.textContent = 'Save';

            if (err) {
                Cookie.toast.error('Failed to update selector');
                return;
            }

            Cookie.toast.success('Selector updated');

            // Update local data
            for (var i = 0; i < sources.length; i++) {
                if (sources[i].id === sourceId) {
                    sources[i].result_selector = newSelector;
                    break;
                }
            }

            renderSelectors();
        });
    }

    /**
     * Escape HTML special characters
     */
    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // ============================================
    // USER MANAGEMENT FUNCTIONS
    // ============================================

    /**
     * Load profiles from API
     */
    function loadProfiles() {
        Cookie.ajax.get('/api/profiles/', function(err, result) {
            if (err) {
                profilesList.innerHTML = '<div class="error-placeholder">Failed to load profiles</div>';
                return;
            }

            profiles = result;
            renderProfiles();
            updateProfileCount();
        });
    }

    /**
     * Update profile count display
     */
    function updateProfileCount() {
        profileCount.textContent = profiles.length + ' profile' + (profiles.length !== 1 ? 's' : '');
    }

    /**
     * Render profiles list
     */
    function renderProfiles() {
        var html = '';

        for (var i = 0; i < profiles.length; i++) {
            var profile = profiles[i];
            var isCurrent = profile.id === currentProfileId;
            var currentBadge = isCurrent ? '<span class="profile-current-badge">Current</span>' : '';
            var disabledAttr = isCurrent ? 'disabled' : '';
            var disabledClass = isCurrent ? 'btn-delete-disabled' : '';

            html += '<div class="profile-card" data-profile-id="' + profile.id + '">';
            html += '  <div class="profile-avatar" style="background-color: ' + escapeHtml(profile.avatar_color) + '"></div>';
            html += '  <div class="profile-info">';
            html += '    <div class="profile-name-row">';
            html += '      <span class="profile-name">' + escapeHtml(profile.name) + '</span>';
            html += '      ' + currentBadge;
            html += '    </div>';
            html += '    <span class="profile-meta">Created ' + formatDate(profile.created_at) + '</span>';
            html += '    <span class="profile-stats">';
            html += '      ' + profile.stats.favorites + ' favorites · ';
            html += '      ' + profile.stats.collections + ' collections · ';
            html += '      ' + profile.stats.remixes + ' remixes';
            html += '    </span>';
            html += '  </div>';
            html += '  <button type="button" class="btn-delete ' + disabledClass + '" ' + disabledAttr + ' data-action="delete-profile" data-profile-id="' + profile.id + '" title="' + (isCurrent ? 'Cannot delete current profile' : 'Delete profile') + '">';
            html += '    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">';
            html += '      <path d="M3 6h18"></path>';
            html += '      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>';
            html += '      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>';
            html += '    </svg>';
            html += '  </button>';
            html += '</div>';
        }

        profilesList.innerHTML = html;

        // Attach event listeners
        var deleteBtns = profilesList.querySelectorAll('[data-action="delete-profile"]');
        for (var i = 0; i < deleteBtns.length; i++) {
            deleteBtns[i].addEventListener('click', handleDeleteProfileClick);
        }
    }

    /**
     * Format date for display
     */
    function formatDate(dateStr) {
        if (!dateStr) return 'Unknown';
        var date = new Date(dateStr);
        return date.toLocaleDateString();
    }

    /**
     * Handle delete profile button click
     */
    function handleDeleteProfileClick(e) {
        var btn = e.currentTarget;
        if (btn.disabled) return;

        var profileId = parseInt(btn.getAttribute('data-profile-id'), 10);
        pendingDeleteId = profileId;

        // Fetch deletion preview
        Cookie.ajax.get('/api/profiles/' + profileId + '/deletion-preview/', function(err, preview) {
            if (err) {
                Cookie.toast.error('Failed to load profile info');
                pendingDeleteId = null;
                return;
            }

            renderDeleteModal(preview);
            deleteModal.classList.remove('hidden');
        });
    }

    /**
     * Render delete modal content
     */
    function renderDeleteModal(preview) {
        var profile = preview.profile;
        var data = preview.data_to_delete;

        // Profile info
        deleteProfileInfo.innerHTML = [
            '<div class="profile-avatar" style="background-color: ' + escapeHtml(profile.avatar_color) + '"></div>',
            '<div>',
            '  <div class="profile-name">' + escapeHtml(profile.name) + '</div>',
            '  <div class="profile-meta">Created ' + formatDate(profile.created_at) + '</div>',
            '</div>'
        ].join('');

        // Data summary
        var summaryItems = [];
        if (data.remixes > 0) {
            summaryItems.push(data.remixes + ' remixed recipe' + (data.remixes !== 1 ? 's' : '') +
                ' (' + data.remix_images + ' images)');
        }
        if (data.favorites > 0) {
            summaryItems.push(data.favorites + ' favorite' + (data.favorites !== 1 ? 's' : ''));
        }
        if (data.collections > 0) {
            summaryItems.push(data.collections + ' collection' + (data.collections !== 1 ? 's' : '') +
                ' (' + data.collection_items + ' items)');
        }
        if (data.view_history > 0) {
            summaryItems.push(data.view_history + ' view history entries');
        }
        if (data.scaling_cache > 0 || data.discover_cache > 0) {
            summaryItems.push('Cached AI data');
        }
        if (summaryItems.length === 0) {
            summaryItems.push('No associated data');
        }

        deleteDataSummary.innerHTML =
            '<div class="summary-title">Data to be deleted:</div>' +
            '<ul class="summary-list">' + summaryItems.map(function(item) {
                return '<li>' + item + '</li>';
            }).join('') + '</ul>';
    }

    /**
     * Close delete modal (exposed globally)
     */
    function closeDeleteModal() {
        deleteModal.classList.add('hidden');
        pendingDeleteId = null;
    }

    /**
     * Execute profile deletion (exposed globally)
     */
    function executeDeleteProfile() {
        if (!pendingDeleteId) return;

        confirmDeleteBtn.disabled = true;
        deleteBtnText.textContent = 'Deleting...';

        Cookie.ajax.delete('/api/profiles/' + pendingDeleteId + '/', function(err, result) {
            confirmDeleteBtn.disabled = false;
            deleteBtnText.textContent = 'Delete Profile';

            if (err) {
                Cookie.toast.error('Failed to delete profile');
                return;
            }

            Cookie.toast.success('Profile deleted successfully');

            // Remove from local data and re-render (before closing modal clears pendingDeleteId)
            var deletedId = pendingDeleteId;
            closeDeleteModal();

            profiles = profiles.filter(function(p) {
                return p.id !== deletedId;
            });
            renderProfiles();
            updateProfileCount();
        });
    }

    // Expose modal functions globally for onclick handlers
    window.closeDeleteModal = closeDeleteModal;
    window.executeDeleteProfile = executeDeleteProfile;

    // ============================================
    // DATABASE RESET FUNCTIONS (DANGER ZONE)
    // ============================================

    /**
     * Setup Danger Zone tab handlers
     */
    function setupDangerZoneTab() {
        // Enable/disable confirm button based on input
        if (resetConfirmInput) {
            resetConfirmInput.addEventListener('input', function() {
                confirmResetBtn.disabled = resetConfirmInput.value !== 'RESET';
            });
        }
    }

    /**
     * Show reset modal (exposed globally)
     */
    function showResetModal() {
        // Fetch reset preview
        Cookie.ajax.get('/api/system/reset-preview/', function(err, preview) {
            if (err) {
                Cookie.toast.error('Failed to load reset preview');
                return;
            }

            resetPreview = preview;
            renderResetSummary(preview);
            resetModalStep1.classList.remove('hidden');
        });
    }

    /**
     * Render reset data summary
     */
    function renderResetSummary(preview) {
        var counts = preview.data_counts;
        var html = '<ul class="summary-list">';
        html += '<li>' + counts.profiles + ' profiles</li>';
        html += '<li>' + counts.recipes + ' recipes (' + counts.recipe_images + ' images)</li>';
        html += '<li>' + counts.favorites + ' favorites</li>';
        html += '<li>' + counts.collections + ' collections</li>';
        html += '<li>' + counts.view_history + ' view history entries</li>';
        html += '<li>' + (counts.ai_suggestions + counts.serving_adjustments) + ' cached AI entries</li>';
        html += '</ul>';
        resetDataSummary.innerHTML = html;
    }

    /**
     * Show step 2 of reset modal (exposed globally)
     */
    function showResetStep2() {
        resetModalStep1.classList.add('hidden');
        resetModalStep2.classList.remove('hidden');
        resetConfirmInput.value = '';
        confirmResetBtn.disabled = true;
        resetConfirmInput.focus();
    }

    /**
     * Show step 1 of reset modal (exposed globally)
     */
    function showResetStep1() {
        resetModalStep2.classList.add('hidden');
        resetModalStep1.classList.remove('hidden');
    }

    /**
     * Close reset modal (exposed globally)
     */
    function closeResetModal() {
        resetModalStep1.classList.add('hidden');
        resetModalStep2.classList.add('hidden');
        resetConfirmInput.value = '';
        confirmResetBtn.disabled = true;
        resetPreview = null;
    }

    /**
     * Execute database reset (exposed globally)
     */
    function executeReset() {
        if (resetConfirmInput.value !== 'RESET') return;

        confirmResetBtn.disabled = true;
        resetBtnText.textContent = 'Resetting...';

        Cookie.ajax.post('/api/system/reset/', { confirmation_text: 'RESET' }, function(err, result) {
            confirmResetBtn.disabled = false;
            resetBtnText.textContent = 'Reset Database';

            if (err) {
                Cookie.toast.error('Failed to reset database');
                return;
            }

            Cookie.toast.success('Database reset complete');
            closeResetModal();

            // Redirect to home/profile creation
            setTimeout(function() {
                window.location.href = '/legacy/';
            }, 1000);
        });
    }

    // Expose reset modal functions globally for onclick handlers
    window.showResetModal = showResetModal;
    window.showResetStep1 = showResetStep1;
    window.showResetStep2 = showResetStep2;
    window.closeResetModal = closeResetModal;
    window.executeReset = executeReset;

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
