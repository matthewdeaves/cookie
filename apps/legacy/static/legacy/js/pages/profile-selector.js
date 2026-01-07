/**
 * Profile Selector page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.profileSelector = (function() {
    'use strict';

    // Profile colors (same as React)
    var PROFILE_COLORS = [
        '#d97850',
        '#8fae6f',
        '#c9956b',
        '#6b9dad',
        '#d16b6b',
        '#9d80b8',
        '#e6a05f',
        '#6bb8a5',
        '#c77a9e',
        '#7d9e6f'
    ];

    var selectedColor = PROFILE_COLORS[0];
    var profileGrid = null;
    var createForm = null;
    var nameInput = null;
    var createBtn = null;

    /**
     * Initialize the page
     */
    function init() {
        profileGrid = document.getElementById('profile-grid');
        createForm = document.getElementById('create-form');
        nameInput = document.getElementById('profile-name');
        createBtn = document.getElementById('create-btn');

        setupColorPicker();
        setupEventListeners();
    }

    /**
     * Setup color picker
     */
    function setupColorPicker() {
        var colorPicker = document.getElementById('color-picker');

        PROFILE_COLORS.forEach(function(color, index) {
            var swatch = document.createElement('button');
            swatch.type = 'button';
            swatch.className = 'color-swatch' + (index === 0 ? ' selected' : '');
            swatch.style.backgroundColor = color;
            swatch.style.margin = '0.25rem';
            swatch.setAttribute('data-color', color);

            swatch.addEventListener('click', function() {
                // Remove selected from all
                var swatches = colorPicker.querySelectorAll('.color-swatch');
                for (var i = 0; i < swatches.length; i++) {
                    swatches[i].classList.remove('selected');
                }
                // Add selected to clicked
                swatch.classList.add('selected');
                selectedColor = color;
            });

            colorPicker.appendChild(swatch);
        });
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Profile buttons
        var profileBtns = profileGrid.querySelectorAll('.profile-btn');
        for (var i = 0; i < profileBtns.length; i++) {
            profileBtns[i].addEventListener('click', handleProfileClick);
        }

        // Add profile button
        var addBtn = document.getElementById('add-profile-btn');
        addBtn.addEventListener('click', showCreateForm);

        // Cancel button
        var cancelBtn = document.getElementById('cancel-btn');
        cancelBtn.addEventListener('click', hideCreateForm);

        // Name input
        nameInput.addEventListener('input', function() {
            createBtn.disabled = !nameInput.value.trim();
        });

        // Form submit
        var form = document.getElementById('profile-form');
        form.addEventListener('submit', handleCreateProfile);
    }

    /**
     * Handle profile click
     */
    function handleProfileClick(e) {
        var btn = e.currentTarget;
        var profileId = btn.getAttribute('data-profile-id');

        selectProfile(profileId);
    }

    /**
     * Select a profile
     */
    function selectProfile(profileId) {
        Cookie.ajax.post('/profiles/' + profileId + '/select/', null, function(err, response) {
            if (err) {
                Cookie.toast.error('Failed to select profile');
                return;
            }

            // Store profile in state
            Cookie.state.setProfile(response);

            // Navigate to home
            window.location.href = '/legacy/home/';
        });
    }

    /**
     * Show create form
     */
    function showCreateForm() {
        createForm.classList.remove('hidden');
        nameInput.value = '';
        createBtn.disabled = true;
        selectedColor = PROFILE_COLORS[0];

        // Reset color selection
        var swatches = document.querySelectorAll('.color-swatch');
        for (var i = 0; i < swatches.length; i++) {
            swatches[i].classList.remove('selected');
        }
        if (swatches[0]) {
            swatches[0].classList.add('selected');
        }

        nameInput.focus();
    }

    /**
     * Hide create form
     */
    function hideCreateForm() {
        createForm.classList.add('hidden');
        nameInput.value = '';
    }

    /**
     * Handle create profile form submit
     */
    function handleCreateProfile(e) {
        e.preventDefault();

        var name = nameInput.value.trim();
        if (!name) return;

        createBtn.disabled = true;
        createBtn.textContent = 'Creating...';

        var data = {
            name: name,
            avatar_color: selectedColor,
            theme: 'light',
            unit_preference: 'metric'
        };

        Cookie.ajax.post('/profiles/', data, function(err, profile) {
            createBtn.disabled = false;
            createBtn.textContent = 'Create';

            if (err) {
                Cookie.toast.error('Failed to create profile');
                return;
            }

            Cookie.toast.success('Welcome, ' + profile.name + '!');

            // Add new profile to grid
            addProfileToGrid(profile);

            // Hide form
            hideCreateForm();
        });
    }

    /**
     * Add a profile to the grid
     */
    function addProfileToGrid(profile) {
        var addBtn = document.getElementById('add-profile-btn').parentElement;

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'profile-btn';
        btn.setAttribute('data-profile-id', profile.id);
        btn.setAttribute('data-profile-name', profile.name);

        var avatar = document.createElement('div');
        avatar.className = 'avatar avatar-xl';
        avatar.style.backgroundColor = profile.avatar_color;
        avatar.textContent = profile.name.charAt(0).toUpperCase();

        var nameLbl = document.createElement('span');
        nameLbl.className = 'profile-btn-name';
        nameLbl.textContent = profile.name;

        btn.appendChild(avatar);
        btn.appendChild(nameLbl);

        btn.addEventListener('click', handleProfileClick);

        // Insert before add button
        profileGrid.insertBefore(btn, addBtn);
    }

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.profileSelector.init);
    } else {
        Cookie.pages.profileSelector.init();
    }
})();
