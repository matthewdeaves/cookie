/**
 * Timer functionality (ES5, iOS 9 compatible)
 * CRITICAL: This must work on iOS 9 Safari
 */
var Cookie = Cookie || {};

Cookie.Timer = (function() {
    'use strict';

    var timers = [];
    var nextId = 1;

    /**
     * Timer constructor
     * @param {string} label - Timer label
     * @param {number} durationSeconds - Duration in seconds
     */
    function Timer(label, durationSeconds) {
        this.id = nextId++;
        this.label = label;
        this.duration = durationSeconds;
        this.remaining = durationSeconds;
        this.isRunning = false;
        this.intervalId = null;
        this.element = null;
        this.onComplete = null;
    }

    /**
     * Start the timer
     */
    Timer.prototype.start = function() {
        var self = this;
        if (this.isRunning) return;
        if (this.remaining <= 0) return;

        this.isRunning = true;
        this.intervalId = setInterval(function() {
            self.remaining--;
            self.render();
            if (self.remaining <= 0) {
                self.complete();
            }
        }, 1000);
        this.render();
    };

    /**
     * Pause the timer
     */
    Timer.prototype.pause = function() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.render();
    };

    /**
     * Toggle start/pause
     */
    Timer.prototype.toggle = function() {
        if (this.isRunning) {
            this.pause();
        } else {
            this.start();
        }
    };

    /**
     * Reset the timer to original duration
     */
    Timer.prototype.reset = function() {
        this.pause();
        this.remaining = this.duration;
        this.render();
    };

    /**
     * Called when timer reaches zero
     */
    Timer.prototype.complete = function() {
        this.pause();
        this.remaining = 0;
        this.render();
        Cookie.Timer.notify(this.label);
        if (this.onComplete) {
            this.onComplete(this);
        }
    };

    /**
     * Format remaining time as MM:SS or H:MM:SS
     */
    Timer.prototype.formatTime = function() {
        var totalSecs = Math.max(0, this.remaining);
        var hrs = Math.floor(totalSecs / 3600);
        var mins = Math.floor((totalSecs % 3600) / 60);
        var secs = totalSecs % 60;

        var pad = function(n) {
            return n < 10 ? '0' + n : '' + n;
        };

        if (hrs > 0) {
            return hrs + ':' + pad(mins) + ':' + pad(secs);
        }
        return mins + ':' + pad(secs);
    };

    /**
     * Update the DOM element with current state
     */
    Timer.prototype.render = function() {
        if (!this.element) return;

        var timeEl = this.element.querySelector('.timer-time');
        var toggleBtn = this.element.querySelector('.timer-toggle');
        var progressEl = this.element.querySelector('.timer-progress-bar');

        if (timeEl) {
            timeEl.textContent = this.formatTime();
        }

        if (toggleBtn) {
            toggleBtn.textContent = this.isRunning ? 'Pause' : 'Start';
            if (this.remaining <= 0) {
                toggleBtn.textContent = 'Done';
                toggleBtn.disabled = true;
            } else {
                toggleBtn.disabled = false;
            }
        }

        if (progressEl) {
            var percent = this.duration > 0
                ? ((this.duration - this.remaining) / this.duration) * 100
                : 100;
            progressEl.style.width = percent + '%';
        }

        // Add running class for visual feedback
        if (this.isRunning) {
            this.element.classList.add('timer-running');
        } else {
            this.element.classList.remove('timer-running');
        }

        // Add completed class
        if (this.remaining <= 0) {
            this.element.classList.add('timer-completed');
        } else {
            this.element.classList.remove('timer-completed');
        }
    };

    /**
     * Bind this timer to a DOM element
     */
    Timer.prototype.bind = function(element) {
        this.element = element;
        this.render();
        return this;
    };

    // ==========================================
    // Module-level functions
    // ==========================================

    /**
     * Notification handling - alert for iOS 9 compatibility
     */
    function notify(label) {
        // Try Notification API first (modern browsers)
        if ('Notification' in window && Notification.permission === 'granted') {
            try {
                new Notification('Timer Complete!', { body: label });
            } catch (e) {
                // Fallback to alert
                alert('Timer Complete: ' + label);
            }
        } else {
            // Fallback to alert for iOS 9
            alert('Timer Complete: ' + label);
        }

        // Try to play sound
        playSound();
    }

    /**
     * Play timer completion sound
     */
    function playSound() {
        try {
            // Try HTML5 audio
            var audio = new Audio('/static/legacy/audio/timer.mp3');
            audio.play();
        } catch (e) {
            // Silent fail - some browsers don't support this
        }
    }

    /**
     * Request notification permission
     */
    function requestPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                Notification.requestPermission();
            } catch (e) {
                // Not supported
            }
        }
    }

    /**
     * Create a new timer
     */
    function create(label, durationSeconds) {
        var timer = new Timer(label, durationSeconds);
        timers.push(timer);
        return timer;
    }

    /**
     * Get all timers
     */
    function getAll() {
        return timers;
    }

    /**
     * Get timer by ID
     */
    function get(id) {
        for (var i = 0; i < timers.length; i++) {
            if (timers[i].id === id) {
                return timers[i];
            }
        }
        return null;
    }

    /**
     * Remove a timer by ID
     */
    function remove(id) {
        for (var i = 0; i < timers.length; i++) {
            if (timers[i].id === id) {
                timers[i].pause();
                timers.splice(i, 1);
                return true;
            }
        }
        return false;
    }

    /**
     * Remove all timers
     */
    function clear() {
        for (var i = 0; i < timers.length; i++) {
            timers[i].pause();
        }
        timers = [];
    }

    /**
     * Get count of running timers
     */
    function getRunningCount() {
        var count = 0;
        for (var i = 0; i < timers.length; i++) {
            if (timers[i].isRunning) {
                count++;
            }
        }
        return count;
    }

    /**
     * Format duration in seconds to human readable string
     * e.g., 90 -> "1 min 30 sec", 3600 -> "1 hour"
     */
    function formatDuration(seconds) {
        if (seconds >= 3600) {
            var hrs = Math.floor(seconds / 3600);
            var mins = Math.floor((seconds % 3600) / 60);
            if (mins > 0) {
                return hrs + 'h ' + mins + 'm';
            }
            return hrs + 'h';
        }
        var mins = Math.floor(seconds / 60);
        var secs = seconds % 60;
        if (mins === 0) {
            return secs + ' sec';
        }
        if (secs === 0) {
            return mins + ' min';
        }
        return mins + 'm ' + secs + 's';
    }

    // Public API
    return {
        Timer: Timer,
        create: create,
        getAll: getAll,
        get: get,
        remove: remove,
        clear: clear,
        getRunningCount: getRunningCount,
        notify: notify,
        requestPermission: requestPermission,
        formatDuration: formatDuration
    };
})();
