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
     * Cache all tab container elements
     */
    function cacheElements() {
        elements.tabBtns = document.querySelectorAll('.tab-toggle-btn');
        var tabNames = ['General', 'Prompts', 'Sources', 'Selectors', 'Users', 'Danger'];
        for (var i = 0; i < tabNames.length; i++) {
            var name = tabNames[i].toLowerCase();
            elements['tab' + tabNames[i]] = document.getElementById('tab-' + name);
        }
    }

    /**
     * Initialize a single tab module if it exists
     */
    function initTab(name) {
        var tab = tabs[name];
        if (tab && tab.init) tab.init();
    }

    /**
     * Initialize all registered tab modules
     */
    function initAllTabs() {
        var tabNames = ['general', 'prompts', 'sources', 'selectors', 'users', 'danger'];
        for (var i = 0; i < tabNames.length; i++) {
            initTab(tabNames[i]);
        }
    }

    /**
     * Initialize the page
     */
    function init() {
        cacheElements();

        // Get current profile ID from session (passed via data attribute)
        var pageElement = document.querySelector('[data-page="settings"]');
        if (pageElement && pageElement.getAttribute('data-profile-id')) {
            state.currentProfileId = parseInt(pageElement.getAttribute('data-profile-id'), 10);
        }

        setupTabSwitching();
        initAllTabs();

        // Load initial data (sources are needed by both sources and selectors tabs)
        var sourcesTab = tabs.sources;
        if (sourcesTab && sourcesTab.loadSources) {
            sourcesTab.loadSources();
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
     * Hide all tab panels
     */
    function hideAllTabs() {
        var tabNames = ['General', 'Prompts', 'Sources', 'Selectors', 'Users', 'Danger'];
        for (var i = 0; i < tabNames.length; i++) {
            var el = elements['tab' + tabNames[i]];
            if (el) el.classList.add('hidden');
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

        hideAllTabs();

        // Show selected tab
        var tabKey = 'tab' + tab.charAt(0).toUpperCase() + tab.slice(1);
        var tabEl = elements[tabKey];
        if (tabEl) tabEl.classList.remove('hidden');

        // Load profiles lazily when users tab is shown
        if (tab === 'users' && state.profiles.length === 0) {
            var usersTab = tabs.users;
            if (usersTab && usersTab.loadProfiles) usersTab.loadProfiles();
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
