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

        // Attach image error handlers to all recipe images on the page
        setupImageErrorHandlers();

        // Initialize page-specific modules if they exist
        var pageName = document.body.getAttribute('data-page');
        if (pageName && Cookie.pages && Cookie.pages[pageName]) {
            Cookie.pages[pageName].init();
        }
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
