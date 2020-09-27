/* global gettext */

import deepmerge from "deepmerge";
import {Uploader, getPaperParams} from "./_uploader";
import {showError} from "./_utils";

// PaperAdmin API
const EventEmitter = window.paperAdmin.EventEmitter;
const modals = window.paperAdmin.modals;
const formUtils = window.paperAdmin.formUtils;

/**
 * @fires upload:submit
 * @fires upload:submitted
 * @fires upload:upload
 * @fires upload:created
 * @fires upload:deleted
 * @fires upload:complete
 * @fires upload:cancel
 * @param element
 * @param options
 * @constructor
 */
function BaseWidget(element, options) {
    /**
     * @type object
     */
    this._opts = deepmerge({
        input: '',
        uploadButton: '',
        cancelButton: '',
        changeButton: '',
        deleteButton: '',

        link: '',

        urls: {
            upload: '',
            change: '',
            delete: ''
        }
    }, options || {});

    this.element = element;

    this.input = this.element.querySelector(this._opts.input);
    if (!this.input) {
        throw new Error(`Not found element "${this._opts.input}"`);
    }

    this.uploadButton = this.element.querySelector(this._opts.uploadButton);
    if (!this.uploadButton) {
        throw new Error(`Not found element "${this._opts.uploadButton}"`);
    }

    this.cancelButton = this.element.querySelector(this._opts.cancelButton);
    if (!this.cancelButton) {
        throw new Error(`Not found element "${this._opts.cancelButton}"`);
    }

    this.changeButton = this.element.querySelector(this._opts.changeButton);
    if (!this.changeButton) {
        throw new Error(`Not found element "${this._opts.changeButton}"`);
    }

    this.deleteButton = this.element.querySelector(this._opts.deleteButton);
    if (!this.deleteButton) {
        throw new Error(`Not found element "${this._opts.deleteButton}"`);
    }

    // инициализация
    this.loading = false;
    this.empty = isNaN(this.instanceId);

    this.uploader = this.initUploader();
    this.addListeners();
}

BaseWidget.prototype = Object.create(EventEmitter.prototype);

Object.defineProperty(BaseWidget.prototype, 'instanceId', {
    get: function() {
        return parseInt(this.input.value);
    },
    set: function(value) {
        this.input.value = parseInt(value) || '';
    }
});

Object.defineProperty(BaseWidget.prototype, 'empty', {
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
        } else {
            this.element.classList.remove('empty');
        }
        this._empty = newValue;
    }
});

Object.defineProperty(BaseWidget.prototype, 'loading', {
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
        } else {
            this.element.classList.remove('loading');
            this.element.classList.remove('processing');
        }
        this._loading = newValue;
    }
});

/**
 * Инициализация загрузчика файлов.
 */
BaseWidget.prototype.initUploader = function() {
    const _this = this;
    return new Uploader(this.element, {
        url: this._opts.urls.upload,
        button: this.uploadButton,
        dropzones: this.element.querySelectorAll('.dropzone-overlay'),
        configuration: JSON.parse(this.element.dataset.configuration),
    }).on('submitted', function(id) {
        _this.trigger('upload:submitted', [id]);
    }).on('upload', function(id) {
        _this.loading = true;

        const progressBar = _this.element.querySelector('.progress-bar');
        progressBar && (progressBar.style.width = '');
        _this.trigger('upload:upload', [id]);
    }).on('progress', function(id, percentage) {
        const progressBar = _this.element.querySelector('.progress-bar');
        progressBar && (progressBar.style.width = percentage + '%');

        if (percentage >= 100) {
            _this.element.classList.add('processing');
        }
    }).on('complete', function(id, response) {
        _this.empty = false;
        _this.instanceId = response.id;
        _this.trigger('upload:created');

        const fileName = _this.element.querySelector('.file-name');
        fileName && (fileName.textContent = response.name);

        const fileInfo = _this.element.querySelector('.file-info');
        fileInfo && (fileInfo.textContent = response.file_info);

        const previewLink = _this.element.querySelector(_this._opts.link);
        previewLink && (previewLink.href = response.url);

        _this.trigger('upload:complete');
    }).on('cancel', function(id) {
        _this.trigger('upload:cancel', [id]);
    }).on('error', function(id, messages) {
        showError(messages);
    }).on('all_complete', function() {
        _this.loading = false;
    });
};

