/**
 * Cookie Legacy - Main application bootstrap (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};

Cookie.app = (function() {
    'use strict';

    /**
     * Initialize the application
     */
    function init() {
        // Add touch class for touch-specific styles
        if ('ontouchstart' in window) {
            document.documentElement.classList.add('touch');
        }

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
