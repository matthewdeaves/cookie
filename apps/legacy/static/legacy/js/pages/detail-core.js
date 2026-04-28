/**
 * Recipe Detail page - Core module (ES5, iOS 9 compatible)
 * Handles initialization and shared state.
 * Load this file FIRST, before feature modules.
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.detail = (function() {
    'use strict';

    // Shared state accessible by feature modules
    var state = {
        recipeId: null,
        profileId: null,
        currentServings: null,
        originalServings: null,
        selectedRemixSuggestion: null,
        remixSuggestions: [],
        isCreatingRemix: false,
        isScaling: false,
        isGeneratingTips: false,
        scaledIngredients: null,
        scaledInstructions: null,
        scalingNotes: [],
        adjustedTimes: null
    };

    // Tips polling state
    var tipsPollingState = {
        isPolling: false,
        pollInterval: null,
        pollStartTime: null
    };

    // Feature module references (populated by feature modules)
    var features = {
        display: null,
        favorites: null,
        collections: null,
        scaling: null,
        remix: null,
        tips: null
    };

    /**
     * Initialize a single feature module if it exists
     */
    function initFeature(name) {
        var feature = features[name];
        if (feature && feature.init) feature.init();
    }

    /**
     * Initialize all registered feature modules
     */
    function initAllFeatures() {
        var featureNames = ['display', 'favorites', 'collections', 'scaling', 'remix', 'tips'];
        for (var i = 0; i < featureNames.length; i++) {
            initFeature(featureNames[i]);
        }
    }

    /**
     * Initialize the page
     */
    function init() {
        var pageEl = document.querySelector('[data-page="recipe-detail"]');
        if (!pageEl) return;

        state.recipeId = parseInt(pageEl.getAttribute('data-recipe-id'), 10);
        state.profileId = parseInt(pageEl.getAttribute('data-profile-id'), 10);

        initAllFeatures();

        // Proactively hide AI buttons for exhausted quota features
        var aiAvailable = pageEl.getAttribute('data-ai-available') === 'true';
        if (aiAvailable) {
            checkAndApplyQuotas();
        }

        // Check if we should poll for tips (recently imported recipe with no tips)
        var scrapedAt = pageEl.getAttribute('data-scraped-at');
        var hasTips = pageEl.getAttribute('data-has-tips') === 'true';
        var tipsFeature = features.tips;

        if (scrapedAt && !hasTips && tipsFeature && tipsFeature.checkAutoStart) {
            tipsFeature.checkAutoStart(scrapedAt);
        }
    }

    /**
     * Fetch quotas and proactively hide AI feature buttons that are exhausted.
     * Mirrors the modern SPA's isFeatureAvailable() behaviour in legacy.
     */
    function checkAndApplyQuotas() {
        Cookie.ajax.get('/api/ai/quotas', function(err, data) {
            if (err || !data) return;
            if (data.unlimited) return; // unlimited user — never hide

            // Feature key → data-ai-feature selector value(s)
            var featureSelectors = {
                remix: ['[data-ai-feature="remix"]'],
                tips:  ['[data-ai-feature="tips-tab"]']
            };

            var keys = Object.keys(featureSelectors);
            for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                var used  = (data.usage  && data.usage[key])  || 0;
                var limit = (data.limits && data.limits[key]) || 0;
                if (limit > 0 && used >= limit) {
                    var selectors = featureSelectors[key];
                    for (var j = 0; j < selectors.length; j++) {
                        var el = document.querySelector(selectors[j]);
                        if (el) el.classList.add('hidden');
                    }
                }
            }
        });
    }

    /**
     * Register a feature module
     */
    function registerFeature(name, module) {
        features[name] = module;
    }

    /**
     * Get shared state
     */
    function getState() {
        return state;
    }

    /**
     * Get tips polling state
     */
    function getTipsPollingState() {
        return tipsPollingState;
    }

    /**
     * Get features
     */
    function getFeatures() {
        return features;
    }

    // Public API
    return {
        init: init,
        registerFeature: registerFeature,
        getState: getState,
        getTipsPollingState: getTipsPollingState,
        getFeatures: getFeatures
    };
})();
