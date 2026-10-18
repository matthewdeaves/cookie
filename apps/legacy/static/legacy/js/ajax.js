/**
 * AJAX wrapper using XMLHttpRequest (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};

Cookie.ajax = (function() {
    'use strict';

    var API_BASE = '/api';

    /**
     * Read CSRF token from cookie
     * @returns {string} CSRF token value or empty string
     */
    function getCsrfToken() {
        var value = '; ' + document.cookie;
        var parts = value.split('; csrftoken=');
        if (parts.length === 2) {
            return parts.pop().split(';').shift() || '';
        }
        return '';
    }

    var PROFILE_STORAGE_KEY = 'cookie_selected_profile_id';
    var restoring = null;  // callbacks waiting on an in-flight session restore

    function isUnsafe(method) {
        var m = method.toUpperCase();
        return m === 'POST' || m === 'PUT' || m === 'DELETE' || m === 'PATCH';
    }

    function readStoredProfileId() {
        try {
            var stored = localStorage.getItem(PROFILE_STORAGE_KEY);
            return stored && /^[0-9]+$/.test(stored) ? stored : null;
        } catch (e) {
            return null;
        }
    }

    /**
     * Home mode keeps the chosen profile in the server session, which can expire.
     * The profile id is remembered in localStorage, so re-select it quietly
     * instead of failing the request. Concurrent 401s share one attempt.
     * @param {Function} done - done(restored: boolean)
     */
    function restoreSession(done) {
        var profileId = readStoredProfileId();
        if (!profileId) {
            done(false);
            return;
        }
        if (restoring) {
            restoring.push(done);
            return;
        }
        restoring = [done];
        send('POST', '/api/profiles/' + profileId + '/select/', null, function(error) {
            var waiting = restoring;
            restoring = null;
            for (var i = 0; i < waiting.length; i++) {
                waiting[i](!error);
            }
        }, { noRestore: true });
    }

    /**
     * Session is gone and could not be restored: go back to the profile picker.
     */
    function sessionLost() {
        if (window.location.pathname === '/legacy/' || window.location.pathname === '/legacy') {
            return;
        }
        if (Cookie.toast && Cookie.toast.error) {
            Cookie.toast.error('Your session ended. Please choose your profile again.');
        }
        setTimeout(function() {
            window.location.href = '/legacy/';
        }, 1500);
    }

    function buildError(xhr) {
        var errorData = null;
        var errorMsg = 'Request failed';
        try {
            errorData = JSON.parse(xhr.responseText);
            errorMsg = errorData.detail || errorData.message || errorMsg;
        } catch (e) {
            errorMsg = xhr.statusText || errorMsg;
        }
        var err = new Error(errorMsg);
        err.status = xhr.status;
        err.data = errorData;  // Include full error data for action field etc.
        return err;
    }

    function succeed(xhr, callback) {
        var response = null;
        if (xhr.responseText && xhr.status !== 204) {
            try {
                response = JSON.parse(xhr.responseText);
            } catch (e) {
                response = xhr.responseText;
            }
        }
        callback(null, response);
    }

    /**
     * Make an XHR request
     * @param {string} method - HTTP method
     * @param {string} url - Request URL
     * @param {Object|null} data - Request data (for POST/PUT)
     * @param {Function} callback - Callback function(error, response)
     * @param {Object} [options] - {timeout: ms, noRestore: bool}
     */
    function send(method, url, data, callback, options) {
        options = options || {};
        var xhr = new XMLHttpRequest();
        var fullUrl = url.indexOf('/api') === 0 ? url : API_BASE + url;

        xhr.open(method, fullUrl, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        if (options.timeout) {
            xhr.timeout = options.timeout;
        }

        // Add CSRF token for state-changing requests
        if (isUnsafe(method)) {
            var csrfToken = getCsrfToken();
            if (csrfToken) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
            }
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState !== 4 || xhr.status === 0) {
                return;  // status 0 is reported through onerror / ontimeout
            }
            if (xhr.status >= 200 && xhr.status < 300) {
                succeed(xhr, callback);
                return;
            }
            var err = buildError(xhr);
            // Plain "Unauthorized" = no valid session (an AI key problem has its own body)
            if (xhr.status === 401 && !options.noRestore && err.message === 'Unauthorized') {
                restoreSession(function(restored) {
                    if (restored) {
                        var retryOptions = { timeout: options.timeout, noRestore: true };
                        send(method, url, data, callback, retryOptions);
                    } else {
                        sessionLost();
                        callback(err, null);
                    }
                });
                return;
            }
            callback(err, null);
        };

        xhr.onerror = function() {
            var err = new Error("Can't reach the server. Check your connection and try again.");
            err.status = 0;
            callback(err, null);
        };

        xhr.ontimeout = function() {
            var err = new Error('The request took too long. Please try again.');
            err.status = 0;
            err.timedOut = true;
            callback(err, null);
        };

        if (data) {
            xhr.send(JSON.stringify(data));
        } else {
            xhr.send();
        }
    }

    function request(method, url, data, callback, options) {
        send(method, url, data, callback, options);
    }

    return {
        /**
         * GET request
         * @param {string} url - Request URL
         * @param {Function} callback - Callback function(error, response)
         * @param {Object} [options] - {timeout: ms}
         */
        get: function(url, callback, options) {
            request('GET', url, null, callback, options);
        },

        /**
         * POST request
         * @param {string} url - Request URL
         * @param {Object} data - Request data
         * @param {Function} callback - Callback function(error, response)
         */
        post: function(url, data, callback) {
            request('POST', url, data, callback);
        },

        /**
         * PUT request
         * @param {string} url - Request URL
         * @param {Object} data - Request data
         * @param {Function} callback - Callback function(error, response)
         */
        put: function(url, data, callback) {
            request('PUT', url, data, callback);
        },

        /**
         * PATCH request
         * @param {string} url - Request URL
         * @param {Object} data - Request data
         * @param {Function} callback - Callback function(error, response)
         */
        patch: function(url, data, callback) {
            request('PATCH', url, data, callback);
        },

        /**
         * DELETE request
         * @param {string} url - Request URL
         * @param {Function} callback - Callback function(error, response)
         */
        delete: function(url, callback) {
            request('DELETE', url, null, callback);
        }
    };
})();
