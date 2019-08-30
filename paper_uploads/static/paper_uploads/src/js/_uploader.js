import {FineUploaderBasic, DragAndDrop} from "fine-uploader";

// PaperAdmin API
const EventEmitter = window.paperAdmin.EventEmitter;


function Uploader(element, options) {
    this._opts = Object.assign({
        url: '',
        multiple: false,
        button: null,
        dropzones: null,
        extraData: null,
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
                if (!_this._opts.multiple) {
                    if (is_loading) {
                        return false;
                    }
                    is_loading = true;
                }

                // пользовательские фильтры для загружаемых файлов
                if (_this._opts.filters && _this._opts.filters.length) {
                    const uploader = this;
                    const file = this.getFile(id);
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
