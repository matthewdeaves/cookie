/**
 * Play Mode — Timer UI module (ES5, iOS 9 compatible)
 * Extracted from play.js for code quality compliance.
 * Provides: createTimerWidget, addTimer, removeTimer, updateTimerCount
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.playTimers = (function() {
    'use strict';

    var PAUSE_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">'
        + '<rect x="6" y="4" width="4" height="16"></rect>'
        + '<rect x="14" y="4" width="4" height="16"></rect></svg>';

    var PLAY_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">'
        + '<polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';

    var RESET_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
        + 'stroke="currentColor" stroke-width="2.5" stroke-linecap="round">'
        + '<path d="M1 4v6h6"></path>'
        + '<path d="M3.5 15a9 9 0 105-13L1 10"></path></svg>';

    var DELETE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
        + 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        + 'stroke-linecap="round" stroke-linejoin="round">'
        + '<path d="M18 6 6 18"></path>'
        + '<path d="m6 6 12 12"></path></svg>';

    // References to DOM elements (set via setElements)
    var timerList = null;
    var timerListEmpty = null;
    var timerCount = null;

    /**
     * Set DOM element references from the page controller
     */
    function setElements(elements) {
        timerList = elements.timerList;
        timerListEmpty = elements.timerListEmpty;
        timerCount = elements.timerCount;
    }

    /**
     * Create a compact single-row timer widget element
     */
    function createTimerWidget(timer) {
        var widget = document.createElement('div');
        widget.className = 'timer-widget';
        widget.setAttribute('data-timer-id', timer.id);

        widget.innerHTML = '<div class="timer-info">'
            + '<div class="timer-label">' + Cookie.utils.escapeHtml(timer.label) + '</div>'
            + '<div class="timer-time">' + timer.formatTime() + '</div>'
            + '</div>'
            + '<div class="timer-actions">'
            + '<button type="button" class="timer-action-btn pause-btn" title="Pause">'
            + PAUSE_SVG + '</button>'
            + '<button type="button" class="timer-action-btn" title="Reset">'
            + RESET_SVG + '</button>'
            + '<button type="button" class="timer-action-btn delete-btn" title="Delete">'
            + DELETE_SVG + '</button>'
            + '</div>';

        var pauseBtn = widget.querySelector('.pause-btn');
        var resetBtn = widget.querySelector('[title="Reset"]');
        var deleteBtn = widget.querySelector('.delete-btn');

        pauseBtn.addEventListener('click', function() {
            timer.toggle();
            pauseBtn.innerHTML = timer.isRunning ? PAUSE_SVG : PLAY_SVG;
            pauseBtn.title = timer.isRunning ? 'Pause' : 'Start';
            if (timer.remaining <= 0) {
                pauseBtn.disabled = true;
            }
            updateTimerCount();
        });

        resetBtn.addEventListener('click', function() {
            timer.reset();
            pauseBtn.innerHTML = PLAY_SVG;
            pauseBtn.title = 'Start';
            pauseBtn.disabled = false;
            updateTimerCount();
        });

        deleteBtn.addEventListener('click', function() {
            removeTimer(timer.id, widget);
        });

        return widget;
    }

    /**
     * Add a new timer to the list
     */
    function addTimer(label, duration) {
        Cookie.Timer.unlockAudio();

        var timer = Cookie.Timer.create(label, duration);

        timer.onComplete = function(t) {
            Cookie.toast.success(t.label + ' timer complete!');
            var w = timerList ? timerList.querySelector('[data-timer-id="' + t.id + '"]') : null;
            if (w) {
                var pb = w.querySelector('.pause-btn');
                if (pb) {
                    pb.innerHTML = PLAY_SVG;
                    pb.title = 'Done';
                    pb.disabled = true;
                }
            }
        };

        var widget = createTimerWidget(timer);
        timer.bind(widget);

        if (timerList) {
            timerList.appendChild(widget);
        }

        if (timerListEmpty) {
            timerListEmpty.style.display = 'none';
        }

        updateTimerCount();
        timer.start();

        Cookie.toast.success('Timer added: ' + label);
    }

    /**
     * Remove a timer by ID
     */
    function removeTimer(id, widget) {
        Cookie.Timer.remove(id);
        if (widget && widget.parentNode) {
            widget.parentNode.removeChild(widget);
        }
        updateTimerCount();

        var timers = Cookie.Timer.getAll();
        if (timers.length === 0 && timerListEmpty) {
            timerListEmpty.style.display = 'block';
        }
    }

    /**
     * Update the timer count badge display
     */
    function updateTimerCount() {
        if (!timerCount) return;

        var timers = Cookie.Timer.getAll();
        var total = timers.length;
        var running = Cookie.Timer.getRunningCount();

        if (total === 0) {
            timerCount.textContent = '';
            timerCount.style.display = 'none';
        } else {
            var text = total + '';
            if (running > 0) {
                text += ' (' + running + ' active)';
            }
            timerCount.textContent = text;
            timerCount.style.display = 'inline';
        }
    }

    return {
        setElements: setElements,
        createTimerWidget: createTimerWidget,
        addTimer: addTimer,
        removeTimer: removeTimer,
        updateTimerCount: updateTimerCount
    };
})();
