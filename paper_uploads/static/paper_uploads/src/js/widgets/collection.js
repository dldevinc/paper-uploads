/* global gettext */
/* global ngettext */
/* global interpolate */

import allSettled from "promise.allsettled";
import deepmerge from "deepmerge";
import EventEmitter from "wolfy87-eventemitter";
import Mustache from "mustache";
import { Uploader } from "paper-uploader";
import * as utils from "../utils.js";

// PaperAdmin API
const Sortable = window.paperAdmin.Sortable;
const Widget = window.paperAdmin.Widget;
const modals = window.paperAdmin.modals;
const formUtils = window.paperAdmin.formUtils;

// CSS
import "css/collection_widget.scss";

/**
 * Базовый класс элемента коллекции.
 */
class CollectionItemBase extends EventEmitter {
    static Defaults = {};

    static STATUS = {
        REMOVING: "removing"
    };

    static CSS = {
        container: "collection-item"
    };

    constructor(root, collection, options) {
        super();

        this.config = {
            ...this.constructor.Defaults,
            ...options
        };

        this.root = root;
        if (!this.root) {
            throw new Error("Root element required.");
        }

        this.collection = collection;

        this.init();
    }

    get STATUS() {
        return this.constructor.STATUS;
    }

    get CSS() {
        return this.constructor.CSS;
    }

    /**
     * Public methods
     */

    init() {
        // store instance
        this.root.collectionItem = this;

        this._addListeners();
    }

    destroy() {
        this.root.collectionItem = null;
        this.root.remove();
    }

    /**
     * @returns {string}
     */
    getStatus() {
        return Object.values(this.STATUS).find(value => {
            return this.root.classList.contains(`${this.CSS.container}--${value}`);
        });
    }

    /**
     * @param {string} status
     */
    setStatus(status) {
        Object.values(this.STATUS).forEach(value => {
            this.root.classList.toggle(`${this.CSS.container}--${value}`, status === value);
        });
    }

    /**
     * Анимированное удаление DOM-элемента.
     */
    removeDOM() {
        this.setStatus(this.STATUS.REMOVING);

        const animationPromise = new Promise(resolve => {
            this.root.addEventListener("animationend", () => {
                resolve();
            });
        });

        const fallbackPromise = new Promise(resolve => {
            setTimeout(resolve, 600);
        });

        return Promise.race([animationPromise, fallbackPromise]).then(() => {
            this.destroy();
        });
    }

    /**
     * Private methods
     */

    _addListeners() {}
}

/**
 * Элемент-заглушка, представляющая файл, находящийся в очереди на загрузку.
 *
 * События:
 *  1. upload
 *      Format: function(file, xhr, formData) {}
 *
 *      Вызывается прямо перед отправкой файла на сервер.
 *      Через аргументы xhr и formData можно модифицировать отправляемые данные.
 *
 *  2. progress
 *      Format: function(file, progress, bytesSent) {}
 *
 *      Вызывается при обновлении прогресса отправки файла.
 *      Аргумент progress - это состояние отправки в процентах (0-100).
 *
 *  3. cancel
 *      Format: function(file) {}
 *
 *      Вызывается при отмене загрузки файла.
 *
 *  4. complete
 *      Format: function(file, response) {}
 *
 *      Событие успешной загрузки файла.
 *      Загрузка считается успешной, когда сервер ответил статусом 200
 *      и JSON-ответ содержит "success: true".
 *
 *  5. error
 *      Format: function(file, message) {}
 *
 *      Обработчик ошибок загрузки. Вызывается не только при JS-ошибках
 *      во время отправки файла, но и при получении ошибок валидации
 *      от сервера.
 */
class PreloaderItem extends CollectionItemBase {
    static Defaults = Object.assign({}, super.Defaults, {
        progressBar: ".progress-bar",

        cancelUploadButton: ".collection-item__cancel-button"
    });

    static STATUS = Object.assign({}, super.STATUS, {
        PRELOADER: "preloader",
        PROCESSING: "processing"
    });

