/* global gettext */

import deepmerge from "deepmerge";
import {Uploader, ValidationError, getPaperParams} from "./_uploader";
import {showError, collectError, showCollectedErrors} from "./_utils";

// PaperAdmin API
const EventEmitter = window.paperAdmin.EventEmitter;
const whenDomReady = window.paperAdmin.whenDomReady;
const Sortable = window.paperAdmin.Sortable;
const bootbox = window.paperAdmin.bootbox;
const emitters = window.paperAdmin.emitters;
const preloader = window.paperAdmin.preloader;
const formUtils = window.paperAdmin.formUtils;

// CSS
import "../css/collection_widget.scss";


/**
 * @param element
 * @param options
 * @fires collection:created
 * @fires collection:deleted
 * @fires collection:submit_item
 * @fires collection:upload_item
 * @fires collection:cancel_item
 * @fires collection:complete_item
 * @constructor
 */
function Collection(element, options) {
    /**
     * @type Object
     */
    this._opts = deepmerge({
        input: '.collection__input',
        itemContainer: '.collection__items',
        item: '.collection__item',
        createButton: '.collection__create-button',
        uploadButton: '.collection__upload-button',
        deleteButton: '.collection__delete-button',
        preloaderItem: '.collection__item--preloader',
        preloaderTemplate: '.collection__item-preloader',

        itemPreview: '.collection__item-preview',
        itemLink: '.collection__item-link',
        itemCheckbox: '.collection__item-checkbox',
        itemName: '.collection__item-name',
        changeItemButton: '.collection__item-change-button',
        cancelItemButton: '.collection__item-cancel-button',
        deleteItemButton: '.collection__item-delete-button',
        itemSelectorTemplate: '.collection__{}-item-template',

        collectionEmptyState: 'collection--empty',
        itemCheckedState: 'collection__item--checked',
        itemRemovingState: 'collection__item--removing',

        urls: {
            createCollection: '',
            deleteCollection: '',
            uploadItem: '',
            changeItem: '',
            deleteItem: '',
            sortItems: ''
        }
    }, options || {});

    this.element = element;

    this.input = this.element.querySelector(this._opts.input);
    if (!this.input) {
        throw new Error(`Not found element "${this._opts.input}"`);
    }

    this.itemContainer = this.element.querySelector(this._opts.itemContainer);
    if (!this.itemContainer) {
        throw new Error(`Not found element "${this._opts.itemContainer}"`);
    }

    this.createButton = this.element.querySelector(this._opts.createButton);
    if (!this.createButton) {
        throw new Error(`Not found element "${this._opts.createButton}"`);
    }

    this.uploadButton = this.element.querySelector(this._opts.uploadButton);
    if (!this.uploadButton) {
        throw new Error(`Not found element "${this._opts.uploadButton}"`);
    }

    this.deleteButton = this.element.querySelector(this._opts.deleteButton);
    if (!this.deleteButton) {
        throw new Error(`Not found element "${this._opts.deleteButton}"`);
    }

    this.init();
}

Collection.prototype = Object.create(EventEmitter.prototype);

Object.defineProperty(Collection.prototype, 'collectionId', {
    get: function() {
        return parseInt(this.input.value);
    },
    set: function(value) {
        const newValue = parseInt(value);
        if (isNaN(newValue)) {
            // удаление коллекции
            this.input.value = '';
            this.createButton.disabled = false;
            this.uploadButton.disabled = true;
            this.deleteButton.disabled = true;
            this.element.classList.add(this._opts.collectionEmptyState);

            const uploadInput = this.uploadButton.querySelector('input[type="file"]');
            uploadInput && (uploadInput.disabled = true);
        } else {
            // создание коллекции
            this.input.value = newValue;
            this.createButton.disabled = true;
            this.uploadButton.disabled = false;
            this.deleteButton.disabled = false;
            this.element.classList.remove(this._opts.collectionEmptyState);

            const uploadInput = this.uploadButton.querySelector('input[type="file"]');
            uploadInput && (uploadInput.disabled = false);
        }
    }
});

