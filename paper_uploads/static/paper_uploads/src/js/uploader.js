/* global gettext */

import EventEmitter from "wolfy87-eventemitter";
import {Dropzone} from "./dropzone";


/**
 * Обертка над dropzone.js, абстрагирующая от конкретной библиотеки.
 * В случае перехода на другую библиотеку для загрузки файлов, изменения
 * необходимо будет внести только здесь.
 *
 * События:
 *   1. submit
 *      Format: function(file) {}
 *
 *      Вызывается при добавлении файла в очередь.
 *      Происходит до любых проверок на валидность файла.
 *
 *      Чтобы отменить добавление файла в очередь, необходимо вызвать в обработчике
 *      события исключение с текстом ошибки. Ошибка, созданная таким образом
 *      может быть переопределена встроенными проверками (например проверкой
 *      максимального размера файла).
 *
 *   2. submitted
 *      Format: function(file) {}
 *
 *      Вызывается когда файл успешно добавлен в очередь. Подразумевается, что
 *      на этой стадии файл уже проверен, поэтому отменять загрузку на этой стадии
 *      не стоит.
 *
 *   3. upload
 *      Format: function(file, xhr, formData) {}
 *
 *      Вызывается прямо перед отправкой файла на сервер.
 *      Через аргументы xhr и formData можно модифицировать отправляемые данные.
 *
 *   4. progress
 *      Format: function(file, progress, bytesSent) {}
 *
 *      Вызывается при обновлении прогресса отправки файла.
 *      Аргумент progress - это состояние отправки в процентах (0-100).
 *
 *   5. cancel
 *      Format: function(file) {}
 *
 *      Вызывается при отмене загрузки файла. Чтобы вызвался этот метод,
 *      файл должен пройти стадию submitted.
 *
 *   6. complete
 *      Format: function(file, response) {}
 *
 *      Событие успешной загрузки файла.
 *      Загрузка считается успешной, когда сервер ответил статусом 200
 *      и JSON-ответ содержит "success: true".
 *
 *   7. all_complete
 *      Format: function() {}
 *
 *      Вызывается когда очередь файлов обработана.
 *
 *   8. error
 *      Format: function(file, message) {}
 *
 *      Обработчик ошибок загрузки. Вызывается не только при JS-ошибках
 *      во время отправки файла, но и при получении ошибок валидации
 *      от сервера.
 */
class Uploader extends EventEmitter {
    static Defaults = {
        url: null,
        uploadMultiple: false,
        maxFilesize: null,
        chunkSize: 2 * 1024 * 1024,
        params: null,
        headers: null,
        filters: [],  // strings or functions
        autoStart: true,

        root: null,
        button: null,
        dropzone: null,
        dropzoneActiveClassName: "highlighted"
    }

    constructor(options) {
        super();

        this.config = {
            ...this.constructor.Defaults,
            ...options
        };

        if (!this.config.url) {
            throw new Error("No URL provided.");
        }

        if (!this.config.root) {
            throw new Error("Root element required.");
        }

        this.init();
    }

    get instance() {
        return this._instance;
    }

    init() {
        if (this._instance) {
            throw new Error("FileUploader is already initialized.");
        }

        const options = this._getPluginOptions(this.config.root);
        this._instance = new Dropzone(this.config.dropzone, options);

        // store instance
        this.config.root.uploader = this;
    }

    destroy() {
        if (this._instance) {
            this._instance.destroy();
            this._instance = null;
        }

        this.config.root.uploader = null;
    }

    getUUID(file) {
        return file.upload.uuid;
    }

    cancel(file) {
        if (typeof file === "string") {
            let uuid = file;
            let files = this.instance.files.filter((file) => {
                return file.upload.uuid === uuid
            });

            if (files.length) {
                file = files[0];
            } else {
                console.warn(`Not found file with UUID: ${uuid}`);
                return;
            }
        }

        this.instance.removeFile(file);
    }

    cancelAll() {
        this.instance.removeAllFiles(true);
    }