/**
 * Отправка формы редактирования файла.
 * @param modal
 * @private
 */
BaseWidget.prototype._change = function(modal) {
    if (isNaN(this.instanceId)) {
        return
    }

    const _this = this;
    const $form = $(modal._element).find('form');
    const preloader = modals.showPreloader();
    fetch($form.prop('action'), {
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

        preloader.destroy();
        formUtils.cleanFormErrors($form.get(0));
        if (response.form_errors) {
            formUtils.addFormErrorsFromJSON($form.get(0), response.form_errors);
        } else {
            modal.destroy();

            const fileName = _this.element.querySelector('.file-name');
            fileName && (fileName.textContent = response.name);

            const fileInfo = _this.element.querySelector('.file-info');
            fileInfo && (fileInfo.textContent = response.file_info);

            const previewLink = _this.element.querySelector(_this._opts.link);
            previewLink && (previewLink.href = response.url);
        }
    }).catch(function(error) {
        preloader.destroy();

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
 * Удаление файла.
 * @private
 */
BaseWidget.prototype._delete = function() {
    if (isNaN(this.instanceId)) {
        return
    }

    const data = new FormData();
    const params = getPaperParams(this.element);
    Object.keys(params).forEach(function(name) {
        data.append(name, params[name]);
    });
    data.append('instance_id', this.instanceId.toString());

    const _this = this;
    const preloader = modals.showPreloader();
    fetch(this._opts.urls.delete, {
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

        preloader.destroy();
        _this.empty = true;
        _this.instanceId = '';

        const fileName = _this.element.querySelector('.file-name');
        fileName && (fileName.textContent = '');

        const fileInfo = _this.element.querySelector('.file-info');
        fileInfo && (fileInfo.textContent = '');

        _this.trigger('upload:deleted');
    }).catch(function(error) {
        preloader.destroy();

        if ((typeof error === 'object') && error.response && error.response.errors) {
            showError(error.response.errors);
        } else if (error instanceof Error) {
            showError(error.message);
        } else {
            showError(error);
        }
    });
};

BaseWidget.prototype.addListeners = function() {
    const _this = this;

    // отмена загрузки
    this.cancelButton.addEventListener('click', function(event) {
        event.preventDefault();
        _this.loading = false;
        _this.uploader.uploader.cancelAll();
    });

    // удаление файла
    this.deleteButton.addEventListener('click', function(event) {
        event.preventDefault();

        modals.createModal({
            title: gettext('Confirmation'),
            message: gettext('Are you sure you want to <b>DELETE</b> this file?'),
            buttons: [{
                label: gettext('Cancel'),
                className: 'btn-outline-info'
            }, {
                autofocus: true,
                label: gettext('Delete'),
                className: 'btn-danger',
                callback: function() {
                    _this._delete();
                }
            }]
        }).show();
    });

    // редактирование файла
    this.changeButton.addEventListener('click', function(event) {
        event.preventDefault();

        const data = new FormData();
        const params = getPaperParams(_this.element);
        Object.keys(params).forEach(function(name) {
            data.append(name, params[name]);
        });
        data.append('instance_id', _this.instanceId.toString());
        const queryString = new URLSearchParams(data).toString();

        const preloader = modals.showPreloader();
        fetch(`${_this._opts.urls.change}?${queryString}`, {
            credentials: 'same-origin',
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

            preloader.destroy();

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
                        _this._change(this);
                        return false;
                    }
                }]
            }).show();

            const $form = $(modal._element).find('form');
            $form.on('submit', function() {
                _this._change(modal);
                return false;
            });
        }).catch(function(error) {
            preloader.destroy();

            if ((typeof error === 'object') && error.response && error.response.errors) {
                showError(error.response.errors);
            } else if (error instanceof Error) {
                showError(error.message);
            } else {
                showError(error);
            }
        });
    });
};


export {BaseWidget};
