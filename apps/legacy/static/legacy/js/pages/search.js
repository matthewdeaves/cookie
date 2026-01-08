/**
 * Search page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.search = (function() {
    'use strict';

    // State
    var state = {
        query: '',
        isUrl: false,
        results: [],
        sites: {},
        total: 0,
        page: 1,
        hasMore: false,
        selectedSource: null,
        loading: false,
        importing: null
    };

    // Image polling state (progressive loading)
    var imagePollingState = {
        isPolling: false,
        pendingUrls: {},  // Map of recipe_url -> {image_url, needs_cache}
        pollInterval: null,
        pollStartTime: null,
        currentQuery: null,
        loadedPages: []  // Track all pages that have been loaded
    };

    // DOM elements
    var elements = {
        loading: null,
        resultsGrid: null,
        emptyState: null,
        pagination: null,
        endOfResults: null,
        loadMoreBtn: null,
        sourceFilters: null,
        searchCount: null,
        importUrlBtn: null,
        urlImportCard: null
    };

    /**
     * Initialize the page
     */
    function init() {
        // Get state from window
        state.query = window.searchQuery || '';
        state.isUrl = window.isUrlSearch || false;

        // Get DOM elements
        elements.loading = document.getElementById('loading');
        elements.resultsGrid = document.getElementById('results-grid');
        elements.emptyState = document.getElementById('empty-state');
        elements.pagination = document.getElementById('pagination');
        elements.endOfResults = document.getElementById('end-of-results');
        elements.loadMoreBtn = document.getElementById('load-more-btn');
        elements.sourceFilters = document.getElementById('source-filters');
        elements.searchCount = document.getElementById('search-count');
        elements.importUrlBtn = document.getElementById('import-url-btn');
        elements.urlImportCard = document.getElementById('url-import-card');

        setupEventListeners();

        // Start search if not a URL
        if (!state.isUrl && state.query) {
            searchRecipes(1, true);
        } else if (state.isUrl) {
            hideElement(elements.loading);
        }
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

        // Load more button
        if (elements.loadMoreBtn) {
            elements.loadMoreBtn.addEventListener('click', function() {
                if (!state.loading && state.hasMore) {
                    searchRecipes(state.page + 1, false);
                }
            });
        }

        // URL import button
        if (elements.importUrlBtn) {
            elements.importUrlBtn.addEventListener('click', function() {
                var url = this.getAttribute('data-url');
                if (url) {
                    importRecipe(url, this);
                }
            });
        }

        // Delegate import button clicks in results
        if (elements.resultsGrid) {
            elements.resultsGrid.addEventListener('click', function(e) {
                var btn = e.target.closest('.btn-import');
                if (btn && !btn.disabled) {
                    var url = btn.getAttribute('data-url');
                    if (url) {
                        importRecipe(url, btn);
                    }
                }
            });
        }
    }

    /**
     * Search for recipes
     */
    function searchRecipes(page, reset) {
        if (state.loading) return;

        state.loading = true;
        state.page = page;

        if (reset) {
            state.results = [];
            state.sites = {};
            showElement(elements.loading);
            hideElement(elements.resultsGrid);
            hideElement(elements.emptyState);
            hideElement(elements.pagination);
            hideElement(elements.endOfResults);
        } else {
            // Show loading state on button
            if (elements.loadMoreBtn) {
                elements.loadMoreBtn.textContent = 'Loading...';
                elements.loadMoreBtn.disabled = true;
            }
        }

        // Build URL
        var url = '/api/recipes/search/?q=' + encodeURIComponent(state.query);
        url += '&page=' + page;
        if (state.selectedSource) {
            url += '&sources=' + encodeURIComponent(state.selectedSource);
        }

        Cookie.ajax.get(url, function(error, response) {
            state.loading = false;

            if (error) {
                hideElement(elements.loading);
                Cookie.toast.error('Search failed. Please try again.');
                return;
            }

            var previousCount = state.results.length;

            if (reset) {
                // Stop previous polling
                stopImagePolling();
                imagePollingState.pendingUrls = {};
                imagePollingState.loadedPages = [];

                state.results = response.results;
                state.sites = response.sites;
                renderSourceFilters();
            } else {
                // Append results
                state.results = state.results.concat(response.results);
            }

            state.total = response.total;
            state.hasMore = response.has_more;

            renderResults(reset, previousCount);
            updateSearchCount();

            // Start image polling for uncached images
            startImagePolling(response.results, state.query, page);
        });
    }

    /**
     * Render source filter chips
     */
    function renderSourceFilters() {
        if (!elements.sourceFilters) return;

        var sites = state.sites;
        var sortedSites = Object.keys(sites).sort(function(a, b) {
            return sites[b] - sites[a];
        });

        if (sortedSites.length === 0) {
            elements.sourceFilters.innerHTML = '';
            return;
        }

        // Calculate total
        var total = 0;
        for (var key in sites) {
            if (sites.hasOwnProperty(key)) {
                total += sites[key];
            }
        }

        var html = '';

        // All sources chip
        var allActive = state.selectedSource === null ? ' active' : '';
        html += '<button type="button" class="chip' + allActive + '" data-source="">';
        html += 'All Sources (' + total + ')';
        html += '</button>';

        // Individual source chips
        for (var i = 0; i < sortedSites.length; i++) {
            var site = sortedSites[i];
            var count = sites[site];
            var isActive = state.selectedSource === site ? ' active' : '';
            html += '<button type="button" class="chip' + isActive + '" data-source="' + escapeHtml(site) + '">';
            html += escapeHtml(site) + ' (' + count + ')';
            html += '</button>';
        }

        elements.sourceFilters.innerHTML = html;

        // Add click handlers
        var chips = elements.sourceFilters.querySelectorAll('.chip');
        for (var j = 0; j < chips.length; j++) {
            chips[j].addEventListener('click', handleSourceClick);
        }
    }

    /**
     * Handle source filter click
     */
    function handleSourceClick(e) {
        var source = e.target.getAttribute('data-source');
        state.selectedSource = source || null;

        // Re-search with filter
        searchRecipes(1, true);
    }

    /**
     * Render search results
     */
    function renderResults(reset, previousCount) {
        hideElement(elements.loading);

        if (state.results.length === 0) {
            hideElement(elements.resultsGrid);
            showElement(elements.emptyState);
            hideElement(elements.pagination);
            hideElement(elements.endOfResults);
            return;
        }

        hideElement(elements.emptyState);
        showElement(elements.resultsGrid);

        // Render cards
        var html = '';
        if (reset) {
            // Render all results
            for (var i = 0; i < state.results.length; i++) {
                html += renderSearchResultCard(state.results[i]);
            }
            elements.resultsGrid.innerHTML = html;
        } else {
            // Only render NEW results (from previousCount onwards)
            for (var i = previousCount; i < state.results.length; i++) {
                html += renderSearchResultCard(state.results[i]);
            }
            elements.resultsGrid.innerHTML += html;
        }

        // Update pagination
        if (state.hasMore) {
            showElement(elements.pagination);
            hideElement(elements.endOfResults);
            if (elements.loadMoreBtn) {
                elements.loadMoreBtn.textContent = 'Load More';
                elements.loadMoreBtn.disabled = false;
            }
        } else {
            hideElement(elements.pagination);
            showElement(elements.endOfResults);
        }
    }

    /**
     * Render a single search result card
     */
    function renderSearchResultCard(result) {
        var imageHtml = '';
        // Prefer cached image, fallback to external URL
        var imageUrl = result.cached_image_url || result.image_url;
        if (imageUrl) {
            imageHtml = '<img src="' + escapeHtml(imageUrl) + '" alt="' + escapeHtml(result.title) + '" loading="lazy">';
        } else {
            imageHtml = '<div class="search-result-no-image"><span>No image</span></div>';
        }

        var descriptionHtml = '';
        if (result.description) {
            descriptionHtml = '<p class="search-result-description">' + escapeHtml(truncate(result.description, 100)) + '</p>';
        }

        return '<div class="search-result-card" data-url="' + escapeHtml(result.url) + '">' +
            '<div class="search-result-image">' + imageHtml + '</div>' +
            '<div class="search-result-content">' +
                '<h3 class="search-result-title">' + escapeHtml(result.title) + '</h3>' +
                '<p class="search-result-host">' + escapeHtml(result.host) + '</p>' +
                descriptionHtml +
                '<button type="button" class="btn-import" data-url="' + escapeHtml(result.url) + '">Import</button>' +
            '</div>' +
        '</div>';
    }

    /**
     * Update search count display
     */
    function updateSearchCount() {
        if (!elements.searchCount) return;

        if (state.total === 0) {
            elements.searchCount.textContent = '';
        } else if (state.total === 1) {
            elements.searchCount.textContent = '1 result found';
        } else {
            elements.searchCount.textContent = state.total + ' results found';
        }
    }

    /**
     * Import a recipe from URL
     */
    function importRecipe(url, button) {
        if (state.importing) return;

        state.importing = url;

        // Update button state
        var originalText = button.textContent;
        button.textContent = 'Importing...';
        button.disabled = true;

        Cookie.ajax.post('/api/recipes/scrape/', { url: url }, function(error, response) {
            state.importing = null;

            if (error) {
                button.textContent = originalText;
                button.disabled = false;
                Cookie.toast.error(error.message || 'Failed to import recipe');
                return;
            }

            // Success - show toast and redirect to recipe detail
            Cookie.toast.success('Recipe imported!');

            // Redirect to recipe detail page
            // The detail page will record the view in history
            setTimeout(function() {
                window.location.href = '/legacy/recipe/' + response.id + '/';
            }, 1000);
        });
    }

    /**
     * Helper: Escape HTML
     */
    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Helper: Truncate string
     */
    function truncate(str, length) {
        if (!str) return '';
        if (str.length <= length) return str;
        return str.substring(0, length) + '...';
    }

    /**
     * Helper: Show element
     */
    function showElement(el) {
        if (el) {
            el.classList.remove('hidden');
        }
    }

    /**
     * Helper: Hide element
     */
    function hideElement(el) {
        if (el) {
            el.classList.add('hidden');
        }
    }

    /**
     * Helper: Escape CSS selector
     * Escapes special characters for use in CSS attribute selectors
     */
    function escapeSelector(str) {
        if (!str) return '';
        // Escape all special CSS characters: !"#$%&'()*+,./:;<=>?@[\]^`{|}~
        // Keep alphanumeric, hyphen, and underscore unescaped
        return str.replace(/([!"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~])/g, '\\$1');
    }

    /**
     * Start image polling for progressive loading
     */
    function startImagePolling(results, query, page) {
        // Track which images need caching
        for (var i = 0; i < results.length; i++) {
            var result = results[i];
            if (result.image_url && !result.cached_image_url) {
                imagePollingState.pendingUrls[result.url] = {
                    imageUrl: result.image_url,
                    needsCache: true
                };

                // Show loading spinner on image placeholder
                showImageLoadingSpinner(result.url);
            }
        }

        // Add page to loaded pages if not already tracked
        if (imagePollingState.loadedPages.indexOf(page) === -1) {
            imagePollingState.loadedPages.push(page);
        }

        // Start polling if not already running
        var hasPending = Object.keys(imagePollingState.pendingUrls).length > 0;
        if (!imagePollingState.isPolling && hasPending) {
            imagePollingState.isPolling = true;
            imagePollingState.pollStartTime = Date.now();
            imagePollingState.currentQuery = query;

            pollForCachedImages();
        }
        // If polling already running, extend the duration for new images
        else if (imagePollingState.isPolling && hasPending) {
            // Reset timer to give new images time to cache
            imagePollingState.pollStartTime = Date.now();
        }
    }

    /**
     * Poll for cached images
     */
    function pollForCachedImages() {
        var MAX_POLL_DURATION = 20000; // 20 seconds
        var POLL_INTERVAL = 4000; // 4 seconds

        imagePollingState.pollInterval = setInterval(function() {
            var elapsed = Date.now() - imagePollingState.pollStartTime;
            var hasPendingImages = Object.keys(imagePollingState.pendingUrls).length > 0;

            // Stop conditions
            if (elapsed > MAX_POLL_DURATION || !hasPendingImages) {
                stopImagePolling();
                return;
            }

            // Poll ALL loaded pages to detect cached images
            for (var i = 0; i < imagePollingState.loadedPages.length; i++) {
                var page = imagePollingState.loadedPages[i];
                var url = '/api/recipes/search/?q=' + encodeURIComponent(imagePollingState.currentQuery);
                url += '&page=' + page;
                if (state.selectedSource) {
                    url += '&sources=' + encodeURIComponent(state.selectedSource);
                }

                Cookie.ajax.get(url, function(error, response) {
                    if (!error && response && response.results) {
                        updateCachedImages(response.results);
                    }
                });
            }
        }, POLL_INTERVAL);
    }

    /**
     * Update cached images in displayed results
     */
    function updateCachedImages(results) {
        for (var i = 0; i < results.length; i++) {
            var result = results[i];

            // Early exit if URL not pending (optimization: skip DOM query)
            if (!imagePollingState.pendingUrls[result.url]) {
                continue;
            }

            // Check if this result has a pending image that's now cached
            if (result.cached_image_url) {
                var card = document.querySelector('[data-url="' + escapeSelector(result.url) + '"]');
                if (card) {
                    var imgContainer = card.querySelector('.search-result-image');
                    if (imgContainer) {
                        // Replace loading spinner with actual image
                        imgContainer.innerHTML = '<img src="' + escapeHtml(result.cached_image_url) +
                                                '" alt="' + escapeHtml(result.title) + '" loading="lazy">';
                    }
                }

                // Remove from pending list
                delete imagePollingState.pendingUrls[result.url];
            }
        }

        // Stop polling immediately if all images cached (optimization: no waiting for next interval)
        if (Object.keys(imagePollingState.pendingUrls).length === 0) {
            stopImagePolling();
        }
    }

    /**
     * Stop image polling
     */
    function stopImagePolling() {
        if (imagePollingState.pollInterval) {
            clearInterval(imagePollingState.pollInterval);
            imagePollingState.pollInterval = null;
            imagePollingState.isPolling = false;

            // Hide any remaining loading spinners
            hideAllLoadingSpinners();
        }
    }

    /**
     * Show loading spinner for image
     */
    function showImageLoadingSpinner(recipeUrl) {
        var card = document.querySelector('[data-url="' + escapeSelector(recipeUrl) + '"]');
        if (card) {
            var imgContainer = card.querySelector('.search-result-image');
            if (imgContainer) {
                var existingImg = imgContainer.querySelector('img');
                // Show spinner if no img exists, OR if img is using external URL (not cached)
                if (!existingImg || (existingImg && !existingImg.src.includes('/media/search_images/'))) {
                    imgContainer.innerHTML = '<div class="image-loading-spinner"></div>';
                }
            }
        }
    }

    /**
     * Hide all loading spinners
     */
    function hideAllLoadingSpinners() {
        var spinners = document.querySelectorAll('.image-loading-spinner');
        for (var i = 0; i < spinners.length; i++) {
            // Replace with "No image" placeholder
            spinners[i].parentElement.innerHTML = '<div class="search-result-no-image"><span>No image</span></div>';
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
