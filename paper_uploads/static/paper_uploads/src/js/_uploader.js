import {FineUploaderBasic, DragAndDrop, isFile} from "fine-uploader";

// PaperAdmin API
const EventEmitter = window.paperAdmin.EventEmitter;


function Uploader(element, options) {
    this._opts = Object.assign({
        url: '',
        multiple: false,
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
        maxConnections: 1,
        request: {
            endpoint: this._opts.url,
            params: this.getParams()
        },
        chunking: {
            enabled: true,
            partSize: 1024 * 1024
        },
        text: {
            fileInputTitle: 'Select file'
        },
        callbacks: {
            onSubmit: function(id) {
                const uploader = this;
                const file = uploader.getFile(id);

                if (!_this._opts.multiple) {
                    if (is_loading) {
                        return false;
                    }
                    is_loading = true;
                }

                // пользовательские фильтры для загружаемых файлов
                if (_this._opts.filters && _this._opts.filters.length) {
                    for (let index=0; index<_this._opts.filters.length; index++) {
                        const filter = _this._opts.filters[index];
                        try {
                            filter.call(uploader, id, file);
                        } catch (error) {
                            _this.trigger('reject', [id, file, error.message]);
                            return false;
                        }
                    }
                }

                // ручная проверка файлов, т.к. встроенная валидация вызывает onError
                // без кода ошибки. Отличить одну ошибку от другой не представляется
                // возможным. Но это необходимо для вызова reject.
                const validationOptions = _this._opts.validation;
                if (validationOptions) {
                    // check mimetypes
                    if (validationOptions.acceptFiles) {
                        const allowedMimeTypes = validationOptions.acceptFiles;
                        if (Array.isArray(allowedMimeTypes)) {
                            if (allowedMimeTypes.indexOf(file.type) < 0) {
                                const reason = `Unsupported MIME type: ${file.type}`;
                                _this.trigger('reject', [id, file, reason]);
                                return false;
                            }
                        } else if (typeof allowedMimeTypes === 'string') {
                            if (file.type !== allowedMimeTypes) {
                                const reason = `Unsupported MIME type: ${file.type}`;
                                _this.trigger('reject', [id, file, reason]);
                                return false;
                            }
                        }
                    }

                    // check min size
                    if (validationOptions.minSizeLimit && (file.size < validationOptions.minSizeLimit)) {
                        const sizeLimit = uploader._formatSize(validationOptions.minSizeLimit);
                        const reason = `File is too small. Minimum file size is <strong>${sizeLimit}</strong>`;
                        _this.trigger('reject', [id, file, reason]);
                        return false;
                    }

                    // check max size
                    if (validationOptions.sizeLimit && (file.size > validationOptions.sizeLimit)) {
                        const sizeLimit = uploader._formatSize(validationOptions.sizeLimit);
                        const reason = `File is too large. Maximum file size is <strong>${sizeLimit}</strong>`;
                        _this.trigger('reject', [id, file, reason]);
                        return false;
                    }

                    // check image size
                    if (validationOptions.image && isFile(file)) {
                        return new Promise(function(resolve, reject) {
                            const image = new Image();
                            const url = window.URL && window.URL.createObjectURL ? window.URL : window.webkitURL && window.webkitURL.createObjectURL ? window.webkitURL : null;
                            if (url) {
                                image.onerror = function() {
                                    reject("Cannot determine dimensions for image.  May be too large.");
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
                            if (validationOptions.image.minWidth && (size.width < validationOptions.image.minWidth)) {
                                const reason = `Image is not wide enough. Minimum width is <strong>${validationOptions.image.minWidth}px</strong>`;
                                _this.trigger('reject', [id, file, reason]);
                                throw new Error(reason);
                            }
                            if (validationOptions.image.minHeight && (size.height < validationOptions.image.minHeight)) {
                                const reason = `Image is not tall enough. Minimum height is <strong>${validationOptions.image.minHeight}px</strong>`;
                                _this.trigger('reject', [id, file, reason]);
                                throw new Error(reason);
                            }
                            if (validationOptions.image.maxWidth && (size.width > validationOptions.image.maxWidth)) {
                                const reason = `Image is too wide. Maximum width is <strong>${validationOptions.image.maxWidth}px</strong>`;
                                _this.trigger('reject', [id, file, reason]);
                                throw new Error(reason);
                            }
                            if (validationOptions.image.maxHeight && (size.height > validationOptions.image.maxHeight)) {
                                const reason = `Image is too tall. Maximum height is <strong>${validationOptions.image.maxHeight}px</strong>`;
                                _this.trigger('reject', [id, file, reason]);
                                throw new Error(reason);
                            }
                        });
                    }
                }
            },
            onSubmitted: function(id) {
                _this.trigger('submit', [id]);
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
                if (!_this._opts.multiple) {
                    is_loading = false;
                }
                _this.trigger('all_complete', [succeeded, failed]);
            },
            onError: function(id, name, reason) {
                _this.trigger('error', [id, reason]);
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


export {Uploader, getPaperParams};
