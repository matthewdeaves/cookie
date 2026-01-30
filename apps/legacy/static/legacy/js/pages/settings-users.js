/**
 * Settings page - Users tab (ES5, iOS 9 compatible)
 * Handles user profile management and deletion.
 */
(function() {
    'use strict';

    var profilesList;
    var profileCount;
    var deleteModal;
    var deleteProfileInfo;
    var deleteDataSummary;
    var confirmDeleteBtn;
    var deleteBtnText;

    function init() {
        profilesList = document.getElementById('profiles-list');
        profileCount = document.getElementById('profile-count');
        deleteModal = document.getElementById('delete-profile-modal');
        deleteProfileInfo = document.getElementById('delete-profile-info');
        deleteDataSummary = document.getElementById('delete-data-summary');
        confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        deleteBtnText = document.getElementById('delete-btn-text');

        // Event delegation for dynamically rendered profile delete buttons
        if (profilesList) {
            Cookie.utils.delegate(profilesList, 'click', {
                'delete-profile': handleDeleteProfileClick
            });
        }

        // Expose modal functions globally for onclick handlers
        window.closeDeleteModal = closeDeleteModal;
        window.executeDeleteProfile = executeDeleteProfile;
    }

    function loadProfiles() {
        var state = Cookie.pages.settings.getState();

        Cookie.ajax.get('/api/profiles/', function(err, result) {
            if (err) {
                profilesList.innerHTML = '<div class="error-placeholder">Failed to load profiles</div>';
                return;
            }

            state.profiles = result;
            renderProfiles();
            updateProfileCount();
        });
    }

    function updateProfileCount() {
        var profiles = Cookie.pages.settings.getState().profiles;
        profileCount.textContent = profiles.length + ' profile' + (profiles.length !== 1 ? 's' : '');
    }

    function renderProfiles() {
        var state = Cookie.pages.settings.getState();
        var profiles = state.profiles;
        var currentProfileId = state.currentProfileId;
        var template = document.getElementById('template-profile-card');
        var fragment = document.createDocumentFragment();

        for (var i = 0; i < profiles.length; i++) {
            var profile = profiles[i];
            var isCurrent = profile.id === currentProfileId;
            var clone = template.content.cloneNode(true);
            var card = clone.querySelector('.profile-card');

            card.setAttribute('data-profile-id', profile.id);

            clone.querySelector('[data-field="avatar"]').style.backgroundColor = profile.avatar_color;
            clone.querySelector('[data-field="name"]').textContent = profile.name;
            clone.querySelector('[data-field="created"]').textContent = 'Created ' + Cookie.utils.formatDate(profile.created_at);
            clone.querySelector('[data-field="stats"]').textContent =
                profile.stats.favorites + ' favorites · ' +
                profile.stats.collections + ' collections · ' +
                profile.stats.remixes + ' remixes';

            var badge = clone.querySelector('[data-field="badge"]');
            if (isCurrent) {
                badge.classList.remove('hidden');
            }

            var deleteBtn = clone.querySelector('[data-action="delete-profile"]');
            deleteBtn.setAttribute('data-profile-id', profile.id);
            if (isCurrent) {
                deleteBtn.disabled = true;
                deleteBtn.classList.add('btn-delete-disabled');
                deleteBtn.title = 'Cannot delete current profile';
            }

            fragment.appendChild(clone);
        }

        profilesList.innerHTML = '';
        profilesList.appendChild(fragment);
    }

    function handleDeleteProfileClick(e) {
        var btn = e.delegateTarget || e.currentTarget;
        if (btn.disabled) return;

        var profileId = parseInt(btn.getAttribute('data-profile-id'), 10);
        var state = Cookie.pages.settings.getState();
        state.pendingDeleteId = profileId;

        Cookie.ajax.get('/api/profiles/' + profileId + '/deletion-preview/', function(err, preview) {
            if (err) {
                Cookie.toast.error('Failed to load profile info');
                state.pendingDeleteId = null;
                return;
            }

            renderDeleteModal(preview);
            deleteModal.classList.remove('hidden');
        });
    }

    function renderDeleteModal(preview) {
        var profile = preview.profile;
        var data = preview.data_to_delete;

        deleteProfileInfo.innerHTML = [
            '<div class="profile-avatar" style="background-color: ' + Cookie.utils.escapeHtml(profile.avatar_color) + '"></div>',
            '<div>',
            '  <div class="profile-name">' + Cookie.utils.escapeHtml(profile.name) + '</div>',
            '  <div class="profile-meta">Created ' + Cookie.utils.formatDate(profile.created_at) + '</div>',
            '</div>'
        ].join('');

        var summaryItems = [];
        if (data.remixes > 0) {
            summaryItems.push(data.remixes + ' remixed recipe' + (data.remixes !== 1 ? 's' : '') +
                ' (' + data.remix_images + ' images)');
        }
        if (data.favorites > 0) {
            summaryItems.push(data.favorites + ' favorite' + (data.favorites !== 1 ? 's' : ''));
        }
        if (data.collections > 0) {
            summaryItems.push(data.collections + ' collection' + (data.collections !== 1 ? 's' : '') +
                ' (' + data.collection_items + ' items)');
        }
        if (data.view_history > 0) {
            summaryItems.push(data.view_history + ' view history entries');
        }
        if (data.scaling_cache > 0 || data.discover_cache > 0) {
            summaryItems.push('Cached AI data');
        }
        if (summaryItems.length === 0) {
            summaryItems.push('No associated data');
        }

        deleteDataSummary.innerHTML =
            '<div class="summary-title">Data to be deleted:</div>' +
            '<ul class="summary-list">' + summaryItems.map(function(item) {
                return '<li>' + item + '</li>';
            }).join('') + '</ul>';
    }

    function closeDeleteModal() {
        var state = Cookie.pages.settings.getState();
        deleteModal.classList.add('hidden');
        state.pendingDeleteId = null;
    }

    function executeDeleteProfile() {
        var state = Cookie.pages.settings.getState();
        if (!state.pendingDeleteId) return;

        confirmDeleteBtn.disabled = true;
        deleteBtnText.textContent = 'Deleting...';

        Cookie.ajax.delete('/api/profiles/' + state.pendingDeleteId + '/', function(err, result) {
            confirmDeleteBtn.disabled = false;
            deleteBtnText.textContent = 'Delete Profile';

            if (err) {
                Cookie.toast.error('Failed to delete profile');
                return;
            }

            Cookie.toast.success('Profile deleted successfully');

            var deletedId = state.pendingDeleteId;
            closeDeleteModal();

            state.profiles = state.profiles.filter(function(p) {
                return p.id !== deletedId;
            });
            renderProfiles();
            updateProfileCount();
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('users', {
        init: init,
        loadProfiles: loadProfiles
    });
})();
