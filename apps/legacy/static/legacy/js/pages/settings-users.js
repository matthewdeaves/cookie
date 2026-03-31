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

        // Event delegation for dynamically rendered profile actions
        if (profilesList) {
            Cookie.utils.delegate(profilesList, 'click', {
                'delete-profile': handleDeleteProfileClick,
                'toggle-unlimited': handleToggleUnlimited,
                'rename-profile': handleRenameClick
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

            // Unlimited toggle
            var unlimitedToggle = clone.querySelector('[data-action="toggle-unlimited"]');
            if (unlimitedToggle) {
                unlimitedToggle.setAttribute('data-profile-id', profile.id);
                if (profile.unlimited_ai) {
                    unlimitedToggle.classList.add('active');
                    unlimitedToggle.textContent = 'Unlimited';
                } else {
                    unlimitedToggle.textContent = 'Limited';
                }
            }

            // Usage summary
            var usageSummary = clone.querySelector('[data-field="usage-summary"]');
            if (usageSummary) {
                usageSummary.textContent = profile.unlimited_ai ? 'Unlimited AI access' : 'Standard quota';
            }

            // Rename button
            var renameBtn = clone.querySelector('[data-action="rename-profile"]');
            if (renameBtn) {
                renameBtn.setAttribute('data-profile-id', profile.id);
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

    /**
     * Toggle unlimited AI access for a profile
     */
    function handleToggleUnlimited(e) {
        var btn = e.delegateTarget || e.currentTarget;
        var profileId = parseInt(btn.getAttribute('data-profile-id'), 10);
        var isCurrentlyUnlimited = btn.classList.contains('active');
        var newValue = !isCurrentlyUnlimited;

        btn.disabled = true;

        Cookie.ajax.post('/api/profiles/' + profileId + '/set-unlimited/', { unlimited: newValue }, function(err, result) {
            btn.disabled = false;

            if (err) {
                Cookie.toast.error('Failed to update unlimited status');
                return;
            }

            // Update local state
            var state = Cookie.pages.settings.getState();
            for (var i = 0; i < state.profiles.length; i++) {
                if (state.profiles[i].id === profileId) {
                    state.profiles[i].unlimited_ai = result.unlimited_ai;
                    break;
                }
            }

            if (result.unlimited_ai) {
                btn.classList.add('active');
                btn.textContent = 'Unlimited';
            } else {
                btn.classList.remove('active');
                btn.textContent = 'Limited';
            }

            // Update usage summary in the same card
            var card = btn.closest('.profile-card');
            if (card) {
                var summary = card.querySelector('[data-field="usage-summary"]');
                if (summary) {
                    summary.textContent = result.unlimited_ai ? 'Unlimited AI access' : 'Standard quota';
                }
            }

            Cookie.toast.success(result.unlimited_ai ? 'Unlimited access granted' : 'Unlimited access revoked');
        });
    }

    /**
     * Handle rename button click — show inline input
     */
    function handleRenameClick(e) {
        var btn = e.delegateTarget || e.currentTarget;
        var profileId = parseInt(btn.getAttribute('data-profile-id'), 10);
        var card = btn.closest('.profile-card');
        if (!card) return;

        var nameEl = card.querySelector('[data-field="name"]');
        var renameInput = card.querySelector('[data-field="rename-input"]');
        if (!nameEl || !renameInput) return;

        // Show input, hide name
        renameInput.value = nameEl.textContent;
        nameEl.classList.add('hidden');
        renameInput.classList.remove('hidden');
        btn.classList.add('hidden');
        renameInput.focus();
        renameInput.select();

        // Save on Enter or blur
        function saveRename() {
            var newName = renameInput.value.trim();
            if (!newName || newName === nameEl.textContent) {
                // Cancel — restore display
                renameInput.classList.add('hidden');
                nameEl.classList.remove('hidden');
                btn.classList.remove('hidden');
                return;
            }

            Cookie.ajax.patch('/api/profiles/' + profileId + '/rename/', { name: newName }, function(err, result) {
                renameInput.classList.add('hidden');
                nameEl.classList.remove('hidden');
                btn.classList.remove('hidden');

                if (err) {
                    Cookie.toast.error('Failed to rename profile');
                    return;
                }

                nameEl.textContent = result.name;

                // Update local state
                var state = Cookie.pages.settings.getState();
                for (var i = 0; i < state.profiles.length; i++) {
                    if (state.profiles[i].id === profileId) {
                        state.profiles[i].name = result.name;
                        break;
                    }
                }

                Cookie.toast.success('Profile renamed');
            });
        }

        // Remove previous listeners by replacing the element
        var newInput = renameInput.cloneNode(true);
        renameInput.parentNode.replaceChild(newInput, renameInput);
        newInput.classList.remove('hidden');
        newInput.focus();
        newInput.select();

        newInput.addEventListener('keydown', function(ev) {
            if (ev.keyCode === 13) { // Enter
                ev.preventDefault();
                renameInput = newInput;
                saveRename();
            } else if (ev.keyCode === 27) { // Escape
                renameInput = newInput;
                renameInput.classList.add('hidden');
                nameEl.classList.remove('hidden');
                btn.classList.remove('hidden');
            }
        });
        newInput.addEventListener('blur', function() {
            renameInput = newInput;
            saveRename();
        });
    }

    // Register with core module
    Cookie.pages.settings.registerTab('users', {
        init: init,
        loadProfiles: loadProfiles
    });
})();
