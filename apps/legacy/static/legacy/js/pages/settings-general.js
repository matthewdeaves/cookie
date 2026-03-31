/**
 * Settings page - General tab (ES5, iOS 9 compatible)
 * Handles API key testing/saving and theme/unit preferences.
 */
(function() {
    'use strict';

    var apiKeyInput;
    var testKeyBtn;
    var saveKeyBtn;
    var testKeyText;
    var saveKeyText;
    var themeLightBtn;
    var themeDarkBtn;
    var unitsMetricBtn;
    var unitsImperialBtn;
    var quotaConfigSection;
    var quotaUsageSection;
    var saveQuotasBtn;
    var saveQuotasText;

    function init() {
        apiKeyInput = document.getElementById('api-key-input');
        testKeyBtn = document.getElementById('test-key-btn');
        saveKeyBtn = document.getElementById('save-key-btn');
        testKeyText = document.getElementById('test-key-text');
        saveKeyText = document.getElementById('save-key-text');
        themeLightBtn = document.getElementById('theme-light-btn');
        themeDarkBtn = document.getElementById('theme-dark-btn');
        unitsMetricBtn = document.getElementById('units-metric-btn');
        unitsImperialBtn = document.getElementById('units-imperial-btn');
        quotaConfigSection = document.getElementById('quota-config-section');
        quotaUsageSection = document.getElementById('quota-usage-section');
        saveQuotasBtn = document.getElementById('save-quotas-btn');
        saveQuotasText = document.getElementById('save-quotas-text');

        if (apiKeyInput) {
            apiKeyInput.addEventListener('input', updateApiKeyButtons);
        }
        if (testKeyBtn) {
            testKeyBtn.addEventListener('click', handleTestKey);
        }
        if (saveKeyBtn) {
            saveKeyBtn.addEventListener('click', handleSaveKey);
        }
        if (themeLightBtn) {
            themeLightBtn.addEventListener('click', handleThemeClick);
        }
        if (themeDarkBtn) {
            themeDarkBtn.addEventListener('click', handleThemeClick);
        }
        if (unitsMetricBtn) {
            unitsMetricBtn.addEventListener('click', handleUnitsClick);
        }
        if (unitsImperialBtn) {
            unitsImperialBtn.addEventListener('click', handleUnitsClick);
        }
        if (saveQuotasBtn) {
            saveQuotasBtn.addEventListener('click', handleSaveQuotas);
        }

        loadQuotas();
    }

    function updateApiKeyButtons() {
        var hasValue = apiKeyInput.value.trim().length > 0;
        testKeyBtn.disabled = !hasValue;
        saveKeyBtn.disabled = !hasValue;
    }

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
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            } else {
                Cookie.toast.error(result.message);
            }
        });
    }

    function handleThemeClick(e) {
        var newTheme = e.currentTarget.getAttribute('data-theme');
        savePreference('theme', newTheme);
    }

    function handleUnitsClick(e) {
        var newUnit = e.currentTarget.getAttribute('data-unit');
        savePreference('unit_preference', newUnit);
    }

    function savePreference(field, value) {
        var pageEl = document.querySelector('[data-page="settings"]');
        var profileId = pageEl ? pageEl.getAttribute('data-profile-id') : null;
        if (!profileId) return;

        var profile = Cookie.state.getProfile();
        var payload = {
            name: profile.name,
            avatar_color: profile.avatar_color,
            theme: profile.theme || 'light',
            unit_preference: profile.unit_preference || 'metric'
        };
        payload[field] = value;

        Cookie.ajax.put('/api/profiles/' + profileId + '/', payload, function(err) {
            if (err) {
                Cookie.toast.error('Failed to save preference');
                return;
            }

            if (field === 'theme') {
                setToggleActive(themeLightBtn, themeDarkBtn, value === 'light');
                applyTheme(value);
                profile.theme = value;
                Cookie.toast.success('Theme updated');
            } else if (field === 'unit_preference') {
                setToggleActive(unitsMetricBtn, unitsImperialBtn, value === 'metric');
                profile.unit_preference = value;
                Cookie.toast.success('Units updated');
            }
        });
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    function setToggleActive(btnA, btnB, aIsActive) {
        if (aIsActive) {
            btnA.classList.add('active');
            btnB.classList.remove('active');
        } else {
            btnA.classList.remove('active');
            btnB.classList.add('active');
        }
    }

    /**
     * Feature label lookup for display
     */
    var FEATURE_LABELS = {
        remix: 'Remixes',
        remix_suggestions: 'Remix Suggestions',
        scale: 'Scaling',
        tips: 'Tips',
        discover: 'Discover',
        timer: 'Timer Naming'
    };

    var FEATURE_KEYS = ['remix', 'remix_suggestions', 'scale', 'tips', 'discover', 'timer'];

    /**
     * Load quota data from API
     */
    function loadQuotas() {
        Cookie.ajax.get('/api/ai/quotas', function(err, data) {
            if (err) {
                // 404 means home mode — hide quota sections
                if (quotaConfigSection) quotaConfigSection.classList.add('hidden');
                if (quotaUsageSection) quotaUsageSection.classList.add('hidden');
                return;
            }
            renderQuotaConfig(data);
            renderQuotaUsage(data);
        });
    }

    /**
     * Render quota config inputs (admin only)
     */
    function renderQuotaConfig(data) {
        if (!quotaConfigSection) return;
        quotaConfigSection.classList.remove('hidden');

        for (var i = 0; i < FEATURE_KEYS.length; i++) {
            var key = FEATURE_KEYS[i];
            var input = document.getElementById('quota-limit-' + key);
            if (input) {
                input.value = data.limits[key] || 0;
            }
        }
    }

    /**
     * Render quota usage display
     */
    function renderQuotaUsage(data) {
        if (!quotaUsageSection) return;
        quotaUsageSection.classList.remove('hidden');

        var usageList = document.getElementById('quota-usage-list');
        if (!usageList) return;

        // Clear previous content
        while (usageList.firstChild) {
            usageList.removeChild(usageList.firstChild);
        }

        for (var i = 0; i < FEATURE_KEYS.length; i++) {
            var key = FEATURE_KEYS[i];
            var label = FEATURE_LABELS[key];
            var used = data.usage[key] || 0;
            var limit = data.limits[key] || 0;

            var row = document.createElement('div');
            row.className = 'quota-usage-row';

            var labelSpan = document.createElement('span');
            labelSpan.className = 'quota-usage-label';
            labelSpan.textContent = label;
            row.appendChild(labelSpan);

            var valueSpan = document.createElement('span');
            if (data.unlimited) {
                valueSpan.className = 'quota-badge-unlimited';
                valueSpan.textContent = 'Unlimited';
            } else {
                valueSpan.className = 'quota-usage-value';
                valueSpan.textContent = used + ' / ' + limit;
            }
            row.appendChild(valueSpan);

            usageList.appendChild(row);
        }

        var resetDiv = document.createElement('div');
        resetDiv.className = 'quota-reset-info';
        resetDiv.textContent = 'Resets at ' + formatResetTime(data.resets_at);
        usageList.appendChild(resetDiv);
    }

    /**
     * Format ISO timestamp for display
     */
    function formatResetTime(isoStr) {
        if (!isoStr) return 'midnight UTC';
        try {
            var d = new Date(isoStr);
            var hours = d.getHours();
            var minutes = d.getMinutes();
            var ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12;
            hours = hours || 12;
            var minStr = minutes < 10 ? '0' + minutes : '' + minutes;
            return hours + ':' + minStr + ' ' + ampm + ' (local time)';
        } catch (e) {
            return 'midnight UTC';
        }
    }

    /**
     * Save quota limits (admin only)
     */
    function handleSaveQuotas() {
        var payload = {};
        for (var i = 0; i < FEATURE_KEYS.length; i++) {
            var key = FEATURE_KEYS[i];
            var input = document.getElementById('quota-limit-' + key);
            if (input) {
                payload[key] = parseInt(input.value, 10) || 0;
            }
        }

        saveQuotasBtn.disabled = true;
        saveQuotasText.textContent = 'Saving...';

        Cookie.ajax.put('/api/ai/quotas', payload, function(err, result) {
            saveQuotasBtn.disabled = false;
            saveQuotasText.textContent = 'Save Limits';

            if (err) {
                Cookie.toast.error('Failed to save quota limits');
                return;
            }

            Cookie.toast.success('Quota limits saved');
            renderQuotaUsage(result);
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('general', {
        init: init
    });
})();
