/**
 * AJAX wrapper using XMLHttpRequest (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};

Cookie.ajax = (function() {
    'use strict';

    var API_BASE = '/api';

    /**
     * Make an XHR request
     * @param {string} method - HTTP method
     * @param {string} url - Request URL
     * @param {Object|null} data - Request data (for POST/PUT)
     * @param {Function} callback - Callback function(error, response)
     */
    function request(method, url, data, callback) {
        var xhr = new XMLHttpRequest();
        var fullUrl = url.indexOf('/api') === 0 ? url : API_BASE + url;

        xhr.open(method, fullUrl, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status >= 200 && xhr.status < 300) {
                    var response = null;
                    if (xhr.responseText && xhr.status !== 204) {
                        try {
                            response = JSON.parse(xhr.responseText);
                        } catch (e) {
                            response = xhr.responseText;
                        }
                    }
                    callback(null, response);
                } else {
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
                    callback(err, null);
                }
            }
        };

        xhr.onerror = function() {
            callback(new Error('Network error'), null);
        };

        if (data) {
            xhr.send(JSON.stringify(data));
        } else {
            xhr.send();
        }
    }

    return {
        /**
         * GET request
         * @param {string} url - Request URL
         * @param {Function} callback - Callback function(error, response)
         */
        get: function(url, callback) {
            request('GET', url, null, callback);
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
         * DELETE request
         * @param {string} url - Request URL
         * @param {Function} callback - Callback function(error, response)
         */
        delete: function(url, callback) {
            request('DELETE', url, null, callback);
        }
    };
})();