    get uuid() {
        return this.root.dataset.uuid;
    }

    get progressBar() {
        return this.root.querySelector(this.config.progressBar);
    }

    /**
     * Public methods
     */

    init() {
        super.init();

        this.root.setAttribute("data-uuid", this.uuid);
    }

    /**
     * Отмена загрузки файла.
     */
    cancel() {
        this.collection.uploader.cancel(this.uuid);
    }

    /**
     * Private methods
     */

    _addListeners() {
        super._addListeners();

        this.on("progress", (file, percentage) => {
            const progressBar = this.progressBar;
            progressBar && (progressBar.style.height = percentage + "%");

            if (percentage >= 100) {
                this.setStatus(this.STATUS.PROCESSING);

                // Добавление минимальной задержки для стадии processing,
                // чтобы переход от стадии loading к finished был более плавным.
                this.processingPromise = new Promise(resolve => {
                    setTimeout(() => {
                        resolve();
                    }, 500);
                });
            }
        });

        this.on("error", () => {
            this.removeDOM();
        });

        this.on("complete", (file, response) => {
            const onComplete = response => {
                const itemType = response.type;

                // замена прелоадера перманентным элементом
                const itemHTML = this.collection.createItem(itemType, response);

                this.root.insertAdjacentHTML("afterend", itemHTML);
                const item = this.root.nextElementSibling;

                this.collection.initItem(itemType, item, {
                    file: file
                });

                this.destroy();
            };

            if (this.processingPromise) {
                this.processingPromise.then(() => {
                    this.processingPromise = null;
                    onComplete(response);
                });
            } else {
                // Сюда попадать не должны, но на всякий случай...
                console.warn("processingPromise undefined");
                onComplete(response);
            }
        });

        // отмена загрузки
        if (this.config.cancelUploadButton) {
            this.root.addEventListener("click", event => {
                const cancelUploadButton = event.target.closest(this.config.cancelUploadButton);
                if (cancelUploadButton) {
                    event.preventDefault();
                    this.cancel();
                    this.removeDOM();
                }
            });
        }
    }
}

class PermanentCollectionItemBase extends CollectionItemBase {
    static Defaults = Object.assign({}, super.Defaults, {
        checkbox: ".collection-item__checkbox",

        caption: ".collection-item__caption",
        viewButton: ".collection-item__view-button",
        changeButton: ".collection-item__change-button",
        deleteButton: ".collection-item__delete-button"
    });

    static STATUS = Object.assign({}, super.STATUS, {
        READY: "ready"
    });

    get id() {
        return this.root.dataset.id;
    }

    get itemType() {
        return this.root.dataset.itemType;
    }

    get checkbox() {
        return this.root.querySelector(this.config.checkbox);
    }

    get checked() {
        return this.root.classList.contains("checked");
    }

    set checked(value) {
        this.root.classList.toggle("checked", value);
        this.checkbox.checked = Boolean(value);
    }

