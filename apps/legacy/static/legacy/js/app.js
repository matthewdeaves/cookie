/**
 * Cookie Legacy - Main application bootstrap (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};

Cookie.app = (function() {
    'use strict';

    /**
     * Setup global header button handlers
     */
    function setupHeaderButtons() {
        // Public mode: Logout button (ends authenticated session)
        var logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                window.location.href = '/legacy/logout/';
            });
        }

        // Home mode: Switch profile button (goes to profile selector)
        var switchProfileBtn = document.getElementById('switch-profile-btn');
        if (switchProfileBtn) {
            switchProfileBtn.addEventListener('click', function() {
                window.location.href = '/legacy/';
            });
        }
    }

    /**
     * Initialize the application
     */
    function init() {
        // Add touch class for touch-specific styles
        if ('ontouchstart' in window) {
            document.documentElement.classList.add('touch');
        }

        // Setup global header buttons
        setupHeaderButtons();

        // Initialize page-specific modules if they exist
        var pageName = document.body.getAttribute('data-page');
        if (pageName && Cookie.pages && Cookie.pages[pageName]) {
            Cookie.pages[pageName].init();
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    return {
        init: init
    };
})();
