/**
 * Play Mode page controller (ES5, iOS 9 compatible)
 * CRITICAL: Timers must work on iOS 9
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.play = (function() {
    'use strict';

    // State
    var instructions = [];
    var currentStep = 0;
    var totalSteps = 0;
    var panelExpanded = true;

    // DOM elements
    var elements = {};

    /**
     * Initialize the page
     */
    function init() {
        var pageEl = document.querySelector('[data-page="play-mode"]');
        if (!pageEl) return;

        // Get instructions from global variable
        if (typeof RECIPE_INSTRUCTIONS !== 'undefined') {
            instructions = RECIPE_INSTRUCTIONS;
        }
        totalSteps = instructions.length;

        if (totalSteps === 0) return;

        // Cache DOM elements
        cacheElements();

        // Setup event listeners
        setupEventListeners();

        // Request notification permission
        Cookie.Timer.requestPermission();

        // Enable wake lock to prevent screen sleep during cooking
        Cookie.WakeLock.enable();

        // Initial render
        updateDisplay();
        updateDetectedTimes();
    }

    /**
     * Cache DOM element references
     */
    function cacheElements() {
        elements = {
            progressBar: document.getElementById('progress-bar'),
            currentStep: document.getElementById('current-step'),
            totalSteps: document.getElementById('total-steps'),
            stepNumber: document.getElementById('step-number'),
            instructionText: document.getElementById('instruction-text'),
            prevBtn: document.getElementById('prev-btn'),
            nextBtn: document.getElementById('next-btn'),
            stepIndicators: document.getElementById('step-indicators'),
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

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Initialize audio and wake lock on first user interaction (iOS Safari requirement)
        // This MUST be called from touchstart/click to enable audio/video playback later
        var initMediaHandler = function() {
            Cookie.Timer.unlockAudio();
            Cookie.WakeLock.unlock();
        };
        document.addEventListener('touchstart', initMediaHandler, false);
        document.addEventListener('click', initMediaHandler, false);

        // Exit button - use location.replace() to avoid Play Mode in history
        var exitBtn = document.getElementById('exit-btn');
        if (exitBtn) {
            exitBtn.addEventListener('click', handleExit);
        }

        // Navigation buttons
        if (elements.prevBtn) {
            elements.prevBtn.addEventListener('click', handlePrevious);
        }
        if (elements.nextBtn) {
            elements.nextBtn.addEventListener('click', handleNext);
        }

        // Step indicators
        var dots = document.querySelectorAll('.step-dot');
        for (var i = 0; i < dots.length; i++) {
            dots[i].addEventListener('click', handleDotClick);
        }

        // Timer panel toggle
        if (elements.timerPanelToggle) {
            elements.timerPanelToggle.addEventListener('click', toggleTimerPanel);
        }

        // Quick timer buttons
        var quickBtns = document.querySelectorAll('.quick-timer-btn');
        for (var j = 0; j < quickBtns.length; j++) {
            quickBtns[j].addEventListener('click', handleQuickTimer);
        }

        // Keyboard navigation
        document.addEventListener('keydown', handleKeyDown);
    }

    /**
     * Handle exit button click
     * Uses history.back() to return to Recipe Detail without adding Play Mode
     * to the forward history. This ensures the back button from Recipe Detail
     * goes to the page before it (e.g., Home), not back to Play Mode.
     */
    function handleExit(e) {
        e.preventDefault();

        // Disable wake lock when leaving Play Mode
        Cookie.WakeLock.disable();

        // Go back to the previous page (Recipe Detail)
        // This effectively removes Play Mode from the navigation flow
        if (window.history.length > 1) {
            window.history.back();
        } else {
            // Fallback if no history (direct URL access)
            var exitBtn = document.getElementById('exit-btn');
            var recipeUrl = exitBtn ? exitBtn.getAttribute('href') : '/legacy/home/';
            window.location.href = recipeUrl;
        }
    }

    /**
     * Handle previous button click
     */
    function handlePrevious() {
        if (currentStep > 0) {
            currentStep--;
            updateDisplay();
            updateDetectedTimes();
        }
    }

    /**
     * Handle next button click
     */
    function handleNext() {
        if (currentStep < totalSteps - 1) {
            currentStep++;
            updateDisplay();
            updateDetectedTimes();
        }
    }

    /**
     * Handle step dot click
     */
    function handleDotClick(e) {
        var step = parseInt(e.currentTarget.getAttribute('data-step'), 10);
        if (!isNaN(step) && step >= 0 && step < totalSteps) {
            currentStep = step;
            updateDisplay();
            updateDetectedTimes();
        }
    }

    /**
     * Handle keyboard navigation
     */
    function handleKeyDown(e) {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            handlePrevious();
            e.preventDefault();
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            handleNext();
            e.preventDefault();
        } else if (e.key === 'Escape') {
            // Exit - go back
            var exitBtn = document.getElementById('exit-btn');
            if (exitBtn) {
                exitBtn.click();
            }
        }
    }

    /**
     * Update the display with current step
     */
    function updateDisplay() {
        var instruction = instructions[currentStep] || '';
        var progress = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 0;

        // Update progress bar
        if (elements.progressBar) {
            elements.progressBar.style.width = progress + '%';
        }

        // Update step counter
        if (elements.currentStep) {
            elements.currentStep.textContent = currentStep + 1;
        }

        // Update step number badge
        if (elements.stepNumber) {
            elements.stepNumber.textContent = currentStep + 1;
        }

        // Update instruction text
        if (elements.instructionText) {
            elements.instructionText.textContent = instruction;
        }

        // Update navigation buttons
        if (elements.prevBtn) {
            elements.prevBtn.disabled = currentStep === 0;
            if (currentStep === 0) {
                elements.prevBtn.classList.add('disabled');
            } else {
                elements.prevBtn.classList.remove('disabled');
            }
        }

        if (elements.nextBtn) {
            elements.nextBtn.disabled = currentStep === totalSteps - 1;
            if (currentStep === totalSteps - 1) {
                elements.nextBtn.classList.add('disabled');
            } else {
                elements.nextBtn.classList.remove('disabled');
            }
        }

        // Update step indicators
        var dots = document.querySelectorAll('.step-dot');
        for (var i = 0; i < dots.length; i++) {
            dots[i].classList.remove('active', 'completed');
            if (i === currentStep) {
                dots[i].classList.add('active');
            } else if (i < currentStep) {
                dots[i].classList.add('completed');
            }
        }
    }

    /**
     * Update detected times for current step
     */
    function updateDetectedTimes() {
        if (!elements.detectedTimes || !elements.detectedTimesBtns) return;

        var instruction = instructions[currentStep] || '';
        var times = Cookie.TimeDetect.detect(instruction);

        if (times.length === 0) {
            elements.detectedTimes.style.display = 'none';
            return;
        }

        elements.detectedTimes.style.display = 'block';
        elements.detectedTimesBtns.innerHTML = '';

        for (var i = 0; i < times.length; i++) {
            var seconds = times[i];
            var label = Cookie.TimeDetect.format(seconds);

            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'detected-time-btn';
            btn.setAttribute('data-duration', seconds);
            btn.setAttribute('data-label', label);
            btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"></path></svg> ' + label;
            btn.addEventListener('click', handleDetectedTimer);

            elements.detectedTimesBtns.appendChild(btn);
        }
    }

    /**
     * Toggle timer panel expanded/collapsed
     */
    function toggleTimerPanel() {
        panelExpanded = !panelExpanded;

        if (elements.timerPanelContent) {
            if (panelExpanded) {
                elements.timerPanelContent.style.display = 'block';
            } else {
                elements.timerPanelContent.style.display = 'none';
            }
        }

        if (elements.timerChevron) {
            if (panelExpanded) {
                elements.timerChevron.style.transform = 'rotate(0deg)';
            } else {
                elements.timerChevron.style.transform = 'rotate(180deg)';
            }
        }
    }

    /**
     * Handle quick timer button click
     */
    function handleQuickTimer(e) {
        var btn = e.currentTarget;
        var duration = parseInt(btn.getAttribute('data-duration'), 10);
        var label = btn.getAttribute('data-label');
        addTimer(label, duration);
    }

    /**
     * Handle detected timer button click
     */
    function handleDetectedTimer(e) {
        var btn = e.currentTarget;
        var duration = parseInt(btn.getAttribute('data-duration'), 10);
        var label = btn.getAttribute('data-label');
        addTimer(label, duration);
    }

    /**
     * Add a new timer
     */
    function addTimer(label, duration) {
        // Unlock audio on user interaction (iOS requires this)
        Cookie.Timer.unlockAudio();

        var timer = Cookie.Timer.create(label, duration);

        // Set up completion callback to show toast
        timer.onComplete = function(t) {
            Cookie.toast.success(t.label + ' timer complete!');
        };

        // Create timer widget element
        var widget = createTimerWidget(timer);
        timer.bind(widget);

        // Add to list
        if (elements.timerList) {
            elements.timerList.appendChild(widget);
        }

        // Hide empty message
        if (elements.timerListEmpty) {
            elements.timerListEmpty.style.display = 'none';
        }

        // Update count
        updateTimerCount();

        // Auto-start the timer
        timer.start();

        // Show toast
        Cookie.toast.success('Timer added: ' + label);
    }

    /**
     * Create a timer widget element
     */
    function createTimerWidget(timer) {
        var widget = document.createElement('div');
        widget.className = 'timer-widget';
        widget.setAttribute('data-timer-id', timer.id);

        widget.innerHTML = [
            '<div class="timer-info">',
            '  <span class="timer-label">' + escapeHtml(timer.label) + '</span>',
            '  <span class="timer-time">' + timer.formatTime() + '</span>',
            '</div>',
            '<div class="timer-progress">',
            '  <div class="timer-progress-bar"></div>',
            '</div>',
            '<div class="timer-actions">',
            '  <button type="button" class="timer-toggle btn-timer">Pause</button>',
            '  <button type="button" class="timer-reset btn-timer-secondary">Reset</button>',
            '  <button type="button" class="timer-delete btn-timer-danger">',
            '    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">',
            '      <path d="M18 6 6 18"></path>',
            '      <path d="m6 6 12 12"></path>',
            '    </svg>',
            '  </button>',
            '</div>'
        ].join('');

        // Bind events
        var toggleBtn = widget.querySelector('.timer-toggle');
        var resetBtn = widget.querySelector('.timer-reset');
        var deleteBtn = widget.querySelector('.timer-delete');

        toggleBtn.addEventListener('click', function() {
            timer.toggle();
            updateTimerCount();
        });

        resetBtn.addEventListener('click', function() {
            timer.reset();
            updateTimerCount();
        });

        deleteBtn.addEventListener('click', function() {
            removeTimer(timer.id, widget);
        });

        return widget;
    }

    /**
     * Remove a timer
     */
    function removeTimer(id, widget) {
        Cookie.Timer.remove(id);
        if (widget && widget.parentNode) {
            widget.parentNode.removeChild(widget);
        }
        updateTimerCount();

        // Show empty message if no timers
        var timers = Cookie.Timer.getAll();
        if (timers.length === 0 && elements.timerListEmpty) {
            elements.timerListEmpty.style.display = 'block';
        }
    }

    /**
     * Update the timer count display
     */
    function updateTimerCount() {
        if (!elements.timerCount) return;

        var timers = Cookie.Timer.getAll();
        var total = timers.length;
        var running = Cookie.Timer.getRunningCount();

        if (total === 0) {
            elements.timerCount.textContent = '';
            elements.timerCount.style.display = 'none';
        } else {
            var text = total + '';
            if (running > 0) {
                text += ' (' + running + ' active)';
            }
            elements.timerCount.textContent = text;
            elements.timerCount.style.display = 'inline';
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
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
