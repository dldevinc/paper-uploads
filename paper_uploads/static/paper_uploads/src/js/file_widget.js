/* global gettext */

import EventEmitter from "wolfy87-eventemitter";
import {Uploader} from "./uploader";
import * as utils from "./utils";

// PaperAdmin API
const Widget = window.paperAdmin.Widget;
const modals = window.paperAdmin.modals;
const formUtils = window.paperAdmin.formUtils;

// CSS
import "css/file_widget.scss";


class FileUploader extends EventEmitter {
    static Defaults = {
        input: ".file-uploader__input",
        dropzone: ".dropzone__overlay",
        dropzoneActiveClassName: "dropzone__overlay--highlighted",
        progressBar: ".progress-bar",
        fileName: ".file-name",
        fileInfo: ".file-info",

        uploadButton: ".file-uploader__upload-button",
        cancelButton: ".file-uploader__cancel-button",
        viewButton: ".file-uploader__view-button",
        changeButton: ".file-uploader__change-button",
        deleteButton: ".file-uploader__delete-button",
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

    get empty() {
        return this.root.classList.contains("empty");
    }

    set empty(value) {
        this.root.classList.toggle("empty", value);
    }

    get loading() {
        return this.root.classList.contains("loading");
    }

    set loading(value) {
        this.root.classList.toggle("loading", value);
    }

    get processing() {
        return this.root.classList.contains("processing");
    }

    set processing(value) {
        this.root.classList.toggle("processing", value);
    }

    init() {
        this.empty = !Boolean(this.instanceId);

        // store instance
        this.root.fileUploader = this;

        this._createUploader();
        this._addListeners();
    }

    destroy() {
        if (this.uploader) {
            this.uploader.destroy();
        }

        this.root.fileUploader = null;
    }

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

    _addListeners() {
        const _this = this;

        this.uploader.on("submitted", function() {
            if (!this.loading) {
                this.loading = true;

                const progressBar = this.progressBar;
                progressBar && (progressBar.style.width = "0%");
            }
        }.bind(this));

        this.uploader.on("progress", function(file, percentage) {
            const progressBar = this.progressBar;
            progressBar && (progressBar.style.width = percentage + "%");

            this.showCollectedErrors();

            if (percentage >= 100) {
                this.loading = false;
                this.processing = true;

                // Добавление минимальной задержки для стадии processing,
                // чтобы переход от стадии loading к finished был более плавным.
                this.processingPromise = new Promise(function(resolve) {
                    setTimeout(() => {resolve()}, 600);
                });
            }
        }.bind(this));

        this.uploader.on("complete", function(file, response) {
            const onComplete = function() {
                this.processing = false;
                this.empty = false;
                this.instanceId = response.id;

                const fileName = this.root.querySelector(this.config.fileName);
                fileName && (fileName.textContent = response.name);

                const fileInfo = this.root.querySelector(this.config.fileInfo);
                fileInfo && (fileInfo.textContent = response.file_info);

                const previewLink = this.root.querySelector(this.config.viewButton);
                previewLink && (previewLink.href = response.url);
            }.bind(this);

            if (this.processingPromise) {
                this.processingPromise.then(function() {
                    this.processingPromise = null;
                    onComplete();
                }.bind(this));
            } else {
                // Сюда попадать не должны, но на всякий случай...
                console.warn("processingPromise undefined");
                onComplete();
            }
        }.bind(this));

        this.uploader.on("error", function(file, message) {
            this.collectError(message);
        }.bind(this));

        this.uploader.on("all_complete", function() {
            const onAllComplete = function() {
                this.processing = false;

                const progressBar = this.progressBar;
                progressBar && (progressBar.style.width = "");

                this.showCollectedErrors();
            }.bind(this);

            if (this.processingPromise) {
                this.processingPromise.then(function() {
                    this.processingPromise = null;
                    onAllComplete();
                }.bind(this));
            } else {
                onAllComplete();
            }
        }.bind(this));

        // отмена загрузки
        if (this.config.cancelButton) {
            this.root.addEventListener("click", function(event) {
                const cancelButton = event.target.closest(this.config.cancelButton);
                if (cancelButton) {
                    event.preventDefault();

                    this.uploader.cancelAll();
                    this.loading = false;
                    this.processing = false;
                }
            }.bind(this));
        }

        // удаление файла
        if (this.config.deleteButton) {
            this.root.addEventListener("click", function(event) {
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
                            onClick: function(event, popup) {
                                popup.destroy();
                            }
                        }, {
                            autofocus: true,
                            label: gettext("Delete"),
                            buttonClass: "btn-danger",
                            onClick: function(event, popup) {
                                Promise.all([
                                    popup.destroy(),
                                    _this.deleteFile()
                                ]).catch(function(reason) {
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
            }.bind(this));
        }

        // изменение файла
        if (this.config.changeButton) {
            this.root.addEventListener("click", function(event) {
                const changeButton = event.target.closest(this.config.changeButton);
                if (changeButton) {
                    event.preventDefault();

                    // Препятствуем открытию нескольких окон
                    changeButton.disabled = true;

                    this.fetchChangeForm(
                        //
                    ).then(function(response) {
                        if (response.errors && response.errors.length) {
                            throw response.errors;
                        }

                        modals.createModal({
                            title: gettext("Edit file"),
                            body: response.form,
                            buttons: [{
                                label: gettext("Cancel"),
                                buttonClass: "btn-light",
                                onClick: function(event, popup) {
                                    popup.destroy();
                                }
                            }, {
                                label: gettext("Save"),
                                buttonClass: "btn-success",
                                onClick: function(event, popup) {
                                    _this.sendChangeForm(popup);
                                }
                            }],
                            onInit: function() {
                                const popup = this;
                                const form = popup._body.querySelector("form");
                                form && form.addEventListener("submit", function(event) {
                                    event.preventDefault();
                                    _this.sendChangeForm(popup);
                                });

                                popup.show();

                                // autofocus first field
                                $(popup._element).on("autofocus.bs.modal", function() {
                                    const firstWidget = popup._body.querySelector(".paper-widget");
                                    const firstField = firstWidget && firstWidget.querySelector("input, select, textarea");
                                    firstField && firstField.focus();
                                });
                            },
                            onDestroy: function() {
                                changeButton.disabled = false;
                            }
                        });
                    }).catch(function(reason) {
                        if (reason instanceof Error) {
                            // JS-ошибки дублируем в консоль
                            console.error(reason);
                        }
                        modals.showErrors(reason);
                    });
                }
            }.bind(this));
        }
    }

    collectError(message) {
        const errorKey = `file_${this.input.name}`;
        utils.collectError(errorKey, message);
    }

    showCollectedErrors() {
        const errorKey = `file_${this.input.name}`;
        utils.showCollectedErrors(errorKey);
    }

    /**
     * Удаление файла.
     * @returns {Promise}
     */
    deleteFile() {
        if (!this.instanceId) {
            return Promise.reject("Instance doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(function(name) {
            formData.append(name, params[name]);
        });
        formData.append("pk", this.instanceId);

        const _this = this;
        return modals.showSmartPreloader(
            fetch(this.root.dataset.deleteUrl, {
                method: "POST",
                credentials: "same-origin",
                body: formData
            }).then(function(response) {
                if (!response.ok) {
                    throw `${response.status} ${response.statusText}`;
                }
                return response.json();
            })
        ).then(function(response) {
            if (response.errors && response.errors.length) {
                throw response.errors;
            }

            _this.empty = true;
            _this.instanceId = "";

            const fileName = _this.root.querySelector(_this.config.fileName);
            fileName && (fileName.textContent = "");

            const fileInfo = _this.root.querySelector(_this.config.fileInfo);
            fileInfo && (fileInfo.textContent = "");
        });
    }

    /**
     * Получение с сервера формы изменения файла.
     * @returns {Promise}
     */
    fetchChangeForm() {
        if (!this.instanceId) {
            return Promise.reject("Instance doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(function(name) {
            formData.append(name, params[name]);
        });
        formData.append("pk", this.instanceId);

        const queryString = new URLSearchParams(formData).toString();

        return modals.showSmartPreloader(
            fetch(`${this.root.dataset.changeUrl}?${queryString}`, {
                credentials: "same-origin",
            }).then(function(response) {
                if (!response.ok) {
                    throw `${response.status} ${response.statusText}`;
                }
                return response.json();
            })
        )
    }

    /**
     * Отправка формы редактирования файла.
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

        const _this = this;
        return modals.showSmartPreloader(
            fetch(form.action, {
                method: "POST",
                credentials: "same-origin",
                body: formData
            }).then(function(response) {
                if (!response.ok) {
                    throw `${response.status} ${response.statusText}`;
                }
                return response.json();
            })
        ).then(function(response) {
            if (response.errors && response.errors.length) {
                throw response.errors;
            }

            formUtils.cleanAllErrors(modal._body);
            if (response.form_errors) {
                formUtils.setErrorsFromJSON(modal._body, response.form_errors);
            } else {
                modal.destroy();

                const fileName = _this.root.querySelector(_this.config.fileName);
                fileName && (fileName.textContent = response.name);

                const fileInfo = _this.root.querySelector(_this.config.fileInfo);
                fileInfo && (fileInfo.textContent = response.file_info);

                const previewLink = _this.root.querySelector(_this.config.viewButton);
                previewLink && (previewLink.href = response.url);
            }
        }).catch(function(reason) {
            if (reason instanceof Error) {
                // JS-ошибки дублируем в консоль
                console.error(reason);
            }
            modals.showErrors(reason);
        });
    }
}


class FileUploaderWidget extends Widget {
    _init(element) {
        new FileUploader(element);
    }

    _destroy(element) {
        if (element.fileUploader) {
            element.fileUploader.destroy();
            element.fileUploader = null;
        }
    }
}


const widget = new FileUploaderWidget();
widget.observe(".file-uploader");
widget.initAll(".file-uploader");
