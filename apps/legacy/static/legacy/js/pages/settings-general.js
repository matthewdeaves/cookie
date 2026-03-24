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

    // Register with core module
    Cookie.pages.settings.registerTab('general', {
        init: init
    });
})();
