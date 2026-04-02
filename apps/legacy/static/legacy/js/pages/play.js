/**
 * Play Mode page controller (ES5, iOS 9 compatible)
 * Timer UI logic is in play-timers.js (Cookie.pages.playTimers)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.play = (function() {
    'use strict';

    var instructions = [];
    var currentStep = 0;
    var totalSteps = 0;
    var panelExpanded = true;
    var aiAvailable = false;

    var elements = {};

    function init() {
        var pageEl = document.querySelector('[data-page="play-mode"]');
        if (!pageEl) return;

        aiAvailable = pageEl.getAttribute('data-ai-available') === 'true';

        var instructionsEl = document.getElementById('recipe-instructions');
        if (instructionsEl) {
            try {
                instructions = JSON.parse(instructionsEl.textContent);
            } catch (e) {
                instructions = [];
            }
        }
        totalSteps = instructions.length;
        if (totalSteps === 0) return;

        cacheElements();

        Cookie.pages.playTimers.setElements({
            timerList: elements.timerList,
            timerListEmpty: elements.timerListEmpty,
            timerCount: elements.timerCount
        });

        setupEventListeners();
        Cookie.Timer.requestPermission();
        Cookie.WakeLock.enable();

        // Expand timer panel on init (CSS starts hidden, JS controls state)
        if (elements.timerPanelContent) {
            elements.timerPanelContent.style.display = '-webkit-flex';
            elements.timerPanelContent.style.display = 'flex';
        }

        updateDisplay();
        updateDetectedTimes();
    }

    function cacheElements() {
        elements = {
            playMode: document.querySelector('.play-mode'),
            stepContent: document.querySelector('.step-content'),
            progressBar: document.getElementById('progress-bar'),
            currentStep: document.getElementById('current-step'),
            totalSteps: document.getElementById('total-steps'),
            stepNumber: document.getElementById('step-number'),
            instructionText: document.getElementById('instruction-text'),
            prevBtn: document.getElementById('prev-btn'),
            nextBtn: document.getElementById('next-btn'),
            timerPanel: document.getElementById('timer-panel'),
            timerPanelToggle: document.getElementById('timer-panel-toggle'),
            timerPanelContent: document.getElementById('timer-panel-content'),
            timerChevron: document.getElementById('timer-chevron'),
            timerCount: document.getElementById('timer-count'),
            timerList: document.getElementById('timer-list'),
            timerListEmpty: document.getElementById('timer-list-empty'),
            detectedTimes: document.getElementById('detected-times'),
            detectedTimesBtns: document.getElementById('detected-times-btns')
        };
    }

    function setupEventListeners() {
        var initMediaHandler = function() {
            Cookie.Timer.unlockAudio();
            Cookie.WakeLock.unlock();
        };
        document.addEventListener('touchstart', initMediaHandler, false);
        document.addEventListener('click', initMediaHandler, false);

        window.addEventListener('orientationchange', handleOrientationChange, false);
        window.addEventListener('resize', handleOrientationChange, false);

        var exitBtn = document.getElementById('exit-btn');
        if (exitBtn) {
            exitBtn.addEventListener('click', handleExit);
        }

        if (elements.prevBtn) {
            elements.prevBtn.addEventListener('click', handlePrevious);
        }
        if (elements.nextBtn) {
            elements.nextBtn.addEventListener('click', handleNext);
        }

        if (elements.timerPanelToggle) {
            elements.timerPanelToggle.addEventListener('click', toggleTimerPanel);
        }

        var quickBtns = document.querySelectorAll('.quick-timer-btn');
        for (var j = 0; j < quickBtns.length; j++) {
            quickBtns[j].addEventListener('click', handleQuickTimer);
        }

        document.addEventListener('keydown', handleKeyDown);
    }

    /**
     * Handle exit button click — go back without adding Play Mode to forward history
     */
    function handleExit(e) {
        e.preventDefault();
        Cookie.WakeLock.disable();

        if (window.history.length > 1) {
            window.history.back();
        } else {
            var exitBtn = document.getElementById('exit-btn');
            var recipeUrl = exitBtn ? exitBtn.getAttribute('href') : '/legacy/home/';
            window.location.href = recipeUrl;
        }
    }

    function handleOrientationChange() {
        if (elements.playMode) {
            setTimeout(function() {
                void elements.playMode.offsetHeight;
                if (elements.stepContent) {
                    elements.stepContent.scrollTop = 0;
                }
            }, 150);
        }
    }

    function handlePrevious() {
        if (currentStep > 0) {
            currentStep--;
            updateDisplay();
            updateDetectedTimes();
        }
    }

    function handleNext() {
        if (currentStep < totalSteps - 1) {
            currentStep++;
            updateDisplay();
            updateDetectedTimes();
        }
    }

    function handleKeyDown(e) {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            handlePrevious();
            e.preventDefault();
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            handleNext();
            e.preventDefault();
        } else if (e.key === 'Escape') {
            var exitBtn = document.getElementById('exit-btn');
            if (exitBtn) {
                exitBtn.click();
            }
        }
    }

    function updateDisplay() {
        var instruction = instructions[currentStep] || '';
        var progress = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 0;

        if (elements.progressBar) {
            elements.progressBar.style.width = progress + '%';
        }

        if (elements.currentStep) {
            elements.currentStep.textContent = currentStep + 1;
        }

        if (elements.stepNumber) {
            elements.stepNumber.textContent = currentStep + 1;
        }

        if (elements.instructionText) {
            elements.instructionText.textContent = instruction;
        }

        if (elements.prevBtn) {
            elements.prevBtn.disabled = currentStep === 0;
        }

        if (elements.nextBtn) {
            elements.nextBtn.disabled = currentStep === totalSteps - 1;
        }
    }

    function updateDetectedTimes() {
        if (!elements.detectedTimes || !elements.detectedTimesBtns) return;

        var instruction = instructions[currentStep] || '';
        var times = Cookie.TimeDetect.detect(instruction);

        if (times.length === 0) {
            elements.detectedTimes.classList.add('hidden');
            return;
        }

        elements.detectedTimes.classList.remove('hidden');
        elements.detectedTimesBtns.innerHTML = '';

        for (var i = 0; i < times.length; i++) {
            var seconds = times[i];
            var label = Cookie.TimeDetect.format(seconds);

            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'detected-time-btn';
            btn.setAttribute('data-duration', seconds);
            btn.setAttribute('data-label', label);
            btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
                + 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                + 'stroke-linecap="round" stroke-linejoin="round">'
                + '<path d="M12 5v14M5 12h14"></path></svg> '
                + Cookie.utils.escapeHtml(label);
            btn.addEventListener('click', handleDetectedTimer);

            elements.detectedTimesBtns.appendChild(btn);
        }
    }

    function toggleTimerPanel() {
        panelExpanded = !panelExpanded;

        if (elements.timerPanelContent) {
            if (panelExpanded) {
                elements.timerPanelContent.style.display = '-webkit-flex';
                elements.timerPanelContent.style.display = 'flex';
            } else {
                elements.timerPanelContent.style.display = 'none';
            }
        }

        if (elements.timerChevron) {
            elements.timerChevron.style.webkitTransform = panelExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
            elements.timerChevron.style.transform = panelExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
        }
    }

    /**
     * Handle quick timer button — uses AI for name if available
     */
    function handleQuickTimer(e) {
        var btn = e.currentTarget;
        var duration = parseInt(btn.getAttribute('data-duration'), 10);
        var label = btn.getAttribute('data-label');
        var instruction = instructions[currentStep] || '';

        if (aiAvailable && instruction) {
            requestAITimerName(btn, duration, label, instruction);
        } else {
            Cookie.pages.playTimers.addTimer(label, duration);
        }
    }

    /**
     * Handle detected timer button — uses AI for name if available
     */
    function handleDetectedTimer(e) {
        var btn = e.currentTarget;
        var duration = parseInt(btn.getAttribute('data-duration'), 10);
        var label = btn.getAttribute('data-label');
        var instruction = instructions[currentStep] || '';

        if (aiAvailable && instruction) {
            requestAITimerName(btn, duration, label, instruction);
        } else {
            Cookie.pages.playTimers.addTimer(label, duration);
        }
    }

    /**
     * Request AI-generated timer name, falling back to default label
     */
    function requestAITimerName(btn, duration, label, instruction) {
        btn.disabled = true;
        btn.classList.add('loading');

        var durationMinutes = Math.ceil(duration / 60);
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/ai/timer-name', true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                btn.disabled = false;
                btn.classList.remove('loading');

                if (xhr.status === 200) {
                    try {
                        var response = JSON.parse(xhr.responseText);
                        if (response.label) {
                            Cookie.pages.playTimers.addTimer(response.label, duration);
                            return;
                        }
                    } catch (parseError) {
                        // fall through
                    }
                }
                Cookie.pages.playTimers.addTimer(label, duration);
            }
        };

        xhr.onerror = function() {
            btn.disabled = false;
            btn.classList.remove('loading');
            Cookie.pages.playTimers.addTimer(label, duration);
        };

        xhr.send(JSON.stringify({
            step_text: instruction,
            duration_minutes: durationMinutes
        }));
    }

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.play.init);
    } else {
        Cookie.pages.play.init();
    }
})();
