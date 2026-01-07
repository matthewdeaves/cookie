/**
 * Home page (ES5, iOS 9 compatible)
 * Full implementation coming in Session B
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.home = (function() {
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
        // Logout/switch profile button
        var logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                window.location.href = '/legacy/';
            });
        }

        // Search input - navigate to search on Enter
        var searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', function(e) {
                if (e.keyCode === 13 || e.key === 'Enter') {
                    var query = searchInput.value.trim();
                    if (query) {
                        window.location.href = '/legacy/search/?q=' + encodeURIComponent(query);
                    }
                }
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
        document.addEventListener('DOMContentLoaded', Cookie.pages.home.init);
    } else {
        Cookie.pages.home.init();
    }
})();
