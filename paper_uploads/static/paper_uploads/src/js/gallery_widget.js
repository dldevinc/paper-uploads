/* global gettext */

import deepmerge from "deepmerge";
import {Uploader, getPaperParams} from "./_uploader";
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
import "../css/widget_gallery.scss";


/**
 * @param element
 * @param options
 * @fires gallery:created
 * @fires gallery:deleted
 * @fires gallery:error
 * @fires gallery:submit_item
 * @fires gallery:upload_item
 * @fires gallery:cancel_item
 * @fires gallery:complete_item
 * @constructor
 */
function Gallery(element, options) {
    /**
     * @type Object
     */
    this._opts = deepmerge({
        input: '.gallery__input',
        itemContainer: '.gallery__items',
        item: '.gallery__item',
        uploadButton: '.gallery__upload-button',
        deleteButton: '.gallery__delete-button',
        preloaderItem: '.gallery__item--preloader',
        preloaderTemplate: '.gallery__item-preloader',

        itemPreview: '.gallery__item-preview',
        itemLink: '.gallery__item-link',
        itemCheckbox: '.gallery__item-checkbox',
        itemName: '.gallery__item-name',
        changeItemButton: '.gallery__item-change-button',
        deleteItemButton: '.gallery__item-delete-button',
        itemSelectorTemplate: '.gallery__{}-item-template',
        itemCoverClass: 'gallery__item--cover',

        urls: {
            deleteGallery: '',
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

Gallery.prototype = Object.create(EventEmitter.prototype);

Object.defineProperty(Gallery.prototype, 'galleryId', {
    get: function() {
        return parseInt(this.input.value);
    },
    set: function(value) {
        this.input.value = parseInt(value) || '';
    }
});

Object.defineProperty(Gallery.prototype, 'empty', {
    get: function() {
        return Boolean(this._empty);
    },
    set: function(value) {
        const newValue = Boolean(value);
        if (newValue === Boolean(this._empty)) {
            return
        }
        if (newValue) {
            this.element.classList.add('empty');
            this.deleteButton.disabled = true;
        } else {
            this.element.classList.remove('empty');
            this.deleteButton.disabled = false;
        }
        this._empty = newValue;
    }
});

/**
 * Инициализация галереи
 */
Gallery.prototype.init = function() {
    this.empty = isNaN(this.galleryId);
    this.uploader = this.initUploader();
    this.sortable = this.initSortable();
    this.addListeners();
};

/**
 * Инициализация загрузчика картинок.
 */
Gallery.prototype.initUploader = function() {
    const _this = this;
    return new Uploader(this.element, {
        url: this._opts.urls.uploadItem,
        multiple: true,
        button: this.uploadButton,
        dropzones: this.element.querySelectorAll('.dropzone-overlay'),
        validation: JSON.parse(this.element.dataset.validation),
        extraData: {
            gallery_id: function() {
                return _this.galleryId;
            }
        },
    }).on('submit', function(id) {
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

        _this.trigger('gallery:submit_item', [preloader, id]);
    }).on('upload', function(id) {
        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        _this.trigger('gallery:upload_item', [preloader, id]);
    }).on('progress', function(id, percentage) {
        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        const progressBar = preloader.querySelector('.progress-bar');
        progressBar && (progressBar.style.height = percentage + '%');

        if (percentage >= 100) {
            preloader.classList.add('processing');
        }
    }).on('complete', function(id, response) {
        if (_this.empty) {
            _this.empty = false;
            _this.galleryId = response.gallery_id;
            _this.trigger('gallery:created');
        }

        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        _this.trigger('gallery:complete_item', [preloader, id]);

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

        // set cover class
        const currentCover = _this.itemContainer.querySelector(`.${_this._opts.itemCoverClass}`);
        if (response.cover) {
            const newCover = _this.itemContainer.querySelector(`${_this._opts.item}[data-pk="${response.cover}"]`);
            if (newCover !== currentCover) {
                currentCover && currentCover.classList.remove(_this._opts.itemCoverClass);
                newCover && newCover.classList.add(_this._opts.itemCoverClass);
            }
        }
    }).on('cancel', function(id) {
        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        _this.trigger('gallery:cancel_item', [preloader, id]);
        preloader && preloader.remove();
    }).on('error', function(id, messages) {
        const preloader = _this.itemContainer.querySelector(`.item-preloader-${id}`);
        preloader && preloader.remove();
        collectError(messages);
    }).on('all_complete', function() {
        showCollectedErrors();
    });
};

Gallery.prototype.initSortable = function() {
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
            data.append('gallery_id', _this.galleryId.toString());
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
Gallery.prototype.cleanItems = function() {
    while (this.itemContainer.firstChild) {
        this.itemContainer.removeChild(this.itemContainer.firstChild);
    }
};

Gallery.prototype._deleteItem = function(item) {
    if (item.matches(this._opts.preloaderItem)) {
        // если файл еще не загружен - отменяем загрузку
        if (!item.classList.contains('processing')) {
            const queueId = parseInt(item.dataset.queueId);
            this.uploader.uploader.cancel(queueId);
        }
        return
    }

    if (isNaN(this.galleryId)) {
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
    data.append('gallery_id', this.galleryId.toString());
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

        // set cover class
        const currentCover = _this.itemContainer.querySelector(`.${_this._opts.itemCoverClass}`);
        if (response.cover) {
            const newCover = _this.itemContainer.querySelector(`${_this._opts.item}[data-pk="${response.cover}"]`);
            if (newCover !== currentCover) {
                currentCover && currentCover.classList.remove(_this._opts.itemCoverClass);
                newCover && newCover.classList.add(_this._opts.itemCoverClass);
            }
        }

        preloader.hide();
        item.remove();
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
Gallery.prototype._changeItem = function(item, $dialog) {
    if (isNaN(this.galleryId)) {
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
Gallery.prototype._deleteGallery = function() {
    if (isNaN(this.galleryId)) {
        return
    }

    const data = new FormData();
    const params = getPaperParams(this.element);
    Object.keys(params).forEach(function(name) {
        data.append(name, params[name]);
    });
    data.append('gallery_id', this.galleryId.toString());

    const _this = this;
    fetch(this._opts.urls.deleteGallery, {
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

        _this.cleanItems();
        _this.empty = true;
        _this.galleryId = '';
        _this.trigger('gallery:deleted');
    }).catch(function(error) {
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
Gallery.prototype._checkItem = function(item, state=true) {
    item.classList.toggle('gallery__item--checked', state);
    const checkbox = item.querySelector(this._opts.itemCheckbox);
    checkbox.checked = state;
};

Gallery.prototype.addListeners = function() {
    const _this = this;

    // удаление галереи
    this.element.addEventListener('click', function(event) {
        if (!event.target.closest(_this._opts.deleteButton)) {
            return
        }

        event.preventDefault();

        bootbox.dialog({
            size: 'small',
            title: gettext('Confirmation'),
            message: gettext('Are you sure you want to <b>DELETE</b> this gallery?'),
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
                        _this._deleteGallery();
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
        data.append('gallery_id', _this.galleryId.toString());
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

    // отмена загрузки / удаление элемента
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

    new Gallery(element, {
        urls: {
            deleteGallery: element.dataset.deleteGalleryUrl,
            uploadItem: element.dataset.uploadItemUrl,
            changeItem: element.dataset.changeItemUrl,
            deleteItem: element.dataset.deleteItemUrl,
            sortItems: element.dataset.sortItemsUrl
        }
    });
}


function initWidgets(root = document.body) {
    let file_selector = '.gallery';
    root.matches(file_selector) && initWidget(root);
    root.querySelectorAll(file_selector).forEach(initWidget);
}


whenDomReady(initWidgets);
emitters.dom.on('mutate', initWidgets);