    _addListeners() {
        const _this = this;

        super._addListeners();

        // удаление файла
        if (this.config.deleteButton) {
            this.root.addEventListener("click", event => {
                const deleteButton = event.target.closest(this.config.deleteButton);
                if (deleteButton) {
                    event.preventDefault();
                    event.stopPropagation();

                    // Препятствуем открытию нескольких окон
                    deleteButton.disabled = true;

                    modals.createModal({
                        modalClass: "paper-modal--warning fade",
                        title: gettext("Confirm deletion"),
                        body: gettext("Are you sure you want to <b>DELETE</b> this item?"),
                        buttons: [
                            {
                                label: gettext("Cancel"),
                                buttonClass: "btn-light",
                                onClick: (event, popup) => {
                                    popup.destroy();
                                }
                            },
                            {
                                autofocus: true,
                                label: gettext("Delete"),
                                buttonClass: "btn-danger",
                                onClick: (event, popup) => {
                                    Promise.all([popup.destroy(), this.delete()]).catch(reason => {
                                        if (reason instanceof Error) {
                                            // JS-ошибки дублируем в консоль
                                            console.error(reason);
                                        }
                                        modals.showErrors(reason);
                                    });
                                }
                            }
                        ],
                        onInit: function () {
                            this.show();
                        },
                        onDestroy: function () {
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
                    event.stopPropagation();

                    // Препятствуем открытию нескольких окон
                    changeButton.disabled = true;

                    this
                        .fetchChangeForm
                        //
                        ()
                        .then(response => {
                            if (response.errors && response.errors.length) {
                                throw response.errors;
                            }

                            modals.createModal({
                                title: gettext("Edit item"),
                                body: response.form,
                                buttons: [
                                    {
                                        label: gettext("Cancel"),
                                        buttonClass: "btn-light",
                                        onClick: (event, popup) => {
                                            popup.destroy();
                                        }
                                    },
                                    {
                                        label: gettext("Save"),
                                        buttonClass: "btn-success",
                                        onClick: (event, popup) => {
                                            this.sendChangeForm(popup);
                                        }
                                    }
                                ],
                                onInit: function () {
                                    const popup = this;
                                    const form = popup._body.querySelector("form");
                                    form &&
                                        form.addEventListener("submit", event => {
                                            event.preventDefault();
                                            _this.sendChangeForm(popup);
                                        });

                                    popup.show();

                                    // autofocus first field
                                    $(popup._element).on("autofocus.bs.modal", () => {
                                        const firstWidget = popup._body.querySelector(".paper-widget");
                                        const firstField =
                                            firstWidget && firstWidget.querySelector("input, select, textarea");
                                        firstField && firstField.focus();
                                    });
                                },
                                onDestroy: function () {
                                    changeButton.disabled = false;
                                }
                            });
                        })
                        .catch(reason => {
                            if (reason instanceof Error) {
                                // JS-ошибки дублируем в консоль
                                console.error(reason);
                            }
                            modals.showErrors(reason);
                        });
                }
            });
        }

        // просмотр файла
        if (this.config.viewButton) {
            this.root.addEventListener("click", event => {
                const viewButton = event.target.closest(this.config.viewButton);
                if (viewButton) {
                    // отключение выделения при клике с зажатым Ctrl или Shift
                    event.stopPropagation();
                }
            });
        }
    }

    /**
     * Удаление элемента коллекции.
     * @returns {Promise}
     */
    delete() {
        if (!this.collection.instanceId) {
            return Promise.reject("Collection doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.collection.root);
        Object.keys(params).forEach(name => {
            formData.append(name, params[name]);
        });
        formData.append("collectionId", this.collection.instanceId.toString());
        formData.append("itemId", this.id.toString());
        formData.append("itemType", this.itemType.toString());

        return modals
            .showSmartPreloader(
                fetch(this.collection.root.dataset.deleteItemUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    body: formData
                }).then(response => {
                    if (!response.ok) {
                        throw `${response.status} ${response.statusText}`;
                    }
                    return response.json();
                })
            )
            .then(response => {
                if (response.errors && response.errors.length) {
                    throw response.errors;
                }

                this.removeDOM();
            });
    }

    /**
     * Получение с сервера формы изменения файла.
     * @returns {Promise}
     */
    fetchChangeForm() {
        if (!this.collection.instanceId) {
            return Promise.reject("Collection doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.collection.root);
        Object.keys(params).forEach(name => {
            formData.append(name, params[name]);
        });
        formData.append("collectionId", this.collection.instanceId.toString());
        formData.append("itemId", this.id.toString());
        formData.append("itemType", this.itemType.toString());

        const queryString = new URLSearchParams(formData).toString();

        return modals.showSmartPreloader(
            fetch(`${this.collection.root.dataset.changeItemUrl}?${queryString}`, {
                credentials: "same-origin"
            }).then(response => {
                if (!response.ok) {
                    throw `${response.status} ${response.statusText}`;
                }
                return response.json();
            })
        );
    }

    /**
     * Отправка формы редактирования файла.
     * @param {PaperModal} modal
     * @returns {Promise}
     */
    sendChangeForm(modal) {
        if (!this.collection.instanceId) {
            return Promise.reject("Collection doesn't exist");
        }

        const form = modal._body.querySelector("form");
        if (!form) {
            return Promise.reject("Form not found");
        }

        const formData = new FormData(form);

        return modals
            .showSmartPreloader(
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
            )
            .then(response => {
                if (response.errors && response.errors.length) {
                    throw response.errors;
                }

                formUtils.cleanAllErrors(modal._body);
                if (response.form_errors) {
                    formUtils.setErrorsFromJSON(modal._body, response.form_errors);
                } else {
                    modal.destroy();

                    const caption = this.root.querySelector(this.config.caption);
                    caption && (caption.textContent = response.caption);

                    const previewLink = this.root.querySelector(this.config.viewButton);
                    previewLink && (previewLink.href = response.url);
                }
            })
            .catch(reason => {
                if (reason instanceof Error) {
                    // JS-ошибки дублируем в консоль
                    console.error(reason);
                }
                modals.showErrors(reason);
            });
    }
}

class CollectionItem extends PermanentCollectionItemBase {}

class Collection extends EventEmitter {
    static Defaults = {
        input: ".collection__input",
        dropzone: ".paper-dropzone__overlay",

        // контейнер, содержащий элементы коллекции
        itemContainer: ".collection__items",

        // селектор корневого DOM-элемента элемента коллекции
        item: ".collection-item",

        // кнопки
        uploadItemButton: ".collection__upload-item-button",
        createCollectionButton: ".collection__create-collection-button",
        deleteCollectionButton: ".collection__delete-collection-button",

        // шаблон селектора для <template>-тэгов с шаблонами элементов коллекции
        itemTemplatePattern: ".collection__{}-item-template",

        // JSON с данными о элементах коллекции
        dataJSON: ".collection--data"
    };

    static STATUS = {
        EMPTY: "empty",
        LOADING: "loading",
        READY: "ready",
        REMOVING: "removing"
    };

    static CSS = {
        container: "collection"
    };

    constructor(root, options) {
        super();

        this.config = deepmerge(this.constructor.Defaults, options || {});

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

    get itemContainer() {
        return this.root.querySelector(this.config.itemContainer);
    }

    get items() {
        return this.itemContainer.querySelectorAll(this.config.item);
    }

    get maxOrderValue() {
        let orderValues = Array.from(this.items)
            .map(item => {
                const instance = item.collectionItem;
                return parseInt(instance.root.dataset.order);
            })
            .filter(order => {
                return !isNaN(order);
            });

        if (!orderValues.length) {
            return -1;
        }

        return Math.max.apply(null, orderValues);
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
        this.root.collection = this;

        this._initItems();

        // Отключение Drag-n-drop, если коллекция не поддерживает файлы
        const uploadItemButton = this.root.querySelector(this.config.uploadItemButton);
        if (uploadItemButton) {
            this.root.uploader = this._createUploader();
        }

        this._sortable = this._initSortable();
        this._addListeners();
    }

    destroy() {
        if (this._sortable) {
            this._sortable.destroy();
        }

        if (this.uploader) {
            this.uploader.destroy();
            this.root.uploader = null;
        }

        this.root.collection = null;
    }

    /**
     * @returns {string}
     */
    getStatus() {
        return Object.values(this.STATUS).find(value => {
            return this.root.classList.contains(`${this.CSS.container}--${value}`);
        });
    }

    /**
     * @param {string} status
     */
    setStatus(status) {
        Object.values(this.STATUS).forEach(value => {
            this.root.classList.toggle(`${this.CSS.container}--${value}`, status === value);
        });
    }

    /**
     * @param {String|String[]} message
     */
    collectError(message) {
        const errorKey = `collection_${this.input.name}`;
        utils.collectError(errorKey, message);
    }

    showCollectedErrors() {
        const errorKey = `collection_${this.input.name}`;
        utils.showCollectedErrors(errorKey);
    }

    /**
     * Создание коллекции.
     *
     * @returns {Promise}
     */
    createCollection() {
        if (this.instanceId) {
            return Promise.reject("Collection already exists");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(name => {
            formData.append(name, params[name]);
        });

        return modals
            .showSmartPreloader(
                fetch(this.root.dataset.createCollectionUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    body: formData
                }).then(response => {
                    if (!response.ok) {
                        throw `${response.status} ${response.statusText}`;
                    }
                    return response.json();
                })
            )
            .then(response => {
                if (response.errors && response.errors.length) {
                    throw response.errors;
                }

                this.setStatus(this.STATUS.READY);

                this._fillCollection(response);
            })
            .catch(reason => {
                if (reason instanceof Error) {
                    // JS-ошибки дублируем в консоль
                    console.error(reason);
                }
                modals.showErrors(reason);
            });
    }

    /**
     * Удаление коллекции.
     *
     * @returns {Promise}
     */
    deleteCollection() {
        if (!this.instanceId) {
            return Promise.reject("Collection doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(name => {
            formData.append(name, params[name]);
        });
        formData.append("collectionId", this.instanceId);

        // отмена загрузки всех файлов из очереди.
        if (this.uploader) {
            this.uploader.cancelAll();
        }

        return modals
            .showSmartPreloader(
                fetch(this.root.dataset.deleteCollectionUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    body: formData
                }).then(response => {
                    if (!response.ok) {
                        throw `${response.status} ${response.statusText}`;
                    }
                    return response.json();
                })
            )
            .then(response => {
                if (response.errors && response.errors.length) {
                    throw response.errors;
                }

                this.setStatus(this.STATUS.REMOVING);

                this._disposeCollection(response);

                return this._removeAllItems().then(() => {
                    this.setStatus(this.STATUS.EMPTY);
                });
            });
    }

    /**
     * Рендеринг шаблона элемента галереи.
     *
     * @param {String} itemType
     * @param {Object?} context
     * @returns {String}
     */
    createItem(itemType, context) {
        const selector = this.config.itemTemplatePattern.replace("{}", itemType);
        const template = this.root.querySelector(selector);
        return Mustache.render(template.innerHTML, context || {});
    }

    /**
     * Создание экземпляра JS-класса элемента галереи.
     *
     * @param {String} itemType
     * @param {HTMLElement} element
     * @param {Object?} options
     * @returns {CollectionItemBase}
     */
    initItem(itemType, element, options) {
        // TODO: ability to register custom itemType
        if (itemType === "preloader") {
            return new PreloaderItem(element, this, options);
        } else {
            return new CollectionItem(element, this, options);
        }
    }

    /**
     * Private methods
     */

    /**
     * Создание элементов коллекции из JSON.
     *
     * @private
     */
    _initItems() {
        this.itemContainer.innerHTML = "";

        const dataElement = this.root.querySelector(this.config.dataJSON);
        const data = JSON.parse(dataElement.textContent);
        for (let itemData of data) {
            const itemType = itemData.itemType;

            const itemHTML = this.createItem(itemType, itemData);

            this.itemContainer.insertAdjacentHTML("beforeend", itemHTML);
            const items = this.items;
            const item = items[items.length - 1];

            this.initItem(itemType, item);
        }
    }

    /**
     * @private
     * @returns {Uploader}
     */
    _createUploader() {
        const options = Object.assign(
            {
                url: this.root.dataset.uploadItemUrl,
                uploadMultiple: true,
                params: file => {
                    const params = utils.getPaperParams(this.root);
                    params.collectionId = this.instanceId;

                    const preloader = this._getPreloaderByFile(file);
                    params.order = preloader.root.dataset.order;

                    return params;
                },

                container: this.root,
                button: this.root.querySelector(this.config.uploadItemButton),
                dropzone: this.root.querySelector(this.config.dropzone)
            },
            utils.processConfiguration(this.root.dataset.configuration)
        );

        return new Uploader(options);
    }

    /**
     * @private
     */
    _addListeners() {
        if (this.uploader) {
            this.uploader.on("submitted", file => {
                const status = this.getStatus();
                if (status !== this.STATUS.LOADING) {
                    this.setStatus(this.STATUS.LOADING);
                }

                // создание прелоадера
                const itemHTML = this.createItem("preloader", {
                    uuid: this.uploader.getUUID(file),
                    name: file.name,
                    order: this.maxOrderValue + 1
                });

                this.itemContainer.insertAdjacentHTML("beforeend", itemHTML);
                const items = this.items;
                const item = items[items.length - 1];

                this.initItem("preloader", item);
            });

            this.uploader.on("upload", (file, xhr, formData) => {
                const preloader = this._getPreloaderByFile(file);
                if (preloader) {
                    preloader.trigger("upload", [file, xhr, formData]);
                }
            });

            this.uploader.on("progress", (file, percentage) => {
                const preloader = this._getPreloaderByFile(file);
                if (preloader) {
                    preloader.trigger("progress", [file, percentage]);
                }
            });

            this.uploader.on("cancel", file => {
                const preloader = this._getPreloaderByFile(file);
                if (preloader) {
                    preloader.trigger("cancel", [file]);
                }
            });

            this.uploader.on("complete", (file, response) => {
                const preloader = this._getPreloaderByFile(file);
                if (preloader) {
                    preloader.trigger("complete", [file, response]);
                }
            });

            this.uploader.on("error", (file, message) => {
                this.collectError(message);

                const preloader = this._getPreloaderByFile(file);
                if (preloader) {
                    preloader.trigger("error", [file, message]);
                }
            });

            this.uploader.on("all_complete", () => {
                this.setStatus(this.STATUS.READY);

                this.showCollectedErrors();
            });
        }

        // создание коллекции
        if (this.config.createCollectionButton) {
            this.root.addEventListener("click", event => {
                const createCollectionButton = event.target.closest(this.config.createCollectionButton);
                if (createCollectionButton) {
                    event.preventDefault();

                    // Предотвращаем повторные нажатия
                    createCollectionButton.disabled = true;

                    this.createCollection().finally(() => {
                        createCollectionButton.disabled = false;
                    });
                }
            });
        }

        // удаление коллекции
        if (this.config.deleteCollectionButton) {
            this.root.addEventListener("click", event => {
                const deleteCollectionButton = event.target.closest(this.config.deleteCollectionButton);
                if (deleteCollectionButton) {
                    event.preventDefault();

                    // Препятствуем открытию нескольких окон
                    deleteCollectionButton.disabled = true;

                    modals.createModal({
                        modalClass: "paper-modal--warning fade",
                        title: gettext("Confirm deletion"),
                        body: gettext("Are you sure you want to <b>DELETE</b> this collection?"),
                        buttons: [
                            {
                                label: gettext("Cancel"),
                                buttonClass: "btn-light",
                                onClick: (event, popup) => {
                                    popup.destroy();
                                }
                            },
                            {
                                autofocus: true,
                                label: gettext("Delete"),
                                buttonClass: "btn-danger",
                                onClick: (event, popup) => {
                                    Promise.all([popup.destroy(), this.deleteCollection()]).catch(reason => {
                                        if (reason instanceof Error) {
                                            // JS-ошибки дублируем в консоль
                                            console.error(reason);
                                        }
                                        modals.showErrors(reason);
                                    });
                                }
                            }
                        ],
                        onInit: function () {
                            this.show();
                        },
                        onDestroy: function () {
                            deleteCollectionButton.disabled = false;
                        }
                    });
                }
            });
        }

        // выделение элементов галереи
        let lastChangedItem = null;
        let lastChangedItemChecked = true;
        this.root.addEventListener("click", event => {
            const item = event.target.closest(this.config.item);
            if (!item) {
                return;
            }

            const instance = item.collectionItem;
            if (!(instance instanceof PermanentCollectionItemBase)) {
                return;
            }

            let isCheckboxClick;
            if (instance.config.checkbox) {
                if (event.target.htmlFor) {
                    // <label> tag
                    const labelFor = document.getElementById(event.target.htmlFor);
                    isCheckboxClick = Boolean(labelFor.closest(instance.config.checkbox));
                } else {
                    isCheckboxClick = Boolean(event.target.closest(instance.config.checkbox));
                }
            } else {
                isCheckboxClick = false;
            }

            if (event.shiftKey) {
                if (lastChangedItem) {
                    // mass toggle state
                    const items = Array.from(this.items);
                    const lastChangedItemIndex = items.indexOf(lastChangedItem);
                    const currentItemIndex = items.indexOf(item);
                    const startIndex = Math.min(lastChangedItemIndex, currentItemIndex);
                    const endIndex = Math.max(lastChangedItemIndex, currentItemIndex);
                    const item_slice = items.slice(startIndex, endIndex + 1);
                    item_slice.forEach(item => {
                        const instance = item.collectionItem;
                        if (instance instanceof PermanentCollectionItemBase) {
                            instance.checked = lastChangedItemChecked;
                        }
                    });
                }
            } else if (event.ctrlKey) {
                // toggle checked
                let targetState;
                if (isCheckboxClick) {
                    targetState = instance.checkbox.checked;
                } else {
                    targetState = !instance.checkbox.checked;
                }

                instance.checked = targetState;
                lastChangedItem = item;
                lastChangedItemChecked = targetState;
            } else {
                if (isCheckboxClick) {
                    // toggle checked
                    let targetState = instance.checkbox.checked;
                    instance.checked = targetState;
                    lastChangedItem = item;
                    lastChangedItemChecked = targetState;
                }
            }

            // Фокус на элементе, чтобы можно было удалить выбранные элементы
            // нажав клавишу Delete.
            item.focus();
        });

        // удаление выделенных элементов при нажатии Delete
        this.root.addEventListener("keyup", event => {
            if (event.code !== "Delete") {
                return;
            }

            const items = Array.from(this.items);
            const selectedItems = items.filter(item => {
                const instance = item.collectionItem;
                return instance.checked;
            });

            if (!selectedItems.length) {
                return;
            }

            modals.createModal({
                modalClass: "paper-modal--warning fade",
                title: gettext("Confirmation"),
                body: interpolate(
                    ngettext(
                        "Are you sure you want to <b>DELETE</b> the selected item?",
                        "Are you sure you want to <b>DELETE</b> the <b>%(count)s</b> selected items?",
                        selectedItems.length
                    ),
                    {
                        count: selectedItems.length
                    }
                ),
                buttons: [
                    {
                        label: gettext("Cancel"),
                        buttonClass: "btn-light",
                        onClick: (event, popup) => {
                            popup.destroy();
                        }
                    },
                    {
                        autofocus: true,
                        label: gettext("Delete"),
                        buttonClass: "btn-danger",
                        onClick: (event, popup) => {
                            Promise.all([popup.destroy(), this._deleteItems(selectedItems)]);
                        }
                    }
                ],
                onInit: function () {
                    this.show();
                }
            });
        });
    }

    /**
     * @private
     * @returns {Sortable}
     */
    _initSortable() {
        return Sortable.create(this.itemContainer, {
            animation: 0,
            draggable: this.config.item,
            filter: (event, target) => {
                // Отключение сортировки при нажатой Ctrl или Shift,
                // чтобы сортировка не мешала выделять элементы.
                if (event.ctrlKey || event.shiftKey) {
                    return true;
                }

                // Отключение сортировки при загрузке и удалении.
                const status = this.getStatus();
                if (status === this.STATUS.LOADING || status === this.STATUS.REMOVING) {
                    return true;
                }

                if (!target) {
                    return true;
                }

                const item = target.closest(this.config.item);
                const instance = item.collectionItem;

                // Фильтрация прелоадеров
                if (instance instanceof PreloaderItem) {
                    return true;
                }

                // Фильтрация удаляемых элементов
                const itemStatus = instance.getStatus();
                if (itemStatus === instance.STATUS.REMOVING) {
                    return true;
                }
            },
            handle: ".sortable-handler",
            ghostClass: "sortable-ghost",
            onEnd: () => {
                const orderList = Array.from(this.items)
                    .map(item => {
                        const instance = item.collectionItem;
                        if (instance instanceof PermanentCollectionItemBase) {
                            return instance.id;
                        }
                    })
                    .filter(Boolean);

                const data = new FormData();
                const params = utils.getPaperParams(this.root);
                Object.keys(params).forEach(name => {
                    data.append(name, params[name]);
                });
                data.append("collectionId", this.instanceId.toString());
                data.append("orderList", orderList.join(","));

                fetch(this.root.dataset.sortItemsUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    body: data
                })
                    .then(response => {
                        if (!response.ok) {
                            throw `${response.status} ${response.statusText}`;
                        }
                        return response.json();
                    })
                    .then(response => {
                        if (response.errors && response.errors.length) {
                            throw response.errors;
                        }

                        response.orderMap = response.orderMap || {};

                        // update order
                        this.items.forEach(item => {
                            const id = parseInt(item.dataset.id);
                            item.dataset.order = response.orderMap[id];
                        });
                    })
                    .catch(reason => {
                        if (reason instanceof Error) {
                            // JS-ошибки дублируем в консоль
                            console.error(reason);
                        }
                        modals.showErrors(reason);
                    });
            }
        });
    }

    /**
     * @param {object<string,*>} response
     * @private
     */
    _fillCollection(response) {
        this.instanceId = response.collection_id;
    }

    /**
     * @param {object<string,*>} response
     * @private
     */
    _disposeCollection(response) {
        this.instanceId = "";
    }

    /**
     * Анимированное удаление всех элементов коллекции.
     *
     * @private
     * @returns {Promise}
     */
    _removeAllItems() {
        return Promise.all(
            Array.from(this.items).map(item => {
                const instance = item.collectionItem;
                if (instance) {
                    return instance.removeDOM();
                }
            })
        );
    }

    /**
     * Удаление выбранных элементов.
     *
     * @param {NodeList|HTMLElement[]} items
     * @private
     * @returns {Promise}
     */
    _deleteItems(items) {
        return allSettled(
            Array.from(items).map(item => {
                const instance = item.collectionItem;
                if (instance instanceof PermanentCollectionItemBase) {
                    return instance.delete();
                }
            })
        ).then(results => {
            for (let result of results) {
                if (result.status === "rejected") {
                    const reason = result.reason;
                    if (reason instanceof Error) {
                        // JS-ошибки дублируем в консоль
                        console.error(reason);
                    }
                    this.collectError(reason);
                }
            }

            this.showCollectedErrors();
        });
    }

    /**
     * Получение DOM-элемента прелоадера для загружаемого файла.
     *
     * @param {File} file
     * @returns {null|CollectionItemBase|*}
     */
    _getPreloaderByFile(file) {
        const uuid = this.uploader.getUUID(file);

        const preloaderElement = Array.from(this.items).find(preloader => {
            const instance = preloader.collectionItem;
            if (instance instanceof PreloaderItem) {
                return instance.uuid === uuid;
            }
        });

        return preloaderElement && preloaderElement.collectionItem;
    }
}

class CollectionWidget extends Widget {
    _init(element) {
        new Collection(element);
    }

    _destroy(element) {
        if (element.collection) {
            element.collection.destroy();
        }
    }
}

export { CollectionItemBase, PreloaderItem, PermanentCollectionItemBase, Collection, CollectionWidget };
