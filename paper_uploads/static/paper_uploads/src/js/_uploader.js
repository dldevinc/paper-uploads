import {FineUploaderBasic, isFile} from "./fine-uploader/fine-uploader.core";
import {DragAndDrop} from "./fine-uploader/dnd";
import match from 'mime-match';

// PaperAdmin API
const EventEmitter = window.paperAdmin.EventEmitter;


/**
 * Класс ошибки валидации файла при событии onSubmit()
 * @constructor
 */
function ValidationError() {
    Error.apply(this, arguments) ;
    this.name = "ValidationError";
    if (Error.captureStackTrace) {
        Error.captureStackTrace(this, ValidationError);
    } else {
        this.stack = (new Error()).stack;
    }
}

ValidationError.prototype = Object.create(Error.prototype);


/**
 * Класс-обертка над загрузчиком Fine Uploader.
 * @param element
 * @param options
 * @constructor
 */
function Uploader(element, options) {
    this._opts = Object.assign({
        url: '',
        multiple: false,
        maxConnections: 1,
        button: null,
        dropzones: null,
        extraData: null,
        validation: {},
        filters: []
    }, options);

    this.element = element;
    this.uploader = this._makeUploader();
}

Uploader.prototype = Object.create(EventEmitter.prototype);

Uploader.prototype.getParams = function() {
    if (typeof this._opts.extraData === 'function') {
        return Object.assign(getPaperParams(this.element), this._opts.extraData.call(this));
    } else if (typeof this._opts.extraData === 'object') {
        return Object.assign(getPaperParams(this.element), this._opts.extraData);
    } else {
        return getPaperParams(this.element);
    }
};

