/**
 * Toast notifications for Legacy frontend (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};

Cookie.toast = (function() {
    'use strict';

    var TOAST_DURATION = 3000;
    var container = null;

    /**
     * Initialize toast container
     */
    function init() {
        container = document.getElementById('toast-container');
    }

    /**
     * Show a toast message
     * @param {string} message - Toast message
     * @param {string} type - Toast type ('success' or 'error')
     */
    function show(message, type) {
        if (!container) {
            init();
        }

        var toast = document.createElement('div');
        toast.className = 'toast toast-' + (type || 'success');
        toast.textContent = message;

        container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(function() {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, TOAST_DURATION);
    }

    /**
     * Show success toast
     * @param {string} message - Toast message
     */
    function success(message) {
        show(message, 'success');
    }

    /**
     * Show error toast
     * @param {string} message - Toast message
     */
    function error(message) {
        show(message, 'error');
    }

    // Auto-init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return {
        show: show,
        success: success,
        error: error
    };
})();
