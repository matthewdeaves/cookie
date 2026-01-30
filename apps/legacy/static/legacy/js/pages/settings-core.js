/**
 * Settings page - Core module (ES5, iOS 9 compatible)
 * Handles initialization, tab switching, and shared state.
 * Load this file FIRST, before tab-specific modules.
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.settings = (function() {
    'use strict';

    // Shared state accessible by tab modules
    var state = {
        sources: [],
        profiles: [],
        currentProfileId: null,
        pendingDeleteId: null,
        resetPreview: null
    };

    // Shared DOM elements
    var elements = {
        tabBtns: null,
        tabGeneral: null,
        tabPrompts: null,
        tabSources: null,
        tabSelectors: null,
        tabUsers: null,
        tabDanger: null
    };

    // Tab module references (populated by tab modules)
    var tabs = {
        general: null,
        prompts: null,
        sources: null,
        selectors: null,
        users: null,
        danger: null
    };

    /**
     * Initialize the page
     */
    function init() {
        // Cache tab container elements
        elements.tabBtns = document.querySelectorAll('.tab-toggle-btn');
        elements.tabGeneral = document.getElementById('tab-general');
        elements.tabPrompts = document.getElementById('tab-prompts');
        elements.tabSources = document.getElementById('tab-sources');
        elements.tabSelectors = document.getElementById('tab-selectors');
        elements.tabUsers = document.getElementById('tab-users');
        elements.tabDanger = document.getElementById('tab-danger');

        // Get current profile ID from session (passed via data attribute)
        var pageElement = document.querySelector('[data-page="settings"]');
        if (pageElement && pageElement.getAttribute('data-profile-id')) {
            state.currentProfileId = parseInt(pageElement.getAttribute('data-profile-id'), 10);
        }

        // Setup tab switching
        setupTabSwitching();

        // Initialize all tab modules
        if (tabs.general && tabs.general.init) tabs.general.init();
        if (tabs.prompts && tabs.prompts.init) tabs.prompts.init();
        if (tabs.sources && tabs.sources.init) tabs.sources.init();
        if (tabs.selectors && tabs.selectors.init) tabs.selectors.init();
        if (tabs.users && tabs.users.init) tabs.users.init();
        if (tabs.danger && tabs.danger.init) tabs.danger.init();

        // Load initial data (sources are needed by both sources and selectors tabs)
        if (tabs.sources && tabs.sources.loadSources) {
            tabs.sources.loadSources();
        }
    }

    /**
     * Setup tab switching
     */
    function setupTabSwitching() {
        for (var i = 0; i < elements.tabBtns.length; i++) {
            elements.tabBtns[i].addEventListener('click', handleTabClick);
        }
    }

    /**
     * Handle tab click
     */
    function handleTabClick(e) {
        var btn = e.currentTarget;
        var tab = btn.getAttribute('data-tab');

        // Update active tab button
        for (var i = 0; i < elements.tabBtns.length; i++) {
            elements.tabBtns[i].classList.remove('active');
        }
        btn.classList.add('active');

        // Hide all tabs
        elements.tabGeneral.classList.add('hidden');
        elements.tabPrompts.classList.add('hidden');
        elements.tabSources.classList.add('hidden');
        elements.tabSelectors.classList.add('hidden');
        elements.tabUsers.classList.add('hidden');
        elements.tabDanger.classList.add('hidden');

        // Show selected tab and trigger tab-specific actions
        if (tab === 'general') {
            elements.tabGeneral.classList.remove('hidden');
        } else if (tab === 'prompts') {
            elements.tabPrompts.classList.remove('hidden');
        } else if (tab === 'sources') {
            elements.tabSources.classList.remove('hidden');
        } else if (tab === 'selectors') {
            elements.tabSelectors.classList.remove('hidden');
        } else if (tab === 'users') {
            elements.tabUsers.classList.remove('hidden');
            // Load profiles when users tab is shown
            if (state.profiles.length === 0 && tabs.users && tabs.users.loadProfiles) {
                tabs.users.loadProfiles();
            }
        } else if (tab === 'danger') {
            elements.tabDanger.classList.remove('hidden');
        }
    }

    /**
     * Register a tab module
     */
    function registerTab(name, module) {
        tabs[name] = module;
    }

    /**
     * Get shared state
     */
    function getState() {
        return state;
    }

    /**
     * Get shared elements
     */
    function getElements() {
        return elements;
    }

    // Public API
    return {
        init: init,
        registerTab: registerTab,
        getState: getState,
        getElements: getElements
    };
})();
