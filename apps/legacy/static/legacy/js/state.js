/**
 * Simple state management for Legacy frontend (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};

Cookie.state = (function() {
    'use strict';

    var PROFILE_STORAGE_KEY = 'cookie_selected_profile_id';

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
        if (profile && profile.id) {
            try {
                localStorage.setItem(PROFILE_STORAGE_KEY, String(profile.id));
            } catch (e) { /* localStorage unavailable */ }
            document.cookie = 'selected_profile_id=' + profile.id + ';path=/;SameSite=Lax';
        }
    }

    /**
     * Clear persisted profile (logout/switch)
     */
    function clearProfile() {
        setState({ profile: null });
        try {
            localStorage.removeItem(PROFILE_STORAGE_KEY);
        } catch (e) { /* localStorage unavailable */ }
        document.cookie = 'selected_profile_id=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }

    /**
     * Get persisted profile ID from localStorage
     * @returns {number|null} Profile ID or null
     */
    function getPersistedProfileId() {
        try {
            var stored = localStorage.getItem(PROFILE_STORAGE_KEY);
            if (!stored) return null;
            var id = parseInt(stored, 10);
            return isNaN(id) ? null : id;
        } catch (e) {
            return null;
        }
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
        clearProfile: clearProfile,
        getPersistedProfileId: getPersistedProfileId,
        getProfile: getProfile,
        setLoading: setLoading,
        isLoading: isLoading
    };
})();
