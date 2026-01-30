/**
 * Settings page - Danger Zone tab (ES5, iOS 9 compatible)
 * Handles database reset functionality with two-step confirmation.
 */
(function() {
    'use strict';

    var resetModalStep1;
    var resetModalStep2;
    var resetDataSummary;
    var resetConfirmInput;
    var confirmResetBtn;
    var resetBtnText;

    function init() {
        resetModalStep1 = document.getElementById('reset-modal-step1');
        resetModalStep2 = document.getElementById('reset-modal-step2');
        resetDataSummary = document.getElementById('reset-data-summary');
        resetConfirmInput = document.getElementById('reset-confirm-input');
        confirmResetBtn = document.getElementById('confirm-reset-btn');
        resetBtnText = document.getElementById('reset-btn-text');

        // Enable/disable confirm button based on input
        if (resetConfirmInput) {
            resetConfirmInput.addEventListener('input', function() {
                confirmResetBtn.disabled = resetConfirmInput.value !== 'RESET';
            });
        }

        // Expose modal functions globally for onclick handlers
        window.showResetModal = showResetModal;
        window.showResetStep1 = showResetStep1;
        window.showResetStep2 = showResetStep2;
        window.closeResetModal = closeResetModal;
        window.executeReset = executeReset;
    }

    function showResetModal() {
        var state = Cookie.pages.settings.getState();

        Cookie.ajax.get('/api/system/reset-preview/', function(err, preview) {
            if (err) {
                Cookie.toast.error('Failed to load reset preview');
                return;
            }

            state.resetPreview = preview;
            renderResetSummary(preview);
            resetModalStep1.classList.remove('hidden');
        });
    }

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

    function showResetStep2() {
        resetModalStep1.classList.add('hidden');
        resetModalStep2.classList.remove('hidden');
        resetConfirmInput.value = '';
        confirmResetBtn.disabled = true;
        resetConfirmInput.focus();
    }

    function showResetStep1() {
        resetModalStep2.classList.add('hidden');
        resetModalStep1.classList.remove('hidden');
    }

    function closeResetModal() {
        var state = Cookie.pages.settings.getState();
        resetModalStep1.classList.add('hidden');
        resetModalStep2.classList.add('hidden');
        resetConfirmInput.value = '';
        confirmResetBtn.disabled = true;
        state.resetPreview = null;
    }

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

            setTimeout(function() {
                window.location.href = '/legacy/';
            }, 1000);
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('danger', {
        init: init
    });
})();