Object.defineProperty(Collection.prototype, 'loading', {
    get: function() {
        return Boolean(this._loading);
    },
    set: function(value) {
        const newValue = Boolean(value);
        if (newValue === Boolean(this._loading)) {
            return
        }
        if (newValue) {
            this.element.classList.add('loading');
            this.deleteButton.disabled = true;
        } else {
            this.element.classList.remove('loading');
            this.deleteButton.disabled = false;
        }
        this._loading = newValue;
    }
});

/**
 * Инициализация галереи
 */
Collection.prototype.init = function() {
    this.uploader = this.initUploader();
    this.sortable = this.initSortable();
    this.collectionId = this.input.value;
    this.loading = false;
    this.addListeners();
};

/**
 * Инициализация загрузчика картинок.
 */
Collection.prototype.initUploader = function() {
    const _this = this;
    return new Uploader(this.element, {
        url: this._opts.urls.uploadItem,
        multiple: true,
        maxConnections: 4,
        button: this.uploadButton,
        dropzones: this.element.querySelectorAll('.dropzone-overlay'),
        validation: JSON.parse(this.element.dataset.validation),
        extraData: {
            collectionId: function() {
                return _this.collectionId;
            }
        },
    }).on('submit', function() {
        if (isNaN(_this.collectionId)) {
            throw new ValidationError();
        }
    }).on('submitted', function(id) {
        const template = _this.element.querySelector(_this._opts.preloaderTemplate);
        const clone = document.importNode(template.content, true);

        const preloader = clone.querySelector(_this._opts.item);
        preloader.dataset.queueId = id;
        preloader.classList.add(`item-preloader-${id}`);

        const file = this.uploader.getFile(id);
        const fileName = preloader.querySelector(_this._opts.itemName);
        if (fileName) {
            fileName.title = file.name;
            fileName.textContent = file.name;
        }

        _this.itemContainer.append(clone);

        _this.trigger('collection:submit_item', [preloader, id]);
    }).on('upload', function(id) {
        _this.loading = true;

        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        _this.trigger('collection:upload_item', [preloader, id]);
    }).on('progress', function(id, percentage) {
        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        const progressBar = preloader.querySelector('.progress-bar');
        progressBar && (progressBar.style.height = percentage + '%');

        if (percentage >= 100) {
            preloader.classList.add('processing');
        }
    }).on('complete', function(id, response) {
        if (isNaN(_this.collectionId)) {
            _this.collectionId = response.collectionId;
            _this.trigger('collection:created');
        }

        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        _this.trigger('collection:complete_item', [preloader, id]);

        const itemType = response.item_type;
        const templateSelector = _this._opts.itemSelectorTemplate.replace('{}', itemType);
        const template = _this.element.querySelector(templateSelector);
        if (!template) {
            _this.trigger('error', [id, `Invalid item_type: ${itemType}`]);
            return
        } else {
            const clone = document.importNode(template.content, true);
            const item = clone.querySelector(_this._opts.item);
            item.setAttribute('data-pk', response.id);
            item.setAttribute('data-item-type', itemType);

            const preview = clone.querySelector(_this._opts.itemPreview);
            preview && (preview.innerHTML = response.preview);

            const previewLink = clone.querySelector(_this._opts.itemLink);
            previewLink && (previewLink.href = response.url);

            const fileName = clone.querySelector(_this._opts.itemName);
            if (fileName) {
                fileName.title = response.name;
                fileName.textContent = response.name;
            }

            preloader.before(clone);
        }

        preloader.remove();
    }).on('cancel', function(id) {
        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        _this.trigger('collection:cancel_item', [preloader, id]);
        if (preloader) {
            // анимация удаления
            preloader.addEventListener('animationend', function() {
                preloader.remove();
            });
            preloader.classList.add(_this._opts.itemRemovingState);
        }
    }).on('error', function(id, messages) {
        collectError(messages);
        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        if (preloader) {
            // анимация удаления
            preloader.addEventListener('animationend', function() {
                preloader.remove();
            });
            preloader.classList.add(_this._opts.itemRemovingState);
        }
    }).on('all_complete', function() {
        _this.loading = false;
        showCollectedErrors();
    });
};

