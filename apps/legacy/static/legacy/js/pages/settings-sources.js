/**
 * Settings page - Sources tab (ES5, iOS 9 compatible)
 * Handles recipe source enabling/disabling.
 */
(function() {
    'use strict';

    var sourcesCounter;
    var sourcesList;
    var enableAllBtn;
    var disableAllBtn;

    function init() {
        sourcesCounter = document.getElementById('sources-counter');
        sourcesList = document.getElementById('sources-list');
        enableAllBtn = document.getElementById('enable-all-btn');
        disableAllBtn = document.getElementById('disable-all-btn');

        if (enableAllBtn) {
            enableAllBtn.addEventListener('click', function() {
                bulkToggleSources(true);
            });
        }
        if (disableAllBtn) {
            disableAllBtn.addEventListener('click', function() {
                bulkToggleSources(false);
            });
        }

        // Event delegation for dynamically rendered source toggle buttons
        if (sourcesList) {
            Cookie.utils.delegate(sourcesList, 'click', {
                'toggle-source': handleToggleSource
            });
        }
    }

    function loadSources() {
        var state = Cookie.pages.settings.getState();

        Cookie.ajax.get('/api/sources/', function(err, result) {
            if (err) {
                sourcesList.innerHTML = '<div class="error-placeholder">Failed to load sources</div>';
                return;
            }

            state.sources = result;
            renderSources();
            updateSourcesCounter();

            // Also trigger selectors render if that tab module is loaded
            var selectorsTab = Cookie.pages.settings.registerTab && Cookie.pages.settings;
            if (selectorsTab && selectorsTab.tabs && selectorsTab.tabs.selectors && selectorsTab.tabs.selectors.renderSelectors) {
                selectorsTab.tabs.selectors.renderSelectors();
            }
        });
    }

    function updateSourcesCounter() {
        var sources = Cookie.pages.settings.getState().sources;
        var enabled = 0;
        for (var i = 0; i < sources.length; i++) {
            if (sources[i].is_enabled) enabled++;
        }
        sourcesCounter.textContent = enabled + ' of ' + sources.length + ' sources currently enabled';
    }

    function renderSources() {
        var sources = Cookie.pages.settings.getState().sources;
        var template = document.getElementById('template-source-item');
        var fragment = document.createDocumentFragment();

        for (var i = 0; i < sources.length; i++) {
            var source = sources[i];
            var clone = template.content.cloneNode(true);
            var item = clone.querySelector('.source-item');

            item.setAttribute('data-source-id', source.id);
            item.classList.add(source.is_enabled ? 'source-enabled' : 'source-disabled');

            clone.querySelector('[data-field="name"]').textContent = source.name;
            clone.querySelector('[data-field="host"]').textContent = source.host;

            var badge = clone.querySelector('[data-field="badge"]');
            if (source.is_enabled) {
                badge.textContent = 'Active';
            } else {
                badge.style.display = 'none';
            }

            var btn = clone.querySelector('[data-action="toggle-source"]');
            btn.setAttribute('data-source-id', source.id);
            btn.innerHTML = source.is_enabled
                ? '<svg class="toggle-icon toggle-on" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><rect x="1" y="5" width="22" height="14" rx="7" ry="7"></rect><circle cx="16" cy="12" r="4" fill="var(--background)"></circle></svg>'
                : '<svg class="toggle-icon toggle-off" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="5" width="22" height="14" rx="7" ry="7"></rect><circle cx="8" cy="12" r="3"></circle></svg>';

            fragment.appendChild(clone);
        }

        sourcesList.innerHTML = '';
        sourcesList.appendChild(fragment);
    }

    function handleToggleSource(e) {
        var btn = e.delegateTarget || e.currentTarget;
        var sourceId = parseInt(btn.getAttribute('data-source-id'), 10);
        var state = Cookie.pages.settings.getState();

        btn.disabled = true;

        Cookie.ajax.post('/api/sources/' + sourceId + '/toggle/', {}, function(err, result) {
            btn.disabled = false;

            if (err) {
                Cookie.toast.error('Failed to toggle source');
                return;
            }

            for (var i = 0; i < state.sources.length; i++) {
                if (state.sources[i].id === sourceId) {
                    state.sources[i].is_enabled = result.is_enabled;
                    break;
                }
            }

            renderSources();
            updateSourcesCounter();
        });
    }

    function bulkToggleSources(enable) {
        var state = Cookie.pages.settings.getState();

        enableAllBtn.disabled = true;
        disableAllBtn.disabled = true;

        Cookie.ajax.post('/api/sources/bulk-toggle/', { enable: enable }, function(err, result) {
            enableAllBtn.disabled = false;
            disableAllBtn.disabled = false;

            if (err) {
                Cookie.toast.error('Failed to update sources');
                return;
            }

            for (var i = 0; i < state.sources.length; i++) {
                state.sources[i].is_enabled = enable;
            }

            renderSources();
            updateSourcesCounter();
            Cookie.toast.success(enable ? 'All sources enabled' : 'All sources disabled');
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('sources', {
        init: init,
        loadSources: loadSources,
        renderSources: renderSources,
        updateSourcesCounter: updateSourcesCounter
    });
})();
