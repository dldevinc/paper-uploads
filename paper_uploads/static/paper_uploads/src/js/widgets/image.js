/* global gettext */

import EventEmitter from "wolfy87-eventemitter";
import {Uploader} from "../uploader.js";
import * as utils from "../utils.js";

// PaperAdmin API
const Widget = window.paperAdmin.Widget;
const modals = window.paperAdmin.modals;
const formUtils = window.paperAdmin.formUtils;

// CSS
import "css/image_widget.scss";


class ImageUploader extends EventEmitter {
    static Defaults = {
        input: ".image-uploader__input",
        dropzone: ".dropzone__overlay",
        dropzoneActiveClassName: "dropzone__overlay--highlighted",
        progressBar: ".progress-bar",
        fileName: ".file-name",
        fileInfo: ".file-info",

        uploadButton: ".image-uploader__upload-button",
        cancelButton: ".image-uploader__cancel-button",
        viewButton: ".image-uploader__view-button",
        changeButton: ".image-uploader__change-button",
        deleteButton: ".image-uploader__delete-button",
    }

    static STATUS = {
        EMPTY: "empty",
        LOADING: "loading",
        PROCESSING: "processing",
        READY: "ready"
    }

    static CSS = {
        container: "image-uploader",
    }

    constructor(root, options) {
        super();

        this.config = {
            ...this.constructor.Defaults,
            ...options
        };

        this.root = root;
        if (!this.root) {
            throw new Error("Root element required.");
        }

        this.init();
    }

    get STATUS() {
        return this.constructor.STATUS;
    }

    get CSS() {
        return this.constructor.CSS;
    }

    get uploader() {
        return this.root.uploader;
    }

    get input() {
        return this.root.querySelector(this.config.input);
    }

    get progressBar() {
        return this.root.querySelector(this.config.progressBar);
    }

    get instanceId() {
        return this.input.value;
    }

    set instanceId(value) {
        this.input.value = value;
    }

    /**
     * Public methods
     */

    init() {
        // store instance
        this.root.imageUploader = this;

        this._createUploader();
        this._addListeners();
    }

    destroy() {
        if (this.uploader) {
            this.uploader.destroy();
        }

        this.root.imageUploader = null;
    }

    /**
     * @returns {string}
     */
    getStatus() {
        return Object.values(this.STATUS).find(value => {
            return this.root.classList.contains(`${this.CSS.container}--${value}`)
        });
    }

    /**
     * @param {string} status
     */
    setStatus(status) {
        Object.values(this.STATUS).forEach(value => {
            this.root.classList.toggle(
                `${this.CSS.container}--${value}`,
                status === value
            );
        });
    }

    /**
     * @param {String|String[]} message
     */
    collectError(message) {
        const errorKey = `image_${this.input.name}`;
        utils.collectError(errorKey, message);
    }

    showCollectedErrors() {
        const errorKey = `image_${this.input.name}`;
        utils.showCollectedErrors(errorKey);
    }

    /**
     * Удаление файла.
     *
     * @returns {Promise}
     */
    deleteFile() {
        if (!this.instanceId) {
            return Promise.reject("Instance doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(name => {
            formData.append(name, params[name]);
        });
        formData.append("pk", this.instanceId);

        return modals.showSmartPreloader(
            fetch(this.root.dataset.deleteUrl, {
                method: "POST",
                credentials: "same-origin",
                body: formData
            }).then(response => {
                if (!response.ok) {
                    throw `${response.status} ${response.statusText}`;
                }
                return response.json();
            })
        ).then(response => {
            if (response.errors && response.errors.length) {
                throw response.errors;
            }

            this.setStatus(this.STATUS.EMPTY);

            this._disposeFile(response);
        });
    }

    /**
     * Получение с сервера формы изменения файла.
     *
     * @returns {Promise}
     */
    fetchChangeForm() {
        if (!this.instanceId) {
            return Promise.reject("Instance doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(name => {
            formData.append(name, params[name]);
        });
        formData.append("pk", this.instanceId);

        const queryString = new URLSearchParams(formData).toString();

        return modals.showSmartPreloader(
            fetch(`${this.root.dataset.changeUrl}?${queryString}`, {
                credentials: "same-origin",
            }).then(response => {
                if (!response.ok) {
                    throw `${response.status} ${response.statusText}`;
                }
                return response.json();
            })
        )
    }

