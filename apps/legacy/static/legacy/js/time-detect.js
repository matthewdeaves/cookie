/**
 * Time detection in text (ES5, iOS 9 compatible)
 * Detects time mentions like "15 minutes", "2 hours", "30 seconds"
 */
var Cookie = Cookie || {};

Cookie.TimeDetect = (function() {
    'use strict';

    /**
     * Patterns for detecting time in text
     * Each pattern has a regex and a multiplier to convert to seconds
     */
    var patterns = [
        // Hours: "2 hours", "2 hr", "2h"
        { regex: /(\d+)\s*(?:hours?|hrs?|h)\b/gi, multiplier: 3600 },
        // Minutes: "15 minutes", "15 min", "15m"
        { regex: /(\d+)\s*(?:minutes?|mins?|m)\b/gi, multiplier: 60 },
        // Seconds: "30 seconds", "30 sec", "30s"
        { regex: /(\d+)\s*(?:seconds?|secs?|s)\b/gi, multiplier: 1 }
    ];

    /**
     * Detect time mentions in text and return durations in seconds
     * @param {string} text - Text to search for time mentions
     * @returns {Array<number>} - Array of durations in seconds
     */
    function detect(text) {
        if (!text) return [];

        var times = [];
        var seen = {}; // Track seen values to avoid duplicates

        for (var i = 0; i < patterns.length; i++) {
            var pattern = patterns[i];
            var match;

            // Reset regex lastIndex for each search
            pattern.regex.lastIndex = 0;

            while ((match = pattern.regex.exec(text)) !== null) {
                var value = parseInt(match[1], 10);
                var seconds = value * pattern.multiplier;

                // Create a unique key to avoid duplicates
                var key = match.index + '-' + value + '-' + pattern.multiplier;

                if (!seen[key] && seconds > 0) {
                    seen[key] = true;
                    times.push(seconds);
                }
            }
        }

        return times;
    }

    /**
     * Format seconds as a human-readable duration
     * @param {number} seconds - Duration in seconds
     * @returns {string} - Formatted duration string
     */
    function format(seconds) {
        if (seconds >= 3600) {
            var hrs = Math.floor(seconds / 3600);
            var mins = Math.floor((seconds % 3600) / 60);
            if (mins > 0) {
                return hrs + 'h ' + mins + 'm';
            }
            return hrs + 'h';
        }

        var minutes = Math.floor(seconds / 60);
        var secs = seconds % 60;

        if (minutes === 0) {
            return secs + ' sec';
        }
        if (secs === 0) {
            return minutes + ' min';
        }
        return minutes + 'm ' + secs + 's';
    }

    /**
     * Check if text contains any time mentions
     * @param {string} text - Text to check
     * @returns {boolean} - True if time mentions found
     */
    function hasTime(text) {
        return detect(text).length > 0;
    }

    // Public API
    return {
        detect: detect,
        format: format,
        hasTime: hasTime
    };
})();