Uploader.prototype._makeUploader = function() {
    const _this = this;

    // флаг, ограничивающий количество загрузок при multiple=false
    let is_loading = false;

    let uploader = new FineUploaderBasic({
        button: this._opts.button,
        multiple: this._opts.multiple,
        maxConnections: this._opts.maxConnections,
        request: {
            endpoint: this._opts.url,
            params: this.getParams()
        },
        chunking: {
            enabled: true,
            partSize: 2 * 1024 * 1024,
            concurrent: {
                enabled: false
            }
        },
        text: {
            fileInputTitle: ''
        },
        validation: {
            stopOnFirstInvalidFile: false,
            sizeLimit: _this._opts.validation.sizeLimit || 0,
            acceptFiles: _this._opts.validation.acceptFiles || null,
            allowedExtensions: _this._opts.validation.allowedExtensions || []
        },
        messages: {
            typeError: "`{file}` has an invalid extension. Valid extension(s): {extensions}.",
            sizeError: "`{file}` is too large, maximum file size is {sizeLimit}.",
        },
        callbacks: {
            onSubmit: function(id) {
                const uploader = this;
                const file = uploader.getFile(id);

                if (is_loading && !_this._opts.multiple) {
                    return false
                } else {
                    is_loading = true;
                }

                // пользовательские фильтры для загружаемых файлов
                if (_this._opts.filters && _this._opts.filters.length) {
                    for (let index=0; index<_this._opts.filters.length; index++) {
                        const filter = _this._opts.filters[index];
                        try {
                            filter.call(uploader, id, file);
                        } catch (error) {
                            _this.trigger('error', [id, error.message]);
                            return false;
                        }
                    }
                }

                const validationOptions = _this._opts.validation;
                if (isFile(file)) {
                    // check mimetypes
                    const allowedMimeTypes = validationOptions.acceptFiles;
                    if (allowedMimeTypes && allowedMimeTypes.length) {
                        let allowed = false;
                        if (Array.isArray(allowedMimeTypes)) {
                            allowed = allowedMimeTypes.some(function(template) {
                                return match(file.type, template);
                            });
                        } else if (typeof allowedMimeTypes === 'string') {
                            allowed = match(file.type, allowedMimeTypes);
                        }

                        if (!allowed) {
                            const reason = `\`${file.name}\` has an invalid mimetype '${file.type}'`;
                            _this.trigger('error', [id, reason]);
                            return false;
                        }
                    }

                    // check image size
                    if (validationOptions.image) {
                        return new Promise(function(resolve, reject) {
                            const image = new Image();
                            const url = window.URL && window.URL.createObjectURL ? window.URL : window.webkitURL && window.webkitURL.createObjectURL ? window.webkitURL : null;
                            if (url) {
                                image.onerror = function() {
                                    reject("Cannot determine dimensions for an image. May be too large.");
                                };
                                image.onload = function() {
                                    resolve({
                                        width: this.width,
                                        height: this.height
                                    });
                                };
                                image.src = url.createObjectURL(file);
                            } else {
                                reject("No createObjectURL function available to generate image URL!");
                            }
                        }).then(function(size) {
                            if (validationOptions.minImageWidth && (size.width < validationOptions.minImageWidth)) {
                                const reason = `\`${file.name}\` is not wide enough. Minimum width is ${validationOptions.minImageWidth}px`;
                                _this.trigger('error', [id, reason]);
                                throw new Error(reason);
                            }
                            if (validationOptions.minImageHeight && (size.height < validationOptions.minImageHeight)) {
                                const reason = `\`${file.name}\` is not tall enough. Minimum height is ${validationOptions.minImageHeight}px`;
                                _this.trigger('error', [id, reason]);
                                throw new Error(reason);
                            }
                            if (validationOptions.maxImageWidth && (size.width > validationOptions.maxImageWidth)) {
                                const reason = `\`${file.name}\` is too wide. Maximum width is ${validationOptions.maxImageWidth}px`;
                                _this.trigger('error', [id, reason]);
                                throw new Error(reason);
                            }
                            if (validationOptions.maxImageHeight && (size.height > validationOptions.maxImageHeight)) {
                                const reason = `\`${file.name}\` is too tall. Maximum height is ${validationOptions.maxImageHeight}px`;
                                _this.trigger('error', [id, reason]);
                                throw new Error(reason);
                            }
                        });
                    }
                }

                try {
                    _this.trigger('submit', [id]);
                } catch (e) {
                    if (e.name === 'ValidationError') {
                        return false;
                    } else {
                        throw e;
                    }
                }
            },
            onSubmitted: function(id) {
                _this.trigger('submitted', [id]);
            },
            onUpload: function(id) {
                _this.trigger('upload', [id]);
            },
            onProgress: function(id, name, uploadedBytes, totalBytes) {
                const percentage = Math.ceil(100 * (uploadedBytes / totalBytes));
                _this.trigger('progress', [id, percentage]);
            },
            onCancel: function(id) {
                _this.trigger('cancel', [id]);
            },
            onComplete: function(id, name, response) {
                if (response.success) {
                    _this.trigger('complete', [id, response]);
                }
            },
            onAllComplete: function(succeeded, failed) {
                is_loading = false;
                _this.trigger('all_complete', [succeeded, failed]);
            },
            onError: function(id, name, reason, xhr) {
                let response, messages;
                try {
                    response = JSON.parse(xhr.responseText);
                } catch (error) {

                }

                if (response) {
                    messages = response.errors || response.error || reason;
                } else {
                    messages = reason;
                }

                _this.trigger('error', [id, messages]);
            }
        }
    });

    if (this._opts.dropzones && this._opts.dropzones.length) {
        new DragAndDrop({
            dropZoneElements: this._opts.dropzones,
            allowMultipleItems: this._opts.multiple,
            classes: {
                dropActive: 'dropzone-highlighted'
            },
            callbacks: {
                processingDroppedFilesComplete: function(files) {
                    uploader.addFiles(files);
                }
            }
        });
    }

    return uploader;
};


function getPaperParams(element) {
    const params = {};
    const dataset = element.dataset;
    Object.keys(dataset).forEach(function(name) {
        if (/^paper(?:[^a-z0-9]|$)/.test(name)) {
            params[name] = dataset[name];
        }
    });
    return params;
}


export {Uploader, ValidationError, getPaperParams};