    /**
     * Отправка формы редактирования файла.
     *
     * @param {PaperModal} modal
     * @returns {Promise}
     */
    sendChangeForm(modal) {
        if (!this.instanceId) {
            return Promise.reject("Instance doesn't exist");
        }

        const form = modal._body.querySelector("form");
        if (!form) {
            return Promise.reject("Form not found");
        }

        const formData = new FormData(form);

        return modals.showSmartPreloader(
            fetch(form.action, {
                method: "POST",
                credentials: "same-origin",
                body: formData
            }).then(response => {
                if (!response.ok) {
                    throw `${response.status} ${response.statusText}`;
                }
                return response.json();
            })
        ).then(response => {
            if (response.errors && response.errors.length) {
                throw response.errors;
            }

            formUtils.cleanAllErrors(modal._body);
            if (response.form_errors) {
                formUtils.setErrorsFromJSON(modal._body, response.form_errors);
            } else {
                modal.destroy();

                this._updateFile(response);
            }
        }).catch(reason => {
            if (reason instanceof Error) {
                // JS-ошибки дублируем в консоль
                console.error(reason);
            }
            modals.showErrors(reason);
        });
    }

    /**
     * Private methods
     */

    /**
     * @private
     */
    _createUploader() {
        const options = Object.assign({
            url: this.root.dataset.uploadUrl,
            params: utils.getPaperParams(this.root),

            root: this.root,
            button: this.root.querySelector(this.config.uploadButton),
            dropzone: this.root.querySelector(this.config.dropzone),
            dropzoneActiveClassName: this.config.dropzoneActiveClassName
        }, utils.processConfiguration(this.root.dataset.configuration));

        new Uploader(options);
    }

