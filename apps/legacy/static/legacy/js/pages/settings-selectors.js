/**
 * Settings page - Selectors tab (ES5, iOS 9 compatible)
 * Handles CSS selector testing and editing.
 */
(function() {
    'use strict';

    var selectorsList;
    var testAllBtn;
    var testAllText;

    function init() {
        selectorsList = document.getElementById('selectors-list');
        testAllBtn = document.getElementById('test-all-btn');
        testAllText = document.getElementById('test-all-text');

        if (testAllBtn) {
            testAllBtn.addEventListener('click', handleTestAllSources);
        }

        // Event delegation for dynamically rendered selector buttons
        if (selectorsList) {
            Cookie.utils.delegate(selectorsList, 'click', {
                'test-source': handleTestSource,
                'edit-selector': handleEditSelector,
                'cancel-edit': handleCancelEditSelector,
                'save-selector': handleSaveSelector
            });
        }
    }

    function renderSelectors() {
        var sources = Cookie.pages.settings.getState().sources;
        var template = document.getElementById('template-selector-item');

        if (!template || !selectorsList) return;

        var fragment = document.createDocumentFragment();

        for (var i = 0; i < sources.length; i++) {
            var source = sources[i];
            var clone = template.content.cloneNode(true);
            var item = clone.querySelector('.selector-item');

            item.setAttribute('data-source-id', source.id);

            clone.querySelector('[data-field="name"]').textContent = source.name;
            clone.querySelector('[data-field="host"]').textContent = source.host;
            clone.querySelector('[data-field="last-tested"]').textContent = 'Last tested: ' + Cookie.utils.formatRelativeTime(source.last_validated_at);
            clone.querySelector('[data-field="selector-value"]').textContent = source.result_selector || '(none)';

            var status = getSourceStatus(source);
            clone.querySelector('[data-field="status-icon"]').innerHTML = getStatusIcon(status);

            var failureWarning = clone.querySelector('[data-field="failure-warning"]');
            if (source.consecutive_failures >= 3) {
                failureWarning.textContent = 'Failed ' + source.consecutive_failures + ' times - auto-disabled';
                failureWarning.classList.remove('hidden');
            }

            clone.querySelector('[data-action="test-source"]').setAttribute('data-source-id', source.id);
            clone.querySelector('[data-action="edit-selector"]').setAttribute('data-source-id', source.id);
            clone.querySelector('[data-action="cancel-edit"]').setAttribute('data-source-id', source.id);
            clone.querySelector('[data-action="save-selector"]').setAttribute('data-source-id', source.id);

            clone.querySelector('.selector-input-row').setAttribute('data-source-id', source.id);
            clone.querySelector('.selector-edit-row').setAttribute('data-source-id', source.id);
            clone.querySelector('[data-field="selector"]').value = source.result_selector || '';

            fragment.appendChild(clone);
        }

        selectorsList.innerHTML = '';
        selectorsList.appendChild(fragment);
    }

    function getSourceStatus(source) {
        if (!source.last_validated_at) return 'untested';
        if (source.needs_attention || source.consecutive_failures >= 3) return 'broken';
        return 'working';
    }

    function getStatusIcon(status) {
        if (status === 'working') {
            return '<svg class="status-icon status-working" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
        } else if (status === 'broken') {
            return '<svg class="status-icon status-broken" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
        } else {
            return '<svg class="status-icon status-untested" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
        }
    }

    function handleTestSource(e) {
        var btn = e.delegateTarget || e.currentTarget;
        var sourceId = parseInt(btn.getAttribute('data-source-id'), 10);
        var btnText = btn.querySelector('.test-btn-text');

        btn.disabled = true;
        btnText.textContent = 'Testing...';

        Cookie.ajax.post('/api/sources/' + sourceId + '/test/', {}, function(err, result) {
            btn.disabled = false;
            btnText.textContent = 'Test';

            if (err) {
                Cookie.toast.error('Failed to test source');
                return;
            }

            if (result.success) {
                Cookie.toast.success(result.message);
            } else {
                Cookie.toast.error(result.message);
            }

            // Reload sources to get updated status
            var sourcesTab = Cookie.pages.settings.registerTab && Cookie.pages.settings;
            if (sourcesTab && sourcesTab.tabs && sourcesTab.tabs.sources && sourcesTab.tabs.sources.loadSources) {
                sourcesTab.tabs.sources.loadSources();
            }
        });
    }

    function handleTestAllSources() {
        testAllBtn.disabled = true;
        testAllText.textContent = 'Testing...';

        Cookie.ajax.post('/api/sources/test-all/', {}, function(err, result) {
            testAllBtn.disabled = false;
            testAllText.textContent = 'Test All Sources';

            if (err) {
                Cookie.toast.error('Failed to test sources');
                return;
            }

            Cookie.toast.success('Tested ' + result.tested + ' sources: ' + result.passed + ' passed, ' + result.failed + ' failed');

            // Reload sources to get updated status
            var sourcesTab = Cookie.pages.settings.registerTab && Cookie.pages.settings;
            if (sourcesTab && sourcesTab.tabs && sourcesTab.tabs.sources && sourcesTab.tabs.sources.loadSources) {
                sourcesTab.tabs.sources.loadSources();
            }
        });
    }

    function handleEditSelector(e) {
        var target = e.delegateTarget || e.currentTarget;
        var sourceId = target.getAttribute('data-source-id');
        var inputRow = selectorsList.querySelector('.selector-input-row[data-source-id="' + sourceId + '"]');
        var editRow = selectorsList.querySelector('.selector-edit-row[data-source-id="' + sourceId + '"]');

        inputRow.classList.add('hidden');
        editRow.classList.remove('hidden');
    }

    function handleCancelEditSelector(e) {
        var target = e.delegateTarget || e.currentTarget;
        var sourceId = target.getAttribute('data-source-id');
        var inputRow = selectorsList.querySelector('.selector-input-row[data-source-id="' + sourceId + '"]');
        var editRow = selectorsList.querySelector('.selector-edit-row[data-source-id="' + sourceId + '"]');

        editRow.classList.add('hidden');
        inputRow.classList.remove('hidden');
    }

    function handleSaveSelector(e) {
        var btn = e.delegateTarget || e.currentTarget;
        var sourceId = parseInt(btn.getAttribute('data-source-id'), 10);
        var editRow = selectorsList.querySelector('.selector-edit-row[data-source-id="' + sourceId + '"]');
        var input = editRow.querySelector('[data-field="selector"]');
        var newSelector = input.value;
        var state = Cookie.pages.settings.getState();

        btn.disabled = true;
        btn.textContent = 'Saving...';

        Cookie.ajax.put('/api/sources/' + sourceId + '/selector/', { result_selector: newSelector }, function(err, result) {
            btn.disabled = false;
            btn.textContent = 'Save';

            if (err) {
                Cookie.toast.error('Failed to update selector');
                return;
            }

            Cookie.toast.success('Selector updated');

            for (var i = 0; i < state.sources.length; i++) {
                if (state.sources[i].id === sourceId) {
                    state.sources[i].result_selector = newSelector;
                    break;
                }
            }

            renderSelectors();
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('selectors', {
        init: init,
        renderSelectors: renderSelectors
    });
})();
