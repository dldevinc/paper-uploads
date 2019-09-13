/* global gettext */

import deepmerge from "deepmerge";
import {Uploader, getPaperParams} from "./_uploader";

// PaperAdmin API
const EventEmitter = window.paperAdmin.EventEmitter;
const whenDomReady = window.paperAdmin.whenDomReady;
const bootbox = window.paperAdmin.bootbox;
const emitters = window.paperAdmin.emitters;
const preloader = window.paperAdmin.preloader;
const formUtils = window.paperAdmin.formUtils;

// CSS
import "../css/widget_file.scss";


/**
 * @fires upload:submit
 * @fires upload:upload
 * @fires upload:created
 * @fires upload:deleted
 * @fires upload:complete
 * @fires upload:error
 * @param element
 * @param options
 * @constructor
 */
function FileWidget(element, options) {
    /**
     * @type object
     */
    this._opts = deepmerge({
        input: '.file-uploader__input',
        uploadButton: '.file-uploader__upload-button',
        changeButton: '.file-uploader__change-button',
        deleteButton: '.file-uploader__delete-button',

        link: '.file-uploader__link',

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

FileWidget.prototype = Object.create(EventEmitter.prototype);

Object.defineProperty(FileWidget.prototype, 'instanceId', {
    get: function() {
        return parseInt(this.input.value);
    },
    set: function(value) {
        this.input.value = parseInt(value) || '';
    }
});

Object.defineProperty(FileWidget.prototype, 'empty', {
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

Object.defineProperty(FileWidget.prototype, 'loading', {
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
        }
        this._loading = newValue;
    }
});

/**
 * Инициализация загрузчика файлов.
 */
FileWidget.prototype.initUploader = function() {
    const _this = this;
    return new Uploader(this.element, {
        url: this._opts.urls.upload,
        button: this.uploadButton,
        dropzones: this.element.querySelectorAll('.dropzone-overlay'),
        validation: JSON.parse(this.element.dataset.validation),
    }).on('submit', function(id) {
        _this.trigger('upload:submit', [id]);
    }).on('upload', function(id) {
        _this.loading = true;

        const progressBar = _this.element.querySelector('.progress-bar');
        progressBar && (progressBar.style.width = '');
        _this.trigger('upload:upload', [id]);
    }).on('progress', function(id, percentage) {
        const progressBar = _this.element.querySelector('.progress-bar');
        progressBar && (progressBar.style.width = percentage + '%');
    }).on('complete', function(id, response) {
        _this.empty = false;
        _this.instanceId = response.instance_id;
        _this.trigger('upload:created');

        _this.element.classList.remove('loading');

        const fileName = _this.element.querySelector('.file-name');
        fileName && (fileName.textContent = response.name);

        const fileInfo = _this.element.querySelector('.file-info');
        fileInfo && (fileInfo.textContent = response.file_info);

        const previewLink = _this.element.querySelector(_this._opts.link);
        previewLink && (previewLink.href = response.url);

        _this.trigger('upload:complete');
    }).on('cancel', function(id) {
        _this.trigger('upload:cancel', [id]);
    }).on('error', function(id, reason) {
        _this.trigger('upload:error', [reason]);
    }).on('all_complete', function() {
        _this.loading = false;
    });
};

/**
 * Отправка формы редактирования файла.
 * @param $dialog
 * @private
 */
FileWidget.prototype._change = function($dialog) {
    if (isNaN(this.instanceId)) {
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
        if (response.error) {
            const error = new Error(response.error);
            error.response = response;
            throw error
        }

        preloader.hide();
        formUtils.cleanFormErrors($form.get(0));
        if (response.form_errors) {
            formUtils.addFormErrorsFromJSON($form.get(0), response.form_errors);
        } else {
            $dialog.modal('hide');

            const fileName = _this.element.querySelector('.file-name');
            fileName && (fileName.textContent = response.name);

            const fileInfo = _this.element.querySelector('.file-info');
            fileInfo && (fileInfo.textContent = response.file_info);

            const previewLink = _this.element.querySelector(_this._opts.link);
            previewLink && (previewLink.href = response.url);
        }
    }).catch(function(error) {
        preloader.hide();
        _this.trigger('upload:error', [null, error]);
    });
};

/**
 * Удаление файла.
 * @private
 */
FileWidget.prototype._delete = function() {
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
        if (response.error) {
            const error = new Error(response.error);
            error.response = response;
            throw error
        }

        _this.empty = true;
        _this.instanceId = '';

        const fileName = _this.element.querySelector('.file-name');
        fileName && (fileName.textContent = '');

        const fileInfo = _this.element.querySelector('.file-info');
        fileInfo && (fileInfo.textContent = '');

        _this.trigger('upload:deleted');
    }).catch(function(error) {
        _this.trigger('upload:error', [null, error]);
    });
};

FileWidget.prototype.addListeners = function() {
    const _this = this;

    // удаление файла
    this.deleteButton.addEventListener('click', function(event) {
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
                        _this._delete();
                    }
                }
            }
        });
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

        Promise.all([
            preloader.show(),
            fetch(`${_this._opts.urls.change}?${queryString}`, {
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
            if (response.error) {
                const error = new Error(response.error);
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
                            _this._change(this);
                            return false;
                        }
                    }
                }
            });

            const $form = $dialog.find('form');
            $form.on('submit', function() {
                _this._change($dialog);
                return false;
            });
        }).catch(function(error) {
            preloader.hide();
            _this.trigger('upload:error', [error]);
        });
    });
};

// ======================================


function initWidget(element) {
    if (element.closest('.empty-form')) {
        return
    }

    new FileWidget(element, {
        urls: {
            upload: element.dataset.uploadUrl,
            change: element.dataset.changeUrl,
            delete: element.dataset.deleteUrl,
        }
    }).on('upload:error', function(reason) {
        bootbox.alert({
            message: reason,
            size: 'small'
        });
    });
}


function initWidgets(root = document.body) {
    let file_selector = '.file-uploader';
    root.matches(file_selector) && initWidget(root);
    root.querySelectorAll(file_selector).forEach(initWidget);
}


whenDomReady(initWidgets);
emitters.dom.on('mutate', initWidgets);
