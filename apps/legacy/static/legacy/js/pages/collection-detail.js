/**
 * Collection detail page (ES5, iOS 9 compatible)
 */
var Cookie = Cookie || {};
Cookie.pages = Cookie.pages || {};

Cookie.pages.collectionDetail = (function() {
    'use strict';

    var collectionId = null;
    var deleteModal = null;

    /**
     * Initialize the page
     */
    function init() {
        // Get collection ID from data attribute
        var screen = document.querySelector('[data-page="collection-detail"]');
        if (screen) {
            collectionId = screen.getAttribute('data-collection-id');
        }

        deleteModal = document.getElementById('delete-modal');
        setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Delete collection button
        var deleteBtn = document.getElementById('delete-collection-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', openDeleteModal);
        }

        // Delete modal close/cancel
        if (deleteModal) {
            var closeBtn = deleteModal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', closeDeleteModal);
            }

            var cancelBtn = deleteModal.querySelector('.modal-cancel');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', closeDeleteModal);
            }

            // Click outside to close
            deleteModal.addEventListener('click', function(e) {
                if (e.target === deleteModal) {
                    closeDeleteModal();
                }
            });

            // Confirm delete
            var confirmBtn = document.getElementById('confirm-delete');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', deleteCollection);
            }
        }

        // Remove recipe buttons
        var removeBtns = document.querySelectorAll('.remove-recipe-btn');
        for (var i = 0; i < removeBtns.length; i++) {
            removeBtns[i].addEventListener('click', handleRemoveRecipe);
        }
    }

    /**
     * Open delete confirmation modal
     */
    function openDeleteModal() {
        if (deleteModal) {
            deleteModal.classList.remove('hidden');
        }
    }

    /**
     * Close delete confirmation modal
     */
    function closeDeleteModal() {
        if (deleteModal) {
            deleteModal.classList.add('hidden');
        }
    }

    /**
     * Delete the collection
     */
    function deleteCollection() {
        if (!collectionId) return;

        var confirmBtn = document.getElementById('confirm-delete');
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Deleting...';
        }

        Cookie.ajax.delete('/api/collections/' + collectionId + '/', function(err) {
            if (err) {
                if (confirmBtn) {
                    confirmBtn.disabled = false;
                    confirmBtn.textContent = 'Delete';
                }
                Cookie.toast.error('Failed to delete collection');
                return;
            }

            Cookie.toast.success('Collection deleted');
            // Navigate back to collections list
            window.location.href = '/legacy/collections/';
        });
    }

    /**
     * Handle remove recipe button click
     */
    function handleRemoveRecipe(e) {
        e.preventDefault();
        e.stopPropagation();

        var btn = e.currentTarget;
        var recipeId = btn.getAttribute('data-recipe-id');

        if (!collectionId || !recipeId) return;

        // Disable button while removing
        btn.disabled = true;

        Cookie.ajax.delete('/api/collections/' + collectionId + '/recipes/' + recipeId + '/', function(err) {
            if (err) {
                btn.disabled = false;
                Cookie.toast.error('Failed to remove recipe');
                return;
            }

            // Animate and remove the card wrapper
            var wrapper = btn.closest('.recipe-card-wrapper');
            if (wrapper) {
                wrapper.style.opacity = '0';
                wrapper.style.transform = 'scale(0.9)';
                wrapper.style.transition = 'opacity 0.2s, transform 0.2s';
                setTimeout(function() {
                    wrapper.remove();
                    updateCount();
                    checkEmpty();
                }, 200);
            }

            Cookie.toast.success('Recipe removed');
        });
    }

    /**
     * Update the count display
     */
    function updateCount() {
        var wrappers = document.querySelectorAll('.recipe-card-wrapper');
        var countEl = document.querySelector('.text-muted');
        if (countEl) {
            var count = wrappers.length;
            countEl.textContent = count + ' recipe' + (count !== 1 ? 's' : '');
        }
    }

    /**
     * Check if page should show empty state
     */
    function checkEmpty() {
        var wrappers = document.querySelectorAll('.recipe-card-wrapper');
        if (wrappers.length === 0) {
            window.location.reload();
        }
    }

    return {
        init: init
    };
})();

// Auto-init on page load
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', Cookie.pages.collectionDetail.init);
    } else {
        Cookie.pages.collectionDetail.init();
    }
})();
