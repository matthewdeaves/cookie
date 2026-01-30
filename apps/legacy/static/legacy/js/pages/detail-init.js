/**
 * Recipe Detail page - Auto-initialization (ES5, iOS 9 compatible)
 * Load this file LAST, after all feature modules.
 */
(function() {
    'use strict';

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.detail.init);
    } else {
        Cookie.pages.detail.init();
    }
})();