Collection.prototype.initSortable = function() {
    const _this = this;
    return Sortable.create(this.itemContainer, {
        animation: 0,
        draggable: this._opts.item,
        filter: this._opts.preloaderItem,
        handle: '.sortable-handler',
        ghostClass: 'sortable-ghost',
        onEnd: function() {
            const items = Array.from(_this.itemContainer.querySelectorAll(_this._opts.item));
            const order = items.map(function(item) {
                if (!item.matches(_this._opts.preloaderItem)) {
                    return item.dataset.pk;
                }
            }).filter(Boolean);

            const data = new FormData();
            const params = getPaperParams(_this.element);
            Object.keys(params).forEach(function(name) {
                data.append(name, params[name]);
            });
            data.append('collectionId', _this.collectionId.toString());
            data.append('order', order.join(','));

            fetch(_this._opts.urls.sortItems, {
                method: 'POST',
                credentials: 'same-origin',
                body: data
            }).then(function(response) {
                if (!response.ok) {
                    const error = new Error(`${response.status} ${response.statusText}`);
                    error.response = response;
                    throw error;
                }
                return response.json();
            }).then(function(response) {
                if (response.errors && response.errors.length) {
                    const error = new Error('Invalid request');
                    error.response = response;
                    throw error
                }
            }).catch(function(error) {
                if ((typeof error === 'object') && error.response && error.response.errors) {
                    showError(error.response.errors);
                } else if (error instanceof Error) {
                    showError(error.message);
                } else {
                    showError(error);
                }
            })
        },
    });
};

/**
 * Удаление всех элементов галереи из контейнера.
 */
Collection.prototype.cleanItems = function() {
    while (this.itemContainer.firstChild) {
        this.itemContainer.removeChild(this.itemContainer.firstChild);
    }
};

/**
 * Создание коллекции.
 * @private
 */
Collection.prototype._createCollection = function() {
    if (!isNaN(this.collectionId)) {
        return
    }

    const data = new FormData();
    const params = getPaperParams(this.element);
    Object.keys(params).forEach(function(name) {
        data.append(name, params[name]);
    });

    const _this = this;
    Promise.all([
        preloader.show(),
        fetch(this._opts.urls.createCollection, {
            method: 'POST',
            credentials: 'same-origin',
            body: data
        })
    ]).then(function(values) {
        const response = values[1];
        if (!response.ok) {
            const error = new Error(`${response.status} ${response.statusText}`);
            error.response = response;
            throw error;
        }
        return response.json();
    }).then(function(response) {
        if (response.errors && response.errors.length) {
            const error = new Error('Invalid request');
            error.response = response;
            throw error
        }

        preloader.hide();
        _this.collectionId = response.collection_id;
        _this.trigger('collection:created');
    }).catch(function(error) {
        preloader.hide();
        if ((typeof error === 'object') && error.response && error.response.errors) {
            showError(error.response.errors);
        } else if (error instanceof Error) {
            showError(error.message);
        } else {
            showError(error);
        }
    });
};

/**
 * Удаление элемента коллекции.
 * @param item
 * @private
 */
Collection.prototype._deleteItem = function(item) {
    if (isNaN(this.collectionId)) {
        return
    }

    const instance_id = parseInt(item && item.dataset.pk);
    if (isNaN(instance_id)) {
        return
    }

    const data = new FormData();
    const params = getPaperParams(this.element);
    Object.keys(params).forEach(function(name) {
        data.append(name, params[name]);
    });
    data.append('collectionId', this.collectionId.toString());
    data.append('instance_id', instance_id.toString());
    data.append('item_type', item.dataset.itemType);

    const _this = this;
    Promise.all([
        preloader.show(),
        fetch(this._opts.urls.deleteItem, {
            method: 'POST',
            credentials: 'same-origin',
            body: data
        })
    ]).then(function(values) {
        const response = values[1];
        if (!response.ok) {
            const error = new Error(`${response.status} ${response.statusText}`);
            error.response = response;
            throw error;
        }

        return response.json();
    }).then(function(response) {
        if (response.errors && response.errors.length) {
            const error = new Error('Invalid request');
            error.response = response;
            throw error
        }

        preloader.hide();

        // анимация удаления
        item.addEventListener('animationend', function() {
            item.remove();
        });
        item.classList.add(_this._opts.itemRemovingState);
    }).catch(function(error) {
        preloader.hide();
        if ((typeof error === 'object') && error.response && error.response.errors) {
            showError(error.response.errors);
        } else if (error instanceof Error) {
            showError(error.message);
        } else {
            showError(error);
        }
    });
};

