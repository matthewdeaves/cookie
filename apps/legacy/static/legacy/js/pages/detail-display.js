/**
 * Recipe Detail page - Display module (ES5, iOS 9 compatible)
 * Handles tab switching, meta toggle, navigation.
 */
(function() {
    'use strict';

    function init() {
        setupBackButton();
        setupMetaToggle();
        setupTabs();
        setupCookButton();
    }

    function setupBackButton() {
        var backBtn = document.getElementById('back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', handleBack);
        }
    }

    function handleBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/legacy/home/';
        }
    }

    function setupMetaToggle() {
        var metaToggle = document.getElementById('meta-toggle');
        if (metaToggle) {
            metaToggle.addEventListener('click', handleMetaToggle);
        }
    }

    function handleMetaToggle() {
        var toggle = document.getElementById('meta-toggle');
        var content = document.getElementById('meta-content');
        var chevron = document.getElementById('meta-chevron');

        if (content.classList.contains('hidden')) {
            content.classList.remove('hidden');
            toggle.classList.remove('collapsed');
            chevron.style.transform = 'rotate(0deg)';
        } else {
            content.classList.add('hidden');
            toggle.classList.add('collapsed');
            chevron.style.transform = 'rotate(180deg)';
        }
    }

    function setupTabs() {
        var tabs = document.querySelectorAll('.tab');
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].addEventListener('click', handleTabClick);
        }
    }

    function handleTabClick(e) {
        var btn = e.currentTarget;
        var tabName = btn.getAttribute('data-tab');

        // Update button states
        var allTabs = document.querySelectorAll('.tab');
        for (var i = 0; i < allTabs.length; i++) {
            allTabs[i].classList.remove('active');
        }
        btn.classList.add('active');

        // Update tab content visibility
        var allContents = document.querySelectorAll('.tab-content');
        for (var j = 0; j < allContents.length; j++) {
            allContents[j].classList.add('hidden');
        }

        var targetContent = document.getElementById('tab-' + tabName);
        if (targetContent) {
            targetContent.classList.remove('hidden');
        }

        // QA-046: Auto-generate tips when viewing Tips tab for old recipes without tips
        if (tabName === 'tips') {
            var pageEl = document.querySelector('[data-page="recipe-detail"]');
            var aiAvailable = pageEl && pageEl.getAttribute('data-ai-available') === 'true';
            var hasTips = document.querySelectorAll('.tips-list .tip-item').length > 0;
            var state = Cookie.pages.detail.getState();
            var tipsPollingState = Cookie.pages.detail.getTipsPollingState();
            var features = Cookie.pages.detail.getFeatures();

            if (aiAvailable && !hasTips && !state.isGeneratingTips && !tipsPollingState.isPolling) {
                if (features.tips && features.tips.handleGenerateTips) {
                    features.tips.handleGenerateTips(false);
                }
            }
        }
    }

    function setupCookButton() {
        var cookBtn = document.getElementById('cook-btn');
        if (cookBtn) {
            cookBtn.addEventListener('click', handleCookClick);
        }
    }

    function handleCookClick() {
        var state = Cookie.pages.detail.getState();
        window.location.href = '/legacy/recipe/' + state.recipeId + '/play/';
    }

    // Register with core module
    Cookie.pages.detail.registerFeature('display', {
        init: init
    });
})();
