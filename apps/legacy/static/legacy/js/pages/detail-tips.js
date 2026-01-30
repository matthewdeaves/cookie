/**
 * Recipe Detail page - Tips module (ES5, iOS 9 compatible)
 * Handles tips generation, polling, and display.
 */
(function() {
    'use strict';

    var TIPS_POLL_INTERVAL = 3000;
    var TIPS_MAX_POLL_DURATION = 30000;
    var TIPS_RECENT_THRESHOLD = 60000;

    function init() {
        var generateTipsBtn = document.getElementById('generate-tips-btn');
        if (generateTipsBtn) {
            generateTipsBtn.addEventListener('click', function() {
                handleGenerateTips(false);
            });
        }

        var regenerateTipsBtn = document.getElementById('regenerate-tips-btn');
        if (regenerateTipsBtn) {
            regenerateTipsBtn.addEventListener('click', function() {
                handleGenerateTips(true);
            });
        }
    }

    function checkAutoStart(scrapedAt) {
        // iOS 9 Safari compatible date parsing
        var scrapedDate = new Date(scrapedAt
            .replace('T', ' ')
            .replace(/\.\d+/, '')
            .replace(/[+-]\d{2}:\d{2}$/, '')
            .replace('Z', '')
            .replace(/-/g, '/'));
        var recipeAge = Date.now() - scrapedDate.getTime();

        if (!isNaN(recipeAge) && recipeAge < TIPS_RECENT_THRESHOLD) {
            startTipsPolling();
        }
    }

    function startTipsPolling() {
        var state = Cookie.pages.detail.getState();
        var tipsPollingState = Cookie.pages.detail.getTipsPollingState();

        if (tipsPollingState.isPolling) return;

        tipsPollingState.isPolling = true;
        tipsPollingState.pollStartTime = Date.now();

        var tipsContent = document.getElementById('tips-content');
        var tipsLoading = document.getElementById('tips-loading');
        var tipsSubtext = document.getElementById('tips-loading-subtext');

        if (tipsContent) {
            tipsContent.classList.add('hidden');
        }
        if (tipsLoading) {
            tipsLoading.classList.remove('hidden');
        }
        if (tipsSubtext) {
            tipsSubtext.classList.remove('hidden');
        }

        tipsPollingState.pollInterval = setInterval(function() {
            var elapsed = Date.now() - tipsPollingState.pollStartTime;

            if (elapsed > TIPS_MAX_POLL_DURATION) {
                stopTipsPolling(true);
                return;
            }

            Cookie.ajax.get('/api/recipes/' + state.recipeId + '/', function(error, data) {
                if (error) {
                    return;
                }

                if (data && data.ai_tips && data.ai_tips.length > 0) {
                    renderTips(data.ai_tips);
                    stopTipsPolling(false);
                }
            });
        }, TIPS_POLL_INTERVAL);
    }

    function stopTipsPolling(showEmptyState) {
        var tipsPollingState = Cookie.pages.detail.getTipsPollingState();

        if (tipsPollingState.pollInterval) {
            clearInterval(tipsPollingState.pollInterval);
            tipsPollingState.pollInterval = null;
        }
        tipsPollingState.isPolling = false;

        var tipsLoading = document.getElementById('tips-loading');
        var tipsSubtext = document.getElementById('tips-loading-subtext');

        if (tipsLoading) {
            tipsLoading.classList.add('hidden');
        }
        if (tipsSubtext) {
            tipsSubtext.classList.add('hidden');
        }

        if (showEmptyState) {
            var tipsContent = document.getElementById('tips-content');
            if (tipsContent) {
                tipsContent.classList.remove('hidden');
            }
        }
    }

    function handleGenerateTips(regenerate) {
        var state = Cookie.pages.detail.getState();
        if (state.isGeneratingTips) return;

        state.isGeneratingTips = true;

        var tipsContent = document.getElementById('tips-content');
        var tipsLoading = document.getElementById('tips-loading');

        if (tipsContent) {
            tipsContent.classList.add('hidden');
        }
        if (tipsLoading) {
            tipsLoading.classList.remove('hidden');
        }

        Cookie.ajax.post('/api/ai/tips', {
            recipe_id: state.recipeId,
            regenerate: regenerate || false
        }, function(err, response) {
            state.isGeneratingTips = false;

            if (err) {
                if (tipsContent) {
                    tipsContent.classList.remove('hidden');
                }
                if (tipsLoading) {
                    tipsLoading.classList.add('hidden');
                }
                Cookie.aiError.showError(err, 'Failed to generate tips');
                if (Cookie.aiError.shouldHideFeatures(err)) {
                    Cookie.aiError.hideAIFeatures();
                }
                return;
            }

            renderTips(response.tips);

            Cookie.toast.success(regenerate ? 'Tips regenerated!' : 'Tips generated!');
        });
    }

    function renderTips(tips) {
        var tipsContent = document.getElementById('tips-content');
        var tipsLoading = document.getElementById('tips-loading');

        if (tipsLoading) {
            tipsLoading.classList.add('hidden');
        }

        if (!tipsContent) return;

        if (!tips || tips.length === 0) {
            tipsContent.innerHTML = '<p class="empty-text">No tips available for this recipe.</p>';
            tipsContent.classList.remove('hidden');
            return;
        }

        var html = '<ol class="tips-list">';
        for (var i = 0; i < tips.length; i++) {
            html += '<li class="tip-item">';
            html += '<span class="tip-number">' + (i + 1) + '</span>';
            html += '<p class="tip-text">' + Cookie.utils.escapeHtml(tips[i]) + '</p>';
            html += '</li>';
        }
        html += '</ol>';

        html += '<div class="tips-regenerate">';
        html += '<button type="button" id="regenerate-tips-btn" class="btn btn-secondary">Regenerate Tips</button>';
        html += '</div>';

        tipsContent.innerHTML = html;
        tipsContent.classList.remove('hidden');

        var regenerateBtn = document.getElementById('regenerate-tips-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', function() {
                handleGenerateTips(true);
            });
        }
    }

    // Register with core module
    Cookie.pages.detail.registerFeature('tips', {
        init: init,
        checkAutoStart: checkAutoStart,
        handleGenerateTips: handleGenerateTips
    });
})();
