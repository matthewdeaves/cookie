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

        // Setup profile dropdown (shared across all pages with nav header)
        setupProfileDropdown();

        // Highlight the active nav icon
        highlightActiveNav();

        // Attach image error handlers to all recipe images on the page
        setupImageErrorHandlers();

        // Make source links on recipe cards open the original recipe URL
        setupSourceLinks();

        // Keep links inside the PWA shell on iOS standalone mode
        setupStandaloneNavigation();

        // Apply avatar colors from data attributes (CSP blocks inline style=)
        applyAvatarColors();

        // Initialize page-specific modules if they exist
        var pageName = document.body.getAttribute('data-page');
        if (pageName && Cookie.pages && Cookie.pages[pageName]) {
            Cookie.pages[pageName].init();
        }
    }

    /**
     * Intercept clicks on recipe card source labels that have a source URL.
     * Opens the original recipe URL instead of navigating to the detail page.
     */
    function setupSourceLinks() {
        document.addEventListener('click', function(e) {
            var source = e.target.closest('.recipe-card-source[data-source-url]');
            if (source) {
                e.preventDefault();
                e.stopPropagation();
                window.open(source.getAttribute('data-source-url'), '_blank');
            }
        });
    }

    /**
     * Attach onerror handlers to recipe card images and detail hero images.
     * When an image fails to load (e.g. 404 cached image), hides the broken
     * image and shows a placeholder with the recipe title.
     */
    function setupImageErrorHandlers() {
        // Recipe card images (home, favorites, collections, all-recipes pages)
        var cardImages = document.querySelectorAll('.recipe-card-image img');
        for (var i = 0; i < cardImages.length; i++) {
            (function(img) {
                img.onerror = function() {
                    var card = img.closest('.recipe-card');
                    var title = '';
                    if (card) {
                        var titleEl = card.querySelector('.recipe-card-title');
                        if (titleEl) {
                            title = titleEl.textContent;
                        }
                    }
                    var parent = img.parentElement;
                    if (parent) {
                        var placeholder = document.createElement('div');
                        placeholder.className = 'recipe-card-no-image';
                        var span = document.createElement('span');
                        span.textContent = title || 'No image';
                        placeholder.appendChild(span);
                        img.style.display = 'none';
                        parent.insertBefore(placeholder, img);
                        parent.removeChild(img);
                    }
                };
            })(cardImages[i]);
        }

        // Detail page hero image
        var heroImages = document.querySelectorAll('.hero .hero-image');
        for (var j = 0; j < heroImages.length; j++) {
            (function(img) {
                img.onerror = function() {
                    var hero = img.closest('.hero');
                    var title = '';
                    if (hero) {
                        var titleEl = hero.querySelector('.hero-title');
                        if (titleEl) {
                            title = titleEl.textContent;
                        }
                    }
                    var placeholder = document.createElement('div');
                    placeholder.className = 'hero-placeholder';
                    var span = document.createElement('span');
                    span.textContent = title || 'No image';
                    placeholder.appendChild(span);
                    img.style.display = 'none';
                    img.parentElement.insertBefore(placeholder, img);
                    img.parentElement.removeChild(img);
                };
            })(heroImages[j]);
        }
    }

    /**
     * Setup profile dropdown menu in nav header
     */
    function setupProfileDropdown() {
        var dropdownBtn = document.getElementById('profile-dropdown-btn');
        var dropdownMenu = document.getElementById('profile-dropdown-menu');
        var switchBtn = document.getElementById('switch-profile-btn');
        var logoutBtn = document.getElementById('logout-btn');

        if (!dropdownBtn || !dropdownMenu) return;

        dropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('hidden');
        });

        // Close on outside click
        document.addEventListener('click', function() {
            dropdownMenu.classList.add('hidden');
        });

        if (switchBtn) {
            switchBtn.addEventListener('click', function() {
                Cookie.state.clearProfile();
                window.location.href = '/legacy/';
            });
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                Cookie.state.clearProfile();
                window.location.href = '/legacy/';
            });
        }
    }

    /**
     * Highlight the active navigation icon based on the current page
     */
    function highlightActiveNav() {
        var screen = document.querySelector('.screen[data-page], .play-mode[data-page]');
        if (!screen) return;

        var page = screen.getAttribute('data-page');
        var labelMap = {
            'home': 'Home',
            'all-recipes': 'All recipes',
            'favorites': 'Favorites',
            'collections': 'Collections',
            'collection-detail': 'Collections',
            'settings': 'Settings'
        };

        var label = labelMap[page];
        if (!label) return;

        var links = document.querySelectorAll('.header-nav-link');
        for (var i = 0; i < links.length; i++) {
            if (links[i].getAttribute('aria-label') === label) {
                var cls = label === 'Favorites' ? 'header-nav-link-active-accent' : 'header-nav-link-active';
                links[i].classList.add(cls);
                links[i].setAttribute('aria-current', 'page');
                break;
            }
        }
    }

    /**
     * Apply background colors from data-avatar-color attributes via CSSOM.
     * Inline style= attributes are blocked by CSP, but JS property assignment is not.
     */
    function applyAvatarColors() {
        var elements = document.querySelectorAll('[data-avatar-color]');
        for (var i = 0; i < elements.length; i++) {
            elements[i].style.backgroundColor = elements[i].getAttribute('data-avatar-color');
        }
    }

    /**
     * Keep navigation inside the PWA shell on iOS standalone mode.
     * Without this, tapping <a> links opens a new Safari window.
     */
    function setupStandaloneNavigation() {
        if (!window.navigator.standalone) return;

        document.addEventListener('click', function(e) {
            var target = e.target;
            while (target && target.nodeName !== 'A') {
                target = target.parentNode;
            }
            if (!target || target.nodeName !== 'A') return;

            var href = target.getAttribute('href');
            if (href
                && href.indexOf('http') !== 0
                && href.indexOf('javascript:') !== 0
                && href.charAt(0) !== '#'
                && !target.getAttribute('target')) {
                e.preventDefault();
                window.location.href = href;
            }
        }, false);
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
