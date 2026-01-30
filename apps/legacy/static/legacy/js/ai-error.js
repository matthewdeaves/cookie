/**
 * AI Error Handler (ES5, iOS 9 compatible)
 * Provides user-friendly error handling for AI features with actionable guidance
 */
var Cookie = Cookie || {};

Cookie.aiError = (function() {
    'use strict';

    // Status code to action/message lookup table
    var STATUS_HANDLERS = {
        503: { action: 'configure_key', message: 'AI features are not available. Please configure your API key in Settings.' },
        401: { action: 'update_key', message: 'Your API key appears to be invalid. Please update it in Settings.' },
        429: { action: 'retry', message: 'Too many requests. Please wait a moment and try again.' },
        402: { action: 'add_credits', message: 'Your OpenRouter account may need credits. Please check your account.' }
    };

    /**
     * Get default action/message for a status code
     */
    function getStatusHandler(status, errorCode) {
        if (errorCode === 'ai_unavailable') return STATUS_HANDLERS[503];
        return STATUS_HANDLERS[status] || null;
    }

    /**
     * Handle AI-related errors with actionable guidance
     * @param {Error} err - Error object from ajax callback
     * @param {string} defaultMessage - Default error message to show
     * @returns {Object} - { message: string, action: string|null }
     */
    function handleError(err, defaultMessage) {
        var result = { message: defaultMessage || 'An error occurred', action: null };
        if (!err) return result;

        var data = err.data || {};
        if (data.message) result.message = data.message;
        if (data.action) result.action = data.action;

        // Apply status-based defaults if no action from server
        if (!result.action) {
            var handler = getStatusHandler(err.status, data.error);
            if (handler) {
                result.action = handler.action;
                result.message = result.message || handler.message;
            }
        }

        return result;
    }

    /**
     * Show error toast with appropriate guidance
     * @param {Error} err - Error object from ajax callback
     * @param {string} defaultMessage - Default error message to show
     */
    function showError(err, defaultMessage) {
        var result = handleError(err, defaultMessage);

        // Add guidance text based on action
        var fullMessage = result.message;
        if (result.action === 'configure_key') {
            fullMessage = result.message + ' Go to Settings to configure.';
        } else if (result.action === 'update_key') {
            fullMessage = result.message + ' Go to Settings to update.';
        } else if (result.action === 'retry') {
            fullMessage = result.message;
        } else if (result.action === 'add_credits') {
            fullMessage = result.message;
        }

        Cookie.toast.error(fullMessage);
        return result;
    }

    /**
     * Check if AI features should be hidden based on error
     * @param {Error} err - Error object from ajax callback
     * @returns {boolean} - True if AI features should be hidden
     */
    function shouldHideFeatures(err) {
        if (!err) return false;

        var status = err.status;
        var data = err.data || {};

        // Hide features for 503 (unavailable) or 401 (invalid key)
        return status === 503 || status === 401 || data.error === 'ai_unavailable';
    }

    /**
     * Hide AI feature elements on the page
     */
    function hideAIFeatures() {
        var aiFeatures = document.querySelectorAll('[data-ai-feature]');
        for (var i = 0; i < aiFeatures.length; i++) {
            aiFeatures[i].classList.add('hidden');
        }
    }

    return {
        handleError: handleError,
        showError: showError,
        shouldHideFeatures: shouldHideFeatures,
        hideAIFeatures: hideAIFeatures
    };
})();
