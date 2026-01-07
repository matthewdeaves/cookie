/**
 * Simple state management for Legacy frontend (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};

Cookie.state = (function() {
    'use strict';

    // Application state
    var state = {
        profile: null,
        loading: false
    };

    // Subscribers for state changes
    var subscribers = [];

    /**
     * Get current state
     * @returns {Object} Current state
     */
    function getState() {
        return Object.assign({}, state);
    }

    /**
     * Update state and notify subscribers
     * @param {Object} updates - State updates
     */
    function setState(updates) {
        var prevState = Object.assign({}, state);
        state = Object.assign({}, state, updates);

        // Notify all subscribers
        for (var i = 0; i < subscribers.length; i++) {
            subscribers[i](state, prevState);
        }
    }

    /**
     * Subscribe to state changes
     * @param {Function} callback - Called when state changes
     * @returns {Function} Unsubscribe function
     */
    function subscribe(callback) {
        subscribers.push(callback);

        // Return unsubscribe function
        return function() {
            var index = subscribers.indexOf(callback);
            if (index > -1) {
                subscribers.splice(index, 1);
            }
        };
    }

    /**
     * Set current profile
     * @param {Object|null} profile - Profile object or null
     */
    function setProfile(profile) {
        setState({ profile: profile });
    }

    /**
     * Get current profile
     * @returns {Object|null} Current profile
     */
    function getProfile() {
        return state.profile;
    }

    /**
     * Set loading state
     * @param {boolean} loading - Loading state
     */
    function setLoading(loading) {
        setState({ loading: loading });
    }

    /**
     * Check if loading
     * @returns {boolean} Loading state
     */
    function isLoading() {
        return state.loading;
    }

    return {
        getState: getState,
        setState: setState,
        subscribe: subscribe,
        setProfile: setProfile,
        getProfile: getProfile,
        setLoading: setLoading,
        isLoading: isLoading
    };
})();
