/* global gettext */

import deepmerge from "deepmerge";
import allSettled from "promise.allsettled";
import EventEmitter from "wolfy87-eventemitter";
import {Uploader, ValidationError, getPaperParams} from "./_uploader";
import {showError, collectError, showCollectedErrors} from "./_utils";

// PaperAdmin API
const Sortable = window.paperAdmin.Sortable;
const modals = window.paperAdmin.modals;
const emitters = window.paperAdmin.emitters;
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
        preloaderItem: '.collection-item--preloader',

        templates: '.collection__{}-item-template',

        collection: {
            input: '.collection__input',
            itemList: '.collection__items',
            item: '.collection__item',
            dropzone: '.dropzone-overlay',
            createButton: '.collection__create-button',
            uploadButton: '.collection__upload-button',
            deleteButton: '.collection__delete-button',

            states: {
                empty: 'collection--empty',
            },
        },

        item: {
            caption: '.collection-item__name',
            preview: '.collection-item__preview',
            checkbox: '.collection-item__checkbox',
            view_button: '.collection-item__view-button',
            edit_button: '.collection-item__edit-button',
            cancel_button: '.collection-item__cancel-button',
            delete_button: '.collection-item__delete-button',

            states: {
                checked: 'collection-item--checked',
                removing: 'collection-item--removing',
                processing: 'collection-item--processing',
            },
        },

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

    this.input = this.element.querySelector(this._opts.collection.input);
    if (!this.input) {
        throw new Error(`Not found element "${this._opts.collection.input}"`);
    }

    this.itemList = this.element.querySelector(this._opts.collection.itemList);
    if (!this.itemList) {
        throw new Error(`Not found element "${this._opts.collection.itemList}"`);
    }

    this.createButton = this.element.querySelector(this._opts.collection.createButton);
    if (!this.createButton) {
        throw new Error(`Not found element "${this._opts.collection.createButton}"`);
    }

    this.uploadButton = this.element.querySelector(this._opts.collection.uploadButton);
    if (!this.uploadButton) {
        throw new Error(`Not found element "${this._opts.collection.uploadButton}"`);
    }

    this.deleteButton = this.element.querySelector(this._opts.collection.deleteButton);
    if (!this.deleteButton) {
        throw new Error(`Not found element "${this._opts.collection.deleteButton}"`);
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
            this.createButton.hidden = false;
            this.uploadButton.hidden = true;
            this.deleteButton.hidden = true;
            this.element.classList.add(this._opts.collection.states.empty);

            const uploadInput = this.uploadButton.querySelector('input[type="file"]');
            uploadInput && (uploadInput.disabled = true);
        } else {
            // коллекция инициализирована
            this.input.value = newValue;
            this.createButton.hidden = true;
            this.uploadButton.hidden = false;
            this.deleteButton.hidden = false;
            this.element.classList.remove(this._opts.collection.states.empty);

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
 * Возвращает созданный DOM-элемент элемента коллекции из HTML-шаблона.
 * @param type
 * @returns {DocumentFragment}
 * @private
 */
Collection.prototype._createItem = function(type) {
    const selector = this._opts.templates.replace('{}', type);
    const template = this.element.querySelector(selector);
    return document.importNode(template.content, true);
};

/**
 * Добавление прелоадера нового элемента.
 * @param id
 * @returns {HTMLElement}
 * @private
 */
Collection.prototype._createPreloader = function(id) {
    const clone = this._createItem('preloader');
    const preloader = clone.querySelector(this._opts.collection.item);
    this.itemList.append(clone);

    preloader.dataset.queueId = id;
    preloader.classList.add(`preloader-${id}`);

    const file = this.uploader.uploader.getFile(id);
    const caption = preloader.querySelector(this._opts.item.caption);
    if (caption) {
        caption.title = file.name;
        caption.textContent = file.name;
    }

    return preloader;
};

/**
 * Поиск DOM-элемента, представляющего прелоадер для указанного элемента коллекции.
 * @param id
 * @returns {HTMLElement}
 * @private
 */
Collection.prototype._findPreloader = function(id) {
    return this.itemList.querySelector(`.preloader-${id}`);
}


/**
 * Возвращает созданный DOM-элемент элемента коллекции из HTML-шаблона.
 * @param response
 * @returns {DocumentFragment}
 * @private
 */
Collection.prototype._createUploadedItem = function(response) {
    const itemType = response.item_type;
    const clone = this._createItem(itemType);

    const item = clone.querySelector(this._opts.collection.item);
    item.setAttribute('data-pk', response.id);
    item.setAttribute('data-item-type', itemType);

    const preview = clone.querySelector(this._opts.item.preview);
    preview && (preview.innerHTML = response.preview);

    const viewButton = clone.querySelector(this._opts.item.view_button);
    viewButton && (viewButton.href = response.url);

    const caption = clone.querySelector(this._opts.item.caption);
    if (caption) {
        caption.title = response.caption;
        caption.textContent = response.caption;
    }

    return clone;
};


/**
 * Инициализация коллекции
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
        dropzones: this.element.querySelectorAll(this._opts.collection.dropzone),
        configuration: JSON.parse(this.element.dataset.configuration),
        params: {
            collectionId: function() {
                return _this.collectionId;
            },
            order: function(id) {
                const preloader = _this._findPreloader(id);
                return Array.from(_this.itemList.children).indexOf(preloader);
            }
        },
    }).on('submit', function() {
        if (isNaN(_this.collectionId)) {
            throw new ValidationError();
        }
    }).on('submitted', function(id) {
        const preloader = _this._createPreloader(id);
        emitters.dom.trigger('mutate', [preloader]);
        _this.trigger('collection:submit_item', [preloader, id]);
    }).on('upload', function(id) {
        _this.loading = true;

        const preloader = _this._findPreloader(id);
        _this.trigger('collection:upload_item', [preloader, id]);
    }).on('progress', function(id, percentage) {
        const preloader = _this._findPreloader(id);
        const progressBar = preloader.querySelector('.progress-bar');
        progressBar && (progressBar.style.height = percentage + '%');

        if (percentage >= 100) {
            preloader.classList.add(_this._opts.item.states.processing);
        }
    }).on('complete', function(id, response) {
        if (isNaN(_this.collectionId)) {
            _this.collectionId = response.collectionId;
            _this.trigger('collection:created');
        }

        const preloader = _this._findPreloader(id);
        _this.trigger('collection:complete_item', [preloader, id]);

        const clone = _this._createUploadedItem(response);
        preloader.before(clone);
        preloader.remove();
    }).on('cancel', function(id) {
        const preloader = _this._findPreloader(id);
        _this.trigger('collection:cancel_item', [preloader, id]);

        // анимация удаления
        preloader.addEventListener('animationend', function() {
            preloader.remove();
        });
        preloader.classList.add(_this._opts.item.states.removing);
    }).on('error', function(id, messages) {
        collectError(messages);
        const preloader = _this._findPreloader(id);

        // анимация удаления
        preloader.addEventListener('animationend', function() {
            preloader.remove();
        });
        preloader.classList.add(_this._opts.item.states.removing);
    }).on('all_complete', function() {
        _this.loading = false;
        showCollectedErrors();
    });
};

/**
 * Инициализация плагина Drag-n-Drop сортировки.
 */
Collection.prototype.initSortable = function() {
    const _this = this;
    return Sortable.create(this.itemList, {
        animation: 0,
        draggable: this._opts.collection.item,
        filter: this._opts.preloaderItem,
        handle: '.sortable-handler',
        ghostClass: 'sortable-ghost',
        onEnd: function() {
            const items = Array.from(_this.itemList.querySelectorAll(_this._opts.collection.item));
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
 * Создание коллекции.
 * @private
 * @returns {Promise}
 */
Collection.prototype._createCollection = function() {
    if (!isNaN(this.collectionId)) {
        return Promise.reject('collection already exists');
    }

    const data = new FormData();
    const params = getPaperParams(this.element);
    Object.keys(params).forEach(function(name) {
        data.append(name, params[name]);
    });

    const _this = this;
    return fetch(this._opts.urls.createCollection, {
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

        _this.collectionId = response.collection_id;
        _this.trigger('collection:created');
    });
};

/**
 * Удаление элемента коллекции.
 * @param item
 * @private
 * @returns {Promise}
 */
Collection.prototype._deleteItem = function(item) {
    if (isNaN(this.collectionId)) {
        return Promise.reject('collection required');
    }

    const instance_id = parseInt(item && item.dataset.pk);
    if (isNaN(instance_id)) {
        return Promise.reject('invalid ID')
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
    return fetch(this._opts.urls.deleteItem, {
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

        // анимация удаления
        item.addEventListener('animationend', function() {
            item.remove();
        });
        item.classList.add(_this._opts.item.states.removing);
    });
};

/**
 * Отправка формы редактирования элемента.
 * @param item
 * @param modal
 * @private
 * @returns {Promise}
 */
Collection.prototype._changeItem = function(item, modal) {
    if (isNaN(this.collectionId)) {
        return Promise.reject('collection required');
    }

    const instance_id = parseInt(item && item.dataset.pk);
    if (isNaN(instance_id)) {
        return Promise.reject('invalid ID')
    }

    const _this = this;
    const $form = $(modal._element).find('form');
    return fetch($form.prop('action'), {
        method: 'POST',
        credentials: 'same-origin',
        body: new FormData($form.get(0))
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

        formUtils.cleanFormErrors($form.get(0));
        if (response.form_errors) {
            formUtils.addFormErrorsFromJSON($form.get(0), response.form_errors);
        } else {
            modal.destroy();

            const preview = item.querySelector(_this._opts.item.preview);
            preview && (preview.innerHTML = response.preview);

            const viewButton = item.querySelector(_this._opts.item.view_button);
            viewButton && (viewButton.href = response.url);

            const caption = item.querySelector(_this._opts.item.caption);
            if (caption) {
                caption.title = response.caption;
                caption.textContent = response.caption;
            }
        }
    });
};

/**
 * Удаление DOM-содержимого коллекции.
 */
Collection.prototype.cleanItems = function() {
    while (this.itemList.firstChild) {
        this.itemList.removeChild(this.itemList.firstChild);
    }
};

/**
 * Удаление галереи.
 * @private
 * @returns {Promise}
 */
Collection.prototype._deleteCollection = function() {
    if (isNaN(this.collectionId)) {
        return Promise.reject('collection required')
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
    return fetch(this._opts.urls.deleteCollection, {
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

        let lastItem = null;
        Array.from(_this.itemList.children).forEach(function(item) {
            item.classList.add(_this._opts.item.states.removing);
            lastItem = item;
        });

        if (lastItem) {
            lastItem.addEventListener('animationend', function() {
                _this.cleanItems();
                _this.collectionId = '';
                _this.trigger('collection:deleted');
            });
        } else {
            _this.cleanItems();
            _this.collectionId = '';
            _this.trigger('collection:deleted');
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
    item.classList.toggle(this._opts.item.states.checked, state);
    const checkbox = item.querySelector(this._opts.item.checkbox);
    checkbox.checked = state;
};

Collection.prototype.addListeners = function() {
    const _this = this;

    // создание галереи
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.collection.createButton)) {
            return
        }

        event.preventDefault();

        modals.softPreloaderPromise(
            _this._createCollection()
        ).catch(function(error) {
            if ((typeof error === 'object') && error.response && error.response.errors) {
                showError(error.response.errors);
            } else if (error instanceof Error) {
                showError(error.message);
            } else {
                showError(error);
            }
        });
    });

    // удаление галереи
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.collection.deleteButton)) {
            return
        }

        event.preventDefault();

        modals.createModal({
            title: gettext('Confirmation'),
            message: gettext('Are you sure you want to <b>DELETE</b> this collection?'),
            buttons: [{
                label: gettext('Cancel'),
                className: 'btn-outline-info'
            }, {
                autofocus: true,
                label: gettext('Delete'),
                className: 'btn-danger',
                callback: function() {
                    modals.showSmartPreloader(
                        _this._deleteCollection()
                    ).catch(function(error) {
                        if ((typeof error === 'object') && error.response && error.response.errors) {
                            showError(error.response.errors);
                        } else if (error instanceof Error) {
                            showError(error.message);
                        } else {
                            showError(error);
                        }
                    });
                }
            }]
        }).show();
    });

    // редактирование элемента
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.item.edit_button)) {
            return
        }

        event.preventDefault();

        const item = event.target.closest(_this._opts.collection.item);
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

        modals.showSmartPreloader(
            fetch(`${_this._opts.urls.changeItem}?${queryString}`, {
                credentials: 'same-origin',
            }).then(function(response) {
                if (!response.ok) {
                    const error = new Error(`${response.status} ${response.statusText}`);
                    error.response = response;
                    throw error;
                }
                return response.json();
            })
        ).then(function(response) {
            if (response.errors && response.errors.length) {
                const error = new Error('Invalid request');
                error.response = response;
                throw error
            }

            const modal = modals.createModal({
                title: gettext('Edit file'),
                message: response.form,
                buttons: [{
                    label: gettext('Cancel'),
                    className: 'btn-outline-info'
                }, {
                    autofocus: true,
                    label: gettext('Save'),
                    className: 'btn-success',
                    callback: function() {
                        modals.showSmartPreloader(
                            _this._changeItem(item, modal)
                        ).catch(function(error) {
                            if ((typeof error === 'object') && error.response && error.response.errors) {
                                showError(error.response.errors);
                            } else if (error instanceof Error) {
                                showError(error.message);
                            } else {
                                showError(error);
                            }
                        });
                        return false;
                    }
                }]
            }).show();

            const $form = $(modal._element).find('form');
            $form.on('submit', function() {
                modals.showSmartPreloader(
                    _this._changeItem(item, modal)
                ).catch(function(error) {
                    if ((typeof error === 'object') && error.response && error.response.errors) {
                        showError(error.response.errors);
                    } else if (error instanceof Error) {
                        showError(error.message);
                    } else {
                        showError(error);
                    }
                });
                return false;
            });
        }).catch(function(error) {
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
        if (!event.target.closest(_this._opts.item.cancel_button)) {
            return
        }

        event.preventDefault();
        const item = event.target.closest(_this._opts.collection.item);
        const queueId = parseInt(item.dataset.queueId);
        _this.uploader.uploader.cancel(queueId);
    });

    // удаление элемента
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.item.delete_button)) {
            return
        }

        event.preventDefault();

        const item = event.target.closest(_this._opts.collection.item);

        modals.showSmartPreloader(
            _this._deleteItem(item)
        ).catch(function(error) {
            if ((typeof error === 'object') && error.response && error.response.errors) {
                showError(error.response.errors);
            } else if (error instanceof Error) {
                showError(error.message);
            } else {
                showError(error);
            }
        });
    });

    // выделение элемента галереи
    let lastChecked = null;
    this.element.addEventListener('click', function(event) {
        const item = event.target.closest(_this._opts.collection.item);
        if (!item) {
            return
        }

        let target_state;
        let checkbox = event.target.closest(_this._opts.item.checkbox);
        if (!checkbox) {
            // если клик на сам элемент, то выделение работает только в случае,
            // когда была зажата клавиша Ctrl (или Shift для массового выделения)
            if (!event.ctrlKey && !event.shiftKey) {
                return
            }

            checkbox = item.querySelector(_this._opts.item.checkbox);
            if (!checkbox) {
                return
            }
            target_state = !checkbox.checked;
        } else {
            // при клике на чекбокс целевое состояние уже достигнуто
            target_state = checkbox.checked;
        }

        if (lastChecked && event.shiftKey && (lastChecked !== item)) {
            const items = Array.from(_this.itemList.querySelectorAll(_this._opts.collection.item));
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

    // удаление выделенных элементов при нажатии Delete
    this.element.addEventListener('keyup', function(event) {
        if (event.code === 'Delete') {
            const items = Array.from(_this.itemList.querySelectorAll(_this._opts.collection.item));
            const checkedItems = items.filter(function(item) {
                const checkbox = item.querySelector(_this._opts.item.checkbox);
                return checkbox.checked;
            });

            if (checkedItems.length) {
                modals.createModal({
                    title: gettext('Confirmation'),
                    message: gettext(`Are you sure you want to <b>DELETE</b> the selected <b>${checkedItems.length}</b> file(s)?`),
                    buttons: [{
                        label: gettext('Cancel'),
                        className: 'btn-outline-info'
                    }, {
                        autofocus: true,
                        label: gettext('Delete'),
                        className: 'btn-danger',
                        callback: function() {
                            const delete_promises = checkedItems.map(function(item) {
                                return _this._deleteItem(item)
                            });

                            modals.showSmartPreloader(
                                allSettled(delete_promises)
                            ).then(function(results) {
                                for (let result of results) {
                                    if (result.status === 'rejected') {
                                        const error = result.reason;
                                        if ((typeof error === 'object') && error.response && error.response.errors) {
                                            collectError(error.response.errors);
                                        } else if (error instanceof Error) {
                                            collectError(error.message);
                                        } else {
                                            collectError(error);
                                        }
                                    }
                                }
                                showCollectedErrors();
                            });
                        }
                    }]
                }).show();
            }
        }
    });

    // просмотр при двойном клике
    this.element.addEventListener('dblclick', function(event) {
        const item = event.target.closest(_this._opts.collection.item);
        if (!item) {
            return
        }

        const viewButton = item.querySelector(_this._opts.item.view_button);
        if (viewButton) {
            viewButton.dispatchEvent(new MouseEvent('click', {
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


initWidgets();
emitters.dom.on('mutate', initWidgets);
