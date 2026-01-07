/**
 * Search page (ES5, iOS 9 compatible)
 * Full implementation coming in Session C
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.search = (function() {
    'use strict';

    /**
     * Initialize the page
     */
    function init() {
        setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Back button
        var backBtn = document.getElementById('back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', function() {
                window.location.href = '/legacy/home/';
            });
        }
    }

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.search.init);
    } else {
        Cookie.pages.search.init();
    }
})();