    _getPluginOptions(root) {
        let headers = {};
        if (typeof this.config.headers === "function") {
            headers = Object.assign(headers, this.config.headers(root));
        } else if (typeof this.config.headers === "object") {
            headers = Object.assign(headers, this.config.headers);
        } else {
            throw new Error("Unsupported 'headers' type.");
        }

        let params = {};
        if (typeof this.config.params === "function") {
            // функция будет вызываться при каждой загрузке
        } else if (typeof this.config.params === "object") {
            params = Object.assign(params, this.config.params);
        } else {
            throw new Error("Unsupported 'params' type.");
        }

        const acceptedFiles = [];
        const filterFunctions = [];
        for (let item of this.config.filters) {
            if (typeof item === "string") {
                acceptedFiles.push(item);
            } else if (typeof item === "function") {
                filterFunctions.push(item);
            } else {
                throw new Error(`Unsupported filter: ${item}.`);
            }
        }

        const _this = this;
        return {
            url: this.config.url,
            headers: headers,
            uploadMultiple: false,
            maxFiles: this.config.uploadMultiple ? null : 1,
            maxFilesize: this.config.maxFilesize,
            acceptedFiles: (acceptedFiles && acceptedFiles.length) ? acceptedFiles.join(",") : null,

            chunking: true,
            forceChunking: true,
            chunkSize: this.config.chunkSize,
            autoQueue: this.config.autoStart,

            clickable: this.config.button,
            createImageThumbnails: false,
            hiddenInputContainer: root,

            dictMaxFilesExceeded:
                gettext("You can not upload any more files."),
            dictResponseError:
                gettext("Server responded with {{statusCode}} code."),

            params: function(files, xhr, chunk) {
                let finalParams;
                if (typeof this.config.params === "function") {
                    finalParams = Object.assign({}, params, this.config.params(chunk ? chunk.file : null));
                } else {
                    finalParams = params;
                }

                if (chunk) {
                    return Object.assign({
                        paperUUID: chunk.file.upload.uuid,
                        paperChunkIndex: chunk.index,
                        paperTotalChunkCount: chunk.file.upload.totalChunkCount,
                    }, finalParams);
                } else {
                    return finalParams
                }
            }.bind(this),

            dragenter() {
                _this.config.dropzone && _this.config.dropzone.classList.add(_this.config.dropzoneActiveClassName);
            },

            dragleave(event) {
                if (_this.config.dropzone && !_this.config.dropzone.contains(event.relatedTarget)) {
                    _this.config.dropzone && _this.config.dropzone.classList.remove(_this.config.dropzoneActiveClassName);
                }
            },

            drop() {
                _this.config.dropzone && _this.config.dropzone.classList.remove(_this.config.dropzoneActiveClassName);
            },

            accept(file, done) {
                // Предотвращаем вызов события submitted при ошибке валидации,
                // произошедшей внутри submit.
                if (file.accepted === false) {
                    return done(file._errorMessage);
                }

                const promises = [];

                for (let filter of filterFunctions) {
                    const result = filter.call(this, file);
                    if (result === false) {
                        return done(gettext("File validation failed."));
                    } else if (typeof result === "string") {
                        return done(result);
                    } else if (typeof result.then === "function") {
                        // Promise
                        promises.push(result);
                    }
                }

                if (!promises.length) {
                    _this.trigger("submitted", [file]);
                    done();
                } else {
                    Promise.all(
                        promises
                    ).then(function() {
                        _this.trigger("submitted", [file]);
                        done();
                    }).catch(function(reason) {
                        done(reason || gettext("Unsupported file"));
                    });
                }
            },

            // Called when a file is added to the queue
            addedfile: function(file) {
                try {
                    _this.trigger("submit", [file]);
                } catch (e) {
                    file.accepted = false;
                    file._errorMessage = e.message;
                }
            },

            // Called whenever a file is removed.
            removedfile() {
                return this._updateMaxFilesReachedClass();
            },

            // Called when a file gets processed. Since there is a cue, not all added
            // files are processed immediately.
            processing(file) {

            },

            // Called just before each file is sent.
            sending(file, xhr, formData) {
                _this.trigger("upload", [file, xhr, formData]);
            },

            // Called whenever the upload progress gets updated.
            uploadprogress(file, progress, bytesSent) {
                _this.trigger("progress", [file, progress, bytesSent]);
            },

            // When the upload is canceled.
            canceled(file) {
                _this.trigger("cancel", [file]);
            },

            // When the complete upload is finished and successful
            success(file, response) {
                if (response.errors && response.errors.length) {
                    _this.trigger("error", [file, response.errors]);
                } else {
                    _this.trigger("complete", [file, response]);
                }
            },

            // Called whenever an error occurs
            error(file, message) {
                _this.trigger("error", [file, [message]]);
            },

            // When the upload is finished, either with success or an error.
            complete(file) {
                if (this.files.indexOf(file) >= 0) {
                    this.removeFile(file);
                }
            },

            reset() {
                _this.trigger("all_complete", []);
            }
        }
    }
}

export {
    Uploader
}
