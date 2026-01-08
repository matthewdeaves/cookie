/**
 * Timer functionality (ES5, iOS 9 compatible)
 * CRITICAL: This must work on iOS 9 Safari
 * Uses Web Audio API with webkitAudioContext fallback
 */
var Cookie = Cookie || {};

Cookie.Timer = (function() {
    'use strict';

    var timers = [];
    var nextId = 1;

    // Web Audio API context (created lazily on user gesture)
    var audioContext = null;
    var audioInitialized = false;

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
    // Audio functions using Web Audio API
    // ==========================================

    /**
     * Initialize AudioContext on user gesture (required for iOS)
     * Uses webkitAudioContext fallback for iOS 9 Safari
     */
    function initAudio() {
        if (audioContext) {
            // Already initialized, just resume if suspended
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            return;
        }

        try {
            // Use webkitAudioContext for iOS 9 Safari
            var AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                audioContext = new AudioContextClass();
                audioInitialized = true;
            }
        } catch (e) {
            // Web Audio API not supported
        }

        // Resume if suspended (iOS autoplay policy)
        if (audioContext && audioContext.state === 'suspended') {
            audioContext.resume();
        }
    }

    /**
     * Play alarm sound - 3 beeps at 880 Hz (A5 note)
     * Uses square wave for harsh, attention-grabbing sound
     */
    function playAlarmSound() {
        if (!audioContext) {
            return;
        }

        // Resume if suspended
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }

        try {
            var ctx = audioContext;
            var now = ctx.currentTime;

            // Play 3 beeps
            for (var i = 0; i < 3; i++) {
                var startTime = now + (i * 0.3);

                var oscillator = ctx.createOscillator();
                var gainNode = ctx.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(ctx.destination);

                // 880 Hz = A5 note, square wave for harsh beep
                oscillator.frequency.value = 880;
                oscillator.type = 'square';

                // Volume envelope (attack, sustain, release)
                gainNode.gain.setValueAtTime(0.5, startTime);
                gainNode.gain.setValueAtTime(0.5, startTime + 0.12);
                gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.15);

                oscillator.start(startTime);
                oscillator.stop(startTime + 0.15);
            }
        } catch (e) {
            // Silent fail
        }
    }

    // ==========================================
    // Module-level functions
    // ==========================================

    /**
     * Notification handling - play sound only (no alert)
     */
    function notify(label) {
        // Play alarm sound
        playAlarmSound();

        // Try Notification API for desktop browsers (optional, non-blocking)
        if ('Notification' in window && Notification.permission === 'granted') {
            try {
                new Notification('Timer Complete!', { body: label });
            } catch (e) {
                // Ignore notification errors
            }
        }
        // No alert() - just play the sound and show toast
    }

    /**
     * Initialize audio on user interaction (iOS requires this)
     * Call this from touchstart/click handlers
     */
    function unlockAudio() {
        initAudio();
    }

    /**
     * Request notification permission and initialize audio
     */
    function requestPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                Notification.requestPermission();
            } catch (e) {
                // Not supported
            }
        }
        // Initialize audio context (called from user interaction context)
        initAudio();
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
        unlockAudio: unlockAudio,
        formatDuration: formatDuration
    };
})();
