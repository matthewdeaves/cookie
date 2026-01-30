/**
 * Settings page - Auto-initialization (ES5, iOS 9 compatible)
 * Load this file LAST, after all tab modules.
 */
(function() {
    'use strict';

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.settings.init);
    } else {
        Cookie.pages.settings.init();
    }
})();