/**
 * Отправка формы редактирования элемента.
 * @param item
 * @param $dialog
 * @private
 */
Collection.prototype._changeItem = function(item, $dialog) {
    if (isNaN(this.collectionId)) {
        return
    }

    const instance_id = parseInt(item && item.dataset.pk);
    if (isNaN(instance_id)) {
        return
    }

    const _this = this;
    const $form = $dialog.find('form');
    Promise.all([
        preloader.show(),
        fetch($form.prop('action'), {
            method: 'POST',
            credentials: 'same-origin',
            body: new FormData($form.get(0))
        })
    ]).then(function(values) {
        const response = values[1];
        if (!response.ok) {
            const error = new Error(`${response.status} ${response.statusText}`);
            error.response = response;
            throw error;
        }

        return response.json();
    }).then(function(response) {
        if (response.errors && response.errors.length) {
            const error = new Error('Invalid request');
            error.response = response;
            throw error
        }

        preloader.hide();
        formUtils.cleanFormErrors($form.get(0));
        if (response.form_errors) {
            formUtils.addFormErrorsFromJSON($form.get(0), response.form_errors);
        } else {
            $dialog.modal('hide');

            const preview = item.querySelector(_this._opts.itemPreview);
            preview && (preview.innerHTML = response.preview);

            const previewLink = item.querySelector(_this._opts.itemLink);
            previewLink && (previewLink.href = response.url);

            const fileName = item.querySelector(_this._opts.itemName);
            if (fileName) {
                fileName.title = response.name;
                fileName.textContent = response.name;
            }
        }
    }).catch(function(error) {
        preloader.hide();
        if ((typeof error === 'object') && error.response && error.response.errors) {
            showError(error.response.errors);
        } else if (error instanceof Error) {
            showError(error.message);
        } else {
            showError(error);
        }
    });
};

/**
 * Удаление галереи.
 * @private
 */
Collection.prototype._deleteCollection = function() {
    if (isNaN(this.collectionId)) {
        return
    }

    const data = new FormData();
    const params = getPaperParams(this.element);
    Object.keys(params).forEach(function(name) {
        data.append(name, params[name]);
    });
    data.append('collectionId', this.collectionId.toString());

    // отмена всех текущих загрузок. По идее, их и так быть не должно,
    // т.к. кнопка блокируется.
    this.uploader.uploader.cancelAll();

    const _this = this;
    Promise.all([
        preloader.show(),
        fetch(this._opts.urls.deleteCollection, {
            method: 'POST',
            credentials: 'same-origin',
            body: data
        })
    ]).then(function(values) {
        const response = values[1];
        if (!response.ok) {
            const error = new Error(`${response.status} ${response.statusText}`);
            error.response = response;
            throw error;
        }
        return response.json();
    }).then(function(response) {
        if (response.errors && response.errors.length) {
            const error = new Error('Invalid request');
            error.response = response;
            throw error
        }

        let lastItem = null;
        Array.from(_this.itemContainer.children).forEach(function(item) {
            item.classList.add(_this._opts.itemRemovingState);
            lastItem = item;
        });

        if (lastItem) {
            lastItem.addEventListener('animationend', function() {
                _this.cleanItems();
                _this.collectionId = '';
                _this.trigger('collection:deleted');
                preloader.hide();
            });
        } else {
            _this.cleanItems();
            _this.collectionId = '';
            _this.trigger('collection:deleted');
            preloader.hide();
        }
    }).catch(function(error) {
        preloader.hide();
        if ((typeof error === 'object') && error.response && error.response.errors) {
            showError(error.response.errors);
        } else if (error instanceof Error) {
            showError(error.message);
        } else {
            showError(error);
        }
    });
};

