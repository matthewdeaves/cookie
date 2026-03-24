/**
 * Recipe Detail page - Collections module (ES5, iOS 9 compatible)
 * Handles collection modal and add/create operations.
 */
(function() {
    'use strict';

    function init() {
        setupCollectionButton();
        setupCollectionModal();
        setupCreateCollectionModal();
        setupCollectionOptions();
    }

    function setupCollectionButton() {
        var collectionBtn = document.getElementById('collection-btn');
        if (collectionBtn) {
            collectionBtn.addEventListener('click', handleCollectionClick);
        }
    }

    function handleCollectionClick() {
        var modal = document.getElementById('collection-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    function setupCollectionModal() {
        var modalClose = document.getElementById('modal-close');
        if (modalClose) {
            modalClose.addEventListener('click', closeCollectionModal);
        }

        var collectionModal = document.getElementById('collection-modal');
        if (collectionModal) {
            collectionModal.addEventListener('click', function(e) {
                if (e.target === collectionModal) {
                    closeCollectionModal();
                }
            });
        }
    }

    function closeCollectionModal() {
        var modal = document.getElementById('collection-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function setupCreateCollectionModal() {
        var createCollectionBtn = document.getElementById('create-collection-btn');
        if (createCollectionBtn) {
            createCollectionBtn.addEventListener('click', openCreateCollectionModal);
        }

        var createModalClose = document.getElementById('create-modal-close');
        if (createModalClose) {
            createModalClose.addEventListener('click', closeCreateCollectionModal);
        }

        var createCollectionModal = document.getElementById('create-collection-modal');
        if (createCollectionModal) {
            createCollectionModal.addEventListener('click', function(e) {
                if (e.target === createCollectionModal) {
                    closeCreateCollectionModal();
                }
            });
        }

        var createForm = document.getElementById('create-collection-form');
        if (createForm) {
            createForm.addEventListener('submit', handleCreateCollection);
        }
    }

    function openCreateCollectionModal() {
        closeCollectionModal();
        var modal = document.getElementById('create-collection-modal');
        if (modal) {
            modal.classList.remove('hidden');
            var nameInput = document.getElementById('collection-name');
            if (nameInput) {
                nameInput.value = '';
                nameInput.focus();
            }
        }
    }

    function closeCreateCollectionModal() {
        var modal = document.getElementById('create-collection-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function setupCollectionOptions() {
        var collectionOptions = document.querySelectorAll('.collection-option');
        for (var j = 0; j < collectionOptions.length; j++) {
            collectionOptions[j].addEventListener('click', handleCollectionOptionClick);
        }
    }

    function handleCollectionOptionClick(e) {
        var btn = e.currentTarget;
        var collectionId = parseInt(btn.getAttribute('data-collection-id'), 10);
        addToCollection(collectionId);
    }

    function addToCollection(collectionId) {
        var state = Cookie.pages.detail.getState();

        Cookie.ajax.post('/api/collections/' + collectionId + '/recipes/', { recipe_id: state.recipeId }, function(err) {
            if (err) {
                if (err.message && err.message.indexOf('already') !== -1) {
                    Cookie.toast.error('Recipe already in collection');
                } else {
                    Cookie.toast.error('Failed to add to collection');
                }
                return;
            }
            closeCollectionModal();
            Cookie.toast.success('Added to collection');
        });
    }

    function handleCreateCollection(e) {
        e.preventDefault();
        var state = Cookie.pages.detail.getState();

        var nameInput = document.getElementById('collection-name');
        var name = nameInput ? nameInput.value.trim() : '';

        if (!name) {
            Cookie.toast.error('Please enter a collection name');
            return;
        }

        Cookie.ajax.post('/api/collections/', { name: name }, function(err, collection) {
            if (err) {
                Cookie.toast.error('Failed to create collection');
                return;
            }

            Cookie.ajax.post('/api/collections/' + collection.id + '/recipes/', { recipe_id: state.recipeId }, function(err2) {
                if (err2) {
                    Cookie.toast.error('Collection created but failed to add recipe');
                    closeCreateCollectionModal();
                    return;
                }

                closeCreateCollectionModal();
                Cookie.toast.success('Created collection and added recipe');

                // Add new collection to the list in the modal
                var collectionList = document.querySelector('.collection-list');
                if (collectionList) {
                    var newBtn = document.createElement('button');
                    newBtn.type = 'button';
                    newBtn.className = 'collection-option';
                    newBtn.setAttribute('data-collection-id', collection.id);
                    newBtn.textContent = collection.name;
                    newBtn.addEventListener('click', handleCollectionOptionClick);
                    collectionList.appendChild(newBtn);
                }
            });
        });
    }

    // Register with core module
    Cookie.pages.detail.registerFeature('collections', {
        init: init
    });
})();
