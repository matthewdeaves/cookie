/**
 * Shared utility functions (ES5, iOS 9 compatible)
 *
 * These utilities are used across multiple page modules to eliminate duplication.
 * Load this file BEFORE page-specific modules in base.html.
 */
var Cookie = Cookie || {};

Cookie.utils = (function() {
    'use strict';

    /**
     * Escape HTML special characters to prevent XSS
     * Creates a text node to safely escape user input for HTML display.
     *
     * @param {string} str - The string to escape
     * @returns {string} HTML-escaped string
     */
    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    /**
     * Format minutes as human-readable time
     * Examples: 45 -> "45 min", 90 -> "1h 30m", 120 -> "2h"
     *
     * @param {number} minutes - Number of minutes
     * @returns {string|null} Formatted time string or null if no minutes
     */
    function formatTime(minutes) {
        if (!minutes) return null;
        minutes = parseInt(minutes, 10);
        if (isNaN(minutes)) return null;

        if (minutes < 60) {
            return minutes + ' min';
        }
        var hours = Math.floor(minutes / 60);
        var mins = minutes % 60;
        return mins > 0 ? hours + 'h ' + mins + 'm' : hours + 'h';
    }

    /**
     * Show an element by removing the 'hidden' class
     *
     * @param {HTMLElement} el - The element to show
     */
    function showElement(el) {
        if (el) {
            el.classList.remove('hidden');
        }
    }

    /**
     * Hide an element by adding the 'hidden' class
     *
     * @param {HTMLElement} el - The element to hide
     */
    function hideElement(el) {
        if (el) {
            el.classList.add('hidden');
        }
    }

    /**
     * Truncate a string to a maximum length with ellipsis
     *
     * @param {string} str - The string to truncate
     * @param {number} length - Maximum length before truncation
     * @returns {string} Truncated string with "..." if needed
     */
    function truncate(str, length) {
        if (!str) return '';
        if (str.length <= length) return str;
        return str.substring(0, length) + '...';
    }

    /**
     * Format a number with thousands separators (ES5 compatible)
     * Example: 1234567 -> "1,234,567"
     *
     * @param {number} num - The number to format
     * @returns {string} Formatted number string
     */
    function formatNumber(num) {
        if (!num && num !== 0) return '';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /**
     * Escape special characters for use in CSS attribute selectors
     *
     * @param {string} str - The string to escape for CSS
     * @returns {string} CSS-escaped string
     */
    function escapeSelector(str) {
        if (!str) return '';
        // Escape all special CSS characters: !"#$%&'()*+,./:;<=>?@[\]^`{|}~
        return str.replace(/([!"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~])/g, '\\$1');
    }

    /**
     * Format a relative time string from a date
     * Examples: "Just now", "5m ago", "2h ago", "3d ago"
     *
     * @param {string} dateStr - ISO date string
     * @returns {string} Relative time description
     */
    function formatRelativeTime(dateStr) {
        if (!dateStr) return 'Never';
        var date = new Date(dateStr);
        var now = new Date();
        var diffMs = now.getTime() - date.getTime();
        var diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return diffMins + 'm ago';
        var diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return diffHours + 'h ago';
        var diffDays = Math.floor(diffHours / 24);
        return diffDays + 'd ago';
    }

    /**
     * Format a date for display (localized date string)
     *
     * @param {string} dateStr - ISO date string
     * @returns {string} Localized date string
     */
    function formatDate(dateStr) {
        if (!dateStr) return 'Unknown';
        var date = new Date(dateStr);
        return date.toLocaleDateString();
    }

    /**
     * Generic tab switching handler
     * Updates button active states and shows/hides tab content.
     *
     * @param {HTMLElement} btn - The clicked tab button
     * @param {string} tabName - The tab name from data-tab attribute
     * @param {object} options - Optional configuration
     * @param {string} options.tabBtnSelector - Selector for tab buttons (default: '.tab-toggle-btn')
     * @param {string} options.tabContentSelector - Selector for tab content containers (default: '.tab-content')
     * @param {function} options.onTabChange - Callback after tab changes, receives (tabName)
     */
    function handleTabSwitch(btn, tabName, options) {
        options = options || {};
        var tabBtnSelector = options.tabBtnSelector || '.tab-toggle-btn';
        var tabContentSelector = options.tabContentSelector || '.tab-content';

        // Update button states
        var allBtns = document.querySelectorAll(tabBtnSelector);
        for (var i = 0; i < allBtns.length; i++) {
            allBtns[i].classList.remove('active');
        }
        btn.classList.add('active');

        // Update tab content visibility
        var allTabs = document.querySelectorAll(tabContentSelector);
        for (var j = 0; j < allTabs.length; j++) {
            allTabs[j].classList.add('hidden');
        }

        var targetTab = document.getElementById('tab-' + tabName);
        if (targetTab) {
            targetTab.classList.remove('hidden');
        }

        // Call optional callback
        if (options.onTabChange) {
            options.onTabChange(tabName);
        }
    }

    /**
     * Setup delegated event listener on a container
     * Listens for events on a container and delegates to handlers based on data-action attribute.
     *
     * @param {HTMLElement} container - The container element to listen on
     * @param {string} eventType - The event type (e.g., 'click')
     * @param {object} handlers - Map of action names to handler functions
     * @param {string} actionAttr - The data attribute name (default: 'data-action')
     *
     * @example
     * Cookie.utils.delegate(container, 'click', {
     *   'toggle-source': handleToggleSource,
     *   'test-source': handleTestSource
     * });
     */
    function delegate(container, eventType, handlers, actionAttr) {
        if (!container) return;
        actionAttr = actionAttr || 'data-action';

        container.addEventListener(eventType, function(e) {
            var target = e.target;
            // Walk up the DOM tree to find element with action attribute
            while (target && target !== container) {
                var action = target.getAttribute(actionAttr);
                if (action && handlers[action]) {
                    // Set currentTarget-like behavior for the handler
                    e.delegateTarget = target;
                    handlers[action].call(target, e);
                    return;
                }
                target = target.parentElement;
            }
        });
    }

    /**
     * Parse a date string in iOS 9 Safari compatible way
     * Converts ISO strings to Safari-parseable format
     *
     * @param {string} dateStr - ISO date string (e.g., "2026-01-09T09:18:29.135626+00:00")
     * @returns {Date} Parsed Date object
     */
    function parseDate(dateStr) {
        if (!dateStr) return new Date(NaN);
        // Convert to Safari-parseable format:
        // - Replace T with space
        // - Remove microseconds (.135626)
        // - Remove timezone offset (+00:00 or -05:00)
        // - Remove Z suffix
        // - Convert dashes to slashes for Safari
        var normalized = dateStr
            .replace('T', ' ')
            .replace(/\.\d+/, '')
            .replace(/[+-]\d{2}:\d{2}$/, '')
            .replace('Z', '')
            .replace(/-/g, '/');
        return new Date(normalized);
    }

    // Public API
    return {
        escapeHtml: escapeHtml,
        formatTime: formatTime,
        showElement: showElement,
        hideElement: hideElement,
        truncate: truncate,
        formatNumber: formatNumber,
        escapeSelector: escapeSelector,
        formatRelativeTime: formatRelativeTime,
        formatDate: formatDate,
        handleTabSwitch: handleTabSwitch,
        delegate: delegate,
        parseDate: parseDate
    };
})();