/**
 * Выделение элемента галереи.
 * @param {HTMLElement} item
 * @param {Boolean} state
 * @private
 */
Collection.prototype._checkItem = function(item, state=true) {
    item.classList.toggle(this._opts.itemCheckedState, state);
    const checkbox = item.querySelector(this._opts.itemCheckbox);
    checkbox.checked = state;
};

Collection.prototype.addListeners = function() {
    const _this = this;

    // создание галереи
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.createButton)) {
            return
        }

        event.preventDefault();
        _this._createCollection();
    });

    // удаление галереи
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.deleteButton)) {
            return
        }

        event.preventDefault();

        bootbox.dialog({
            size: 'small',
            title: gettext('Confirmation'),
            message: gettext('Are you sure you want to <b>DELETE</b> this collection?'),
            onEscape: true,
            buttons: {
                cancel: {
                    label: gettext('Cancel'),
                    className: 'btn-outline-info'
                },
                confirm: {
                    label: gettext('Delete'),
                    className: 'btn-danger',
                    callback: function() {
                        _this._deleteCollection();
                    }
                }
            }
        });
    });

    // редактирование элемента
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.changeItemButton)) {
            return
        }

        event.preventDefault();

        const item = event.target.closest(_this._opts.item);
        const instance_id = parseInt(item && item.dataset.pk);
        if (isNaN(instance_id)) {
            return
        }

        const data = new FormData();
        const params = getPaperParams(_this.element);
        Object.keys(params).forEach(function(name) {
            data.append(name, params[name]);
        });
        data.append('collectionId', _this.collectionId.toString());
        data.append('instance_id', instance_id.toString());
        data.append('item_type', item.dataset.itemType);
        const queryString = new URLSearchParams(data).toString();

        Promise.all([
            preloader.show(),
            fetch(`${_this._opts.urls.changeItem}?${queryString}`, {
                credentials: 'same-origin',
            })
        ]).then(function(values) {
            const response = values[1];
            if (!response.ok) {
                const error = new Error(`${response.status} ${response.statusText}`);
                error.response = response;
                throw error;
            }

            return response.json();
        }).then(function(response) {
            if (response.errors && response.errors.length) {
                const error = new Error('Invalid request');
                error.response = response;
                throw error
            }

            preloader.hide();
            const $dialog = bootbox.dialog({
                title: gettext('Edit file'),
                message: response.form,
                onEscape: true,
                buttons: {
                    cancel: {
                        label: gettext('Cancel'),
                        className: 'btn-outline-info'
                    },
                    ok: {
                        label: gettext('Save'),
                        className: 'btn-success',
                        callback: function() {
                            _this._changeItem(item, this);
                            return false;
                        }
                    }
                }
            });

            const $form = $dialog.find('form');
            $form.on('submit', function() {
                _this._changeItem(item, $dialog);
                return false;
            });
        }).catch(function(error) {
            preloader.hide();
            if ((typeof error === 'object') && error.response && error.response.errors) {
                showError(error.response.errors);
            } else if (error instanceof Error) {
                showError(error.message);
            } else {
                showError(error);
            }
        });
    });

    // отмена загрузки
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.cancelItemButton)) {
            return
        }

        event.preventDefault();
        const item = event.target.closest(_this._opts.item);
        const queueId = parseInt(item.dataset.queueId);
        _this.uploader.uploader.cancel(queueId);
    });

    // удаление элемента
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.deleteItemButton)) {
            return
        }

        event.preventDefault();

        bootbox.dialog({
            size: 'small',
            title: gettext('Confirmation'),
            message: gettext('Are you sure you want to <b>DELETE</b> this file?'),
            onEscape: true,
            buttons: {
                cancel: {
                    label: gettext('Cancel'),
                    className: 'btn-outline-info'
                },
                confirm: {
                    label: gettext('Delete'),
                    className: 'btn-danger',
                    callback: function() {
                        const item = event.target.closest(_this._opts.item);
                        _this._deleteItem(item);
                    }
                }
            }
        });
    });

    // выделение элемента галереи
    let lastChecked = null;
    this.element.addEventListener('click', function(event) {
        const item = event.target.closest(_this._opts.item);
        if (!item) {
            return
        }

        let target_state;
        let checkbox = event.target.closest(_this._opts.itemCheckbox);
        if (!checkbox) {
            // если клик на сам элемент, то выделение работает только в случае,
            // когда была зажата клавиша Ctrl (или Shift для массового выделения)
            if (!event.ctrlKey && !event.shiftKey) {
                return
            }

            checkbox = item.querySelector(_this._opts.itemCheckbox);
            if (!checkbox) {
                return
            }
            target_state = !checkbox.checked;
        } else {
            // при клике на чекбокс целевое состяние уже достигнуто
            target_state = checkbox.checked;
        }

        if (lastChecked && event.shiftKey && (lastChecked !== item)) {
            const items = Array.from(_this.itemContainer.querySelectorAll(_this._opts.item));
            const lastIndex = items.indexOf(lastChecked);
            const targetIndex = items.indexOf(item);
            const startIndex = Math.min(lastIndex, targetIndex);
            const endIndex = Math.max(lastIndex, targetIndex);
            const item_slice = items.slice(startIndex, endIndex + 1);
            item_slice.forEach(function(item) {
                _this._checkItem(item, target_state)
            });
        } else {
            _this._checkItem(item, target_state);
        }

        lastChecked = item;
    });

    // удаление выделенных элементов при нижатии Delete
    this.element.addEventListener('keyup', function(event) {
        if (event.code === 'Delete') {
            const items = Array.from(_this.itemContainer.querySelectorAll(_this._opts.item));
            const checkedItems = items.filter(function(item) {
                const checkbox = item.querySelector(_this._opts.itemCheckbox);
                return checkbox.checked;
            });

            if (checkedItems.length) {
                bootbox.dialog({
                    size: 'small',
                    title: gettext('Confirmation'),
                    message: gettext(`Are you sure you want to <b>DELETE</b> the selected <b>${checkedItems.length}</b> file(s)?`),
                    onEscape: true,
                    buttons: {
                        cancel: {
                            label: gettext('Cancel'),
                            className: 'btn-outline-info'
                        },
                        confirm: {
                            label: gettext('Delete'),
                            className: 'btn-danger',
                            callback: function() {
                                checkedItems.forEach(function(item) {
                                    _this._deleteItem(item);
                                });
                            }
                        }
                    }
                });
            }
        }
    });

    // просмотр при двойном клике
    this.element.addEventListener('dblclick', function(event) {
        const item = event.target.closest(_this._opts.item);
        if (!item) {
            return
        }

        const itemLink = item.querySelector(_this._opts.itemLink);
        if (itemLink) {
            itemLink.dispatchEvent(new MouseEvent('click', {
                bubbles: true,
                cancelable: true
            }));
        }
    });
};


function initWidget(element) {
    if (element.closest('.empty-form')) {
        return
    }

    new Collection(element, {
        urls: {
            createCollection: element.dataset.createCollectionUrl,
            deleteCollection: element.dataset.deleteCollectionUrl,
            uploadItem: element.dataset.uploadItemUrl,
            changeItem: element.dataset.changeItemUrl,
            deleteItem: element.dataset.deleteItemUrl,
            sortItems: element.dataset.sortItemsUrl
        }
    });
}


function initWidgets(root = document.body) {
    let file_selector = '.collection';
    root.matches(file_selector) && initWidget(root);
    root.querySelectorAll(file_selector).forEach(initWidget);
}


whenDomReady(initWidgets);
emitters.dom.on('mutate', initWidgets);
