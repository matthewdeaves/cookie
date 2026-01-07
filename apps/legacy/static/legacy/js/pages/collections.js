/**
 * Collections page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.collections = (function() {
    'use strict';

    var modal = null;
    var form = null;

    /**
     * Initialize the page
     */
    function init() {
        modal = document.getElementById('create-modal');
        form = document.getElementById('create-form');
        setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Create collection button (header)
        var createBtn = document.getElementById('create-collection-btn');
        if (createBtn) {
            createBtn.addEventListener('click', openModal);
        }

        // Create first button (empty state)
        var createFirstBtn = document.getElementById('create-first-btn');
        if (createFirstBtn) {
            createFirstBtn.addEventListener('click', openModal);
        }

        // Modal close button
        if (modal) {
            var closeBtn = modal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', closeModal);
            }

            // Cancel button
            var cancelBtn = modal.querySelector('.modal-cancel');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', closeModal);
            }

            // Click outside modal to close
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }

        // Form submission
        if (form) {
            form.addEventListener('submit', handleSubmit);
        }
    }

    /**
     * Open the create modal
     */
    function openModal() {
        if (modal) {
            modal.classList.remove('hidden');
            // Focus the name input
            var nameInput = document.getElementById('collection-name');
            if (nameInput) {
                nameInput.focus();
            }
        }
    }

    /**
     * Close the create modal
     */
    function closeModal() {
        if (modal) {
            modal.classList.add('hidden');
            // Reset form
            if (form) {
                form.reset();
            }
        }
    }

    /**
     * Handle form submission
     */
    function handleSubmit(e) {
        e.preventDefault();

        var nameInput = document.getElementById('collection-name');
        var descInput = document.getElementById('collection-desc');
        var submitBtn = document.getElementById('create-submit');

        if (!nameInput || !nameInput.value.trim()) {
            Cookie.toast.error('Please enter a name');
            return;
        }

        // Disable button while submitting
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
        }

        var data = {
            name: nameInput.value.trim(),
            description: descInput ? descInput.value.trim() : ''
        };

        Cookie.ajax.post('/api/collections/', data, function(err, response) {
            // Re-enable button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create';
            }

            if (err) {
                Cookie.toast.error(err.message || 'Failed to create collection');
                return;
            }

            Cookie.toast.success('Collection created');

            // Navigate to the new collection
            if (response && response.id) {
                window.location.href = '/legacy/collections/' + response.id + '/';
            } else {
                // Reload page to show new collection
                window.location.reload();
            }
        });
    }

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.collections.init);
    } else {
        Cookie.pages.collections.init();
    }
})();
