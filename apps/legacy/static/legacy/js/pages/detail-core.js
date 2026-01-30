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
     * Initialize the page
     */
    function init() {
        var pageEl = document.querySelector('[data-page="recipe-detail"]');
        if (!pageEl) return;

        state.recipeId = parseInt(pageEl.getAttribute('data-recipe-id'), 10);
        state.profileId = parseInt(pageEl.getAttribute('data-profile-id'), 10);

        // Initialize all feature modules
        if (features.display && features.display.init) features.display.init();
        if (features.favorites && features.favorites.init) features.favorites.init();
        if (features.collections && features.collections.init) features.collections.init();
        if (features.scaling && features.scaling.init) features.scaling.init();
        if (features.remix && features.remix.init) features.remix.init();
        if (features.tips && features.tips.init) features.tips.init();

        // Check if we should poll for tips (recently imported recipe with no tips)
        var scrapedAt = pageEl.getAttribute('data-scraped-at');
        var hasTips = pageEl.getAttribute('data-has-tips') === 'true';

        if (scrapedAt && !hasTips && features.tips && features.tips.checkAutoStart) {
            features.tips.checkAutoStart(scrapedAt);
        }
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
