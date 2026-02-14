/**
 * Settings page - General tab (ES5, iOS 9 compatible)
 * Handles API key testing/saving and deployment settings.
 */
(function() {
    'use strict';

    // API Key elements
    var apiKeyInput;
    var testKeyBtn;
    var saveKeyBtn;
    var testKeyText;
    var saveKeyText;

    // Deployment settings elements
    var deploymentLoading;
    var deploymentSettings;
    var deploymentModeHome;
    var deploymentModePublic;
    var deploymentModeEnvNotice;
    var registrationGroup;
    var allowRegistration;
    var registrationEnvNotice;
    var instanceNameGroup;
    var instanceNameInput;
    var instanceNameEnvNotice;
    var saveDeploymentBtn;
    var saveDeploymentText;

    // State
    var originalSettings = null;
    var envOverrides = null;

    function init() {
        // API key elements
        apiKeyInput = document.getElementById('api-key-input');
        testKeyBtn = document.getElementById('test-key-btn');
        saveKeyBtn = document.getElementById('save-key-btn');
        testKeyText = document.getElementById('test-key-text');
        saveKeyText = document.getElementById('save-key-text');

        // Deployment settings elements
        deploymentLoading = document.getElementById('deployment-loading');
        deploymentSettings = document.getElementById('deployment-settings');
        deploymentModeHome = document.getElementById('deployment-mode-home');
        deploymentModePublic = document.getElementById('deployment-mode-public');
        deploymentModeEnvNotice = document.getElementById('deployment-mode-env-notice');
        registrationGroup = document.getElementById('registration-group');
        allowRegistration = document.getElementById('allow-registration');
        registrationEnvNotice = document.getElementById('registration-env-notice');
        instanceNameGroup = document.getElementById('instance-name-group');
        instanceNameInput = document.getElementById('instance-name');
        instanceNameEnvNotice = document.getElementById('instance-name-env-notice');
        saveDeploymentBtn = document.getElementById('save-deployment-btn');
        saveDeploymentText = document.getElementById('save-deployment-text');

        // API key handlers
        if (apiKeyInput) {
            apiKeyInput.addEventListener('input', updateApiKeyButtons);
        }
        if (testKeyBtn) {
            testKeyBtn.addEventListener('click', handleTestKey);
        }
        if (saveKeyBtn) {
            saveKeyBtn.addEventListener('click', handleSaveKey);
        }

        // Deployment settings handlers
        if (deploymentModeHome) {
            deploymentModeHome.addEventListener('change', handleDeploymentModeChange);
        }
        if (deploymentModePublic) {
            deploymentModePublic.addEventListener('change', handleDeploymentModeChange);
        }
        if (allowRegistration) {
            allowRegistration.addEventListener('change', checkDeploymentChanges);
        }
        if (instanceNameInput) {
            instanceNameInput.addEventListener('input', checkDeploymentChanges);
        }
        if (saveDeploymentBtn) {
            saveDeploymentBtn.addEventListener('click', handleSaveDeployment);
        }

        // Load deployment settings
        loadDeploymentSettings();
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

    // ============================================
    // DEPLOYMENT SETTINGS
    // ============================================

    function loadDeploymentSettings() {
        if (!deploymentLoading) return;

        Cookie.ajax.get('/api/system/auth-settings/', function(err, result) {
            if (err) {
                deploymentLoading.textContent = 'Failed to load deployment settings';
                return;
            }

            originalSettings = {
                deployment_mode: result.deployment_mode,
                allow_registration: result.allow_registration,
                instance_name: result.instance_name
            };
            envOverrides = result.env_overrides;

            renderDeploymentSettings(result);
        });
    }

    function renderDeploymentSettings(settings) {
        // Hide loading, show form
        deploymentLoading.classList.add('hidden');
        deploymentSettings.classList.remove('hidden');

        // Set deployment mode
        if (settings.deployment_mode === 'public') {
            deploymentModePublic.checked = true;
        } else {
            deploymentModeHome.checked = true;
        }

        // Handle deployment mode env override
        if (envOverrides.deployment_mode) {
            deploymentModeEnvNotice.classList.remove('hidden');
            deploymentModeHome.disabled = true;
            deploymentModePublic.disabled = true;
            var radioOptions = document.querySelectorAll('#deployment-mode-group .radio-option');
            for (var i = 0; i < radioOptions.length; i++) {
                radioOptions[i].classList.add('disabled');
            }
        }

        // Set allow registration
        allowRegistration.checked = settings.allow_registration;

        // Handle registration env override
        if (envOverrides.allow_registration) {
            registrationEnvNotice.classList.remove('hidden');
            allowRegistration.disabled = true;
            allowRegistration.parentElement.classList.add('disabled');
        }

        // Set instance name
        instanceNameInput.value = settings.instance_name;

        // Handle instance name env override
        if (envOverrides.instance_name) {
            instanceNameEnvNotice.classList.remove('hidden');
            instanceNameInput.disabled = true;
            instanceNameGroup.classList.add('form-group-disabled');
        }

        // Update visibility of public-mode-only fields
        updatePublicModeFields();
    }

    function handleDeploymentModeChange() {
        updatePublicModeFields();
        checkDeploymentChanges();
    }

    function updatePublicModeFields() {
        var isPublicMode = deploymentModePublic.checked;

        // Show/hide registration and instance name for public mode
        if (isPublicMode) {
            registrationGroup.style.display = '';
            instanceNameGroup.style.display = '';
        } else {
            registrationGroup.style.display = 'none';
            instanceNameGroup.style.display = 'none';
        }
    }

    function checkDeploymentChanges() {
        if (!originalSettings) {
            saveDeploymentBtn.disabled = true;
            return;
        }

        var currentMode = deploymentModePublic.checked ? 'public' : 'home';
        var currentRegistration = allowRegistration.checked;
        var currentInstanceName = instanceNameInput.value.trim();

        // Check if any changes are to non-env-controlled fields
        var hasEditableChanges = false;
        if (!envOverrides.deployment_mode && currentMode !== originalSettings.deployment_mode) {
            hasEditableChanges = true;
        }
        if (!envOverrides.allow_registration && currentRegistration !== originalSettings.allow_registration) {
            hasEditableChanges = true;
        }
        if (!envOverrides.instance_name && currentInstanceName !== originalSettings.instance_name) {
            hasEditableChanges = true;
        }

        saveDeploymentBtn.disabled = !hasEditableChanges;
    }

    function handleSaveDeployment() {
        var currentMode = deploymentModePublic.checked ? 'public' : 'home';
        var currentRegistration = allowRegistration.checked;
        var currentInstanceName = instanceNameInput.value.trim();

        // Confirm switching to public mode
        if (currentMode === 'public' && originalSettings.deployment_mode === 'home') {
            var confirmed = window.confirm(
                'Switching to Public mode will require all users to create accounts with passwords.\n\n' +
                'Existing profiles will need to be linked to user accounts.\n\n' +
                'Are you sure you want to continue?'
            );
            if (!confirmed) return;
        }

        saveDeploymentBtn.disabled = true;
        saveDeploymentText.textContent = 'Saving...';

        var data = {};

        // Only send fields that aren't env-controlled
        if (!envOverrides.deployment_mode) {
            data.deployment_mode = currentMode;
        }
        if (!envOverrides.allow_registration) {
            data.allow_registration = currentRegistration;
        }
        if (!envOverrides.instance_name) {
            data.instance_name = currentInstanceName;
        }

        Cookie.ajax.put('/api/system/auth-settings/', data, function(err, result) {
            saveDeploymentBtn.disabled = false;
            saveDeploymentText.textContent = 'Save Changes';

            if (err) {
                Cookie.toast.error('Failed to save deployment settings');
                return;
            }

            if (result.success) {
                Cookie.toast.success('Deployment settings saved');

                // Update original settings
                originalSettings = {
                    deployment_mode: result.deployment_mode,
                    allow_registration: result.allow_registration,
                    instance_name: result.instance_name
                };

                // Show warnings if any
                if (result.warnings && result.warnings.length > 0) {
                    for (var i = 0; i < result.warnings.length; i++) {
                        Cookie.toast.warning(result.warnings[i]);
                    }
                }

                checkDeploymentChanges();

                // If mode changed, reload page to apply changes
                if (data.deployment_mode) {
                    setTimeout(function() {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                Cookie.toast.error(result.message || 'Failed to save settings');
            }
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('general', {
        init: init
    });
})();
