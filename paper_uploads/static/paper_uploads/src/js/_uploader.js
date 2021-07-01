import match from 'mime-match';
import EventEmitter from "wolfy87-eventemitter";
import {FineUploaderBasic, isFile} from "./fine-uploader/fine-uploader.core";
import {DragAndDrop} from "./fine-uploader/dnd";
import {ValidationError} from "./_exceptions";
import {getPaperParams} from "./_utils";


/**
 * Класс-обертка над загрузчиком Fine Uploader.
 * @param element
 * @param options
 * @constructor
 */
function Uploader(element, options) {
    this._opts = Object.assign({
        url: "",
        multiple: false,
        maxConnections: 1,
        button: null,
        dropzones: null,
        params: null,
        configuration: {}
    }, options);

    this.element = element;
    this.uploader = this._makeUploader();
}

Uploader.prototype = Object.create(EventEmitter.prototype);

Uploader.prototype.getParams = function(id) {
    if (typeof this._opts.params === "function") {
        return Object.assign(getPaperParams(this.element), this._opts.params.call(this, id));
    } else if (typeof this._opts.params === "object") {
        return Object.assign(getPaperParams(this.element), this._opts.params);
    } else {
        return getPaperParams(this.element);
    }
};

Uploader.prototype.formatParams = function(params, id) {
    const plain_params = {};
    for (let [key, value] of Object.entries(params)) {
        if (typeof value === "function") {
            plain_params[key] = value(id);
        } else {
            plain_params[key] = value;
        }
    }
    return plain_params;
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
            endpoint: this._opts.url
        },
        chunking: {
            enabled: true,
            partSize: 2 * 1024 * 1024,
            concurrent: {
                enabled: false
            }
        },
        text: {
            fileInputTitle: ""
        },
        validation: {
            stopOnFirstInvalidFile: false,
            acceptFiles: _this._opts.configuration.acceptFiles || null,
            sizeLimit: _this._opts.configuration.sizeLimit || 0,
            allowedExtensions: _this._opts.configuration.allowedExtensions || []
        },
        messages: {
            typeError: "File <b>`{file}`</b> has an invalid extension. Valid extension(s): {extensions}.",
            sizeError: "File <b>`{file}`</b> is too large, maximum file size is {sizeLimit}.",
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

                const configuration = _this._opts.configuration;
                if (isFile(file)) {
                    // check mimetypes
                    const allowedMimeTypes = configuration.accept;
                    if (allowedMimeTypes && allowedMimeTypes.length) {
                        let allowed = false;
                        if (Array.isArray(allowedMimeTypes)) {
                            allowed = allowedMimeTypes.some(function(template) {
                                return match(file.type, template);
                            });
                        } else if (typeof allowedMimeTypes === "string") {
                            allowed = match(file.type, allowedMimeTypes);
                        }

                        if (!allowed) {
                            const reason = `File <b>\`${file.name}\`</b> has an invalid mimetype '${file.type}'`;
                            _this.trigger("error", [id, reason]);
                            return false;
                        }
                    }

                    // check image size
                    if (configuration.strictImageValidation) {
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
                            if (configuration.minImageWidth && (size.width < configuration.minImageWidth)) {
                                const reason = `File <b>\`${file.name}\`</b> is not wide enough. Minimum width is ${configuration.minImageWidth}px`;
                                _this.trigger("error", [id, reason]);
                                throw new Error(reason);
                            }
                            if (configuration.minImageHeight && (size.height < configuration.minImageHeight)) {
                                const reason = `File <b>\`${file.name}\`</b> is not tall enough. Minimum height is ${configuration.minImageHeight}px`;
                                _this.trigger("error", [id, reason]);
                                throw new Error(reason);
                            }
                            if (configuration.maxImageWidth && (size.width > configuration.maxImageWidth)) {
                                const reason = `File <b>\`${file.name}\`</b> is too wide. Maximum width is ${configuration.maxImageWidth}px`;
                                _this.trigger("error", [id, reason]);
                                throw new Error(reason);
                            }
                            if (configuration.maxImageHeight && (size.height > configuration.maxImageHeight)) {
                                const reason = `File <b>\`${file.name}\`</b> is too tall. Maximum height is ${configuration.maxImageHeight}px`;
                                _this.trigger("error", [id, reason]);
                                throw new Error(reason);
                            }
                        });
                    }
                }

                try {
                    _this.trigger("submit", [id]);
                } catch (e) {
                    if (e instanceof ValidationError) {
                        return false;
                    } else {
                        throw e;
                    }
                }
            },
            onSubmitted: function(id) {
                _this.trigger("submitted", [id]);
                let params = _this.getParams(id);
                if (params) {
                    params = _this.formatParams(params, id);
                    this.setParams(params, id);
                }
            },
            onUpload: function(id) {
                _this.trigger("upload", [id]);
            },
            onProgress: function(id, name, uploadedBytes, totalBytes) {
                const percentage = Math.ceil(100 * (uploadedBytes / totalBytes));
                _this.trigger("progress", [id, percentage]);
            },
            onCancel: function(id) {
                _this.trigger("cancel", [id]);
            },
            onComplete: function(id, name, response) {
                if (response.success) {
                    _this.trigger("complete", [id, response]);
                }
            },
            onAllComplete: function(succeeded, failed) {
                is_loading = false;
                _this.trigger("all_complete", [succeeded, failed]);
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

                _this.trigger("error", [id, messages]);
            }
        }
    });

    if (this._opts.dropzones && this._opts.dropzones.length) {
        new DragAndDrop({
            dropZoneElements: this._opts.dropzones,
            allowMultipleItems: this._opts.multiple,
            classes: {
                dropActive: "dropzone__overlay--highlighted"
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

export {
    Uploader
};