    /**
     * @private
     */
    _addListeners() {
        const _this = this;

        this.uploader.on("submitted", () => {
            const status = this.getStatus();
            if (status !== this.STATUS.LOADING) {
                this.setStatus(this.STATUS.LOADING);

                const progressBar = this.progressBar;
                progressBar && (progressBar.style.width = "0%");
            }
        });

        this.uploader.on("progress", (file, percentage) => {
            const progressBar = this.progressBar;
            progressBar && (progressBar.style.width = percentage + "%");

            this.showCollectedErrors();

            if (percentage >= 100) {
                this.setStatus(this.STATUS.PROCESSING);

                // Добавление минимальной задержки для стадии processing,
                // чтобы переход от стадии loading к finished был более плавным.
                this.processingPromise = new Promise(resolve => {
                    setTimeout(() => {resolve()}, 600);
                });
            }
        });

        this.uploader.on("complete", (file, response) => {
            if (this.processingPromise) {
                this.processingPromise.then(() => {
                    this.processingPromise = null;
                    this._fillFile(response);
                });
            } else {
                // Сюда попадать не должны, но на всякий случай...
                console.warn("processingPromise undefined");
                this._fillFile(response);
            }
        });

        this.uploader.on("error", (file, message) => {
            this.collectError(message);
        });

        this.uploader.on("all_complete", () => {
            const onAllComplete = () => {
                if (this.instanceId) {
                    this.setStatus(this.STATUS.READY);
                } else {
                    this.setStatus(this.STATUS.EMPTY);
                }

                const progressBar = this.progressBar;
                progressBar && (progressBar.style.width = "");

                this.showCollectedErrors();
            };

            if (this.processingPromise) {
                this.processingPromise.then(() => {
                    this.processingPromise = null;
                    onAllComplete();
                });
            } else {
                onAllComplete();
            }
        });

        // отмена загрузки
        if (this.config.cancelButton) {
            this.root.addEventListener("click", event => {
                const cancelButton = event.target.closest(this.config.cancelButton);
                if (cancelButton) {
                    event.preventDefault();

                    this.uploader.cancelAll();

                    if (this.instanceId) {
                        this.setStatus(this.STATUS.READY);
                    } else {
                        this.setStatus(this.STATUS.EMPTY);
                    }
                }
            });
        }

        // удаление файла
        if (this.config.deleteButton) {
            this.root.addEventListener("click", event => {
                const deleteButton = event.target.closest(this.config.deleteButton);
                if (deleteButton) {
                    event.preventDefault();

                    // Препятствуем открытию нескольких окон
                    deleteButton.disabled = true;

                    modals.createModal({
                        modalClass: "paper-modal--warning fade",
                        title: gettext("Confirm deletion"),
                        body: gettext("Are you sure you want to <b>DELETE</b> this file?"),
                        buttons: [{
                            label: gettext("Cancel"),
                            buttonClass: "btn-light",
                            onClick: (event, popup) => {
                                popup.destroy();
                            }
                        }, {
                            autofocus: true,
                            label: gettext("Delete"),
                            buttonClass: "btn-danger",
                            onClick: (event, popup) => {
                                Promise.all([
                                    popup.destroy(),
                                    this.deleteFile()
                                ]).catch(reason => {
                                    if (reason instanceof Error) {
                                        // JS-ошибки дублируем в консоль
                                        console.error(reason);
                                    }
                                    modals.showErrors(reason);
                                });
                            }
                        }],
                        onInit: function() {
                            this.show();
                        },
                        onDestroy: function() {
                            deleteButton.disabled = false;
                        }
                    });
                }
            });
        }

        // изменение файла
        if (this.config.changeButton) {
            this.root.addEventListener("click", event => {
                const changeButton = event.target.closest(this.config.changeButton);
                if (changeButton) {
                    event.preventDefault();

                    // Препятствуем открытию нескольких окон
                    changeButton.disabled = true;

                    this.fetchChangeForm(
                        //
                    ).then(response => {
                        if (response.errors && response.errors.length) {
                            throw response.errors;
                        }

                        modals.createModal({
                            title: gettext("Edit image"),
                            body: response.form,
                            buttons: [{
                                label: gettext("Cancel"),
                                buttonClass: "btn-light",
                                onClick: (event, popup) => {
                                    popup.destroy();
                                }
                            }, {
                                label: gettext("Save"),
                                buttonClass: "btn-success",
                                onClick: (event, popup) => {
                                    this.sendChangeForm(popup);
                                }
                            }],
                            onInit: function() {
                                const popup = this;
                                const form = popup._body.querySelector("form");
                                form && form.addEventListener("submit", event => {
                                    event.preventDefault();
                                    _this.sendChangeForm(popup);
                                });

                                popup.show();

                                // autofocus first field
                                $(popup._element).on("autofocus.bs.modal", () => {
                                    const firstWidget = popup._body.querySelector(".paper-widget");
                                    const firstField = firstWidget && firstWidget.querySelector("input, select, textarea");
                                    firstField && firstField.focus();
                                });
                            },
                            onDestroy: function() {
                                changeButton.disabled = false;
                            }
                        });
                    }).catch(reason => {
                        if (reason instanceof Error) {
                            // JS-ошибки дублируем в консоль
                            console.error(reason);
                        }
                        modals.showErrors(reason);
                    });
                }
            });
        }
    }

    /**
     * @param {object<string,*>} response
     * @private
     */
    _fillFile(response) {
        this.instanceId = response.id;

        const fileName = this.root.querySelector(this.config.fileName);
        fileName && (fileName.textContent = response.name);

        const fileInfo = this.root.querySelector(this.config.fileInfo);
        fileInfo && (fileInfo.textContent = response.file_info);

        const previewLink = this.root.querySelector(this.config.viewButton);
        previewLink && (previewLink.href = response.url);
    }

    /**
     * @param {object<string,*>} response
     * @private
     */
    _updateFile(response) {
        const fileName = this.root.querySelector(this.config.fileName);
        fileName && (fileName.textContent = response.name);

        const fileInfo = this.root.querySelector(this.config.fileInfo);
        fileInfo && (fileInfo.textContent = response.file_info);

        const previewLink = this.root.querySelector(this.config.viewButton);
        previewLink && (previewLink.href = response.url);
    }

    /**
     * @param {object<string,*>} response
     * @private
     */
    _disposeFile(response) {
        this.instanceId = "";

        const fileName = this.root.querySelector(this.config.fileName);
        fileName && (fileName.textContent = "");

        const fileInfo = this.root.querySelector(this.config.fileInfo);
        fileInfo && (fileInfo.textContent = "");
    }
}


class ImageUploaderWidget extends Widget {
    _init(element) {
        new ImageUploader(element);
    }

    _destroy(element) {
        if (element.imageUploader) {
            element.imageUploader.destroy();
        }
    }
}


export {
    ImageUploader,
    ImageUploaderWidget
}
