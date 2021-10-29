/* global gettext */
/* global ngettext */
/* global interpolate */

import allSettled from "promise.allsettled";
import deepmerge from "deepmerge";
import EventEmitter from "wolfy87-eventemitter";
import Mustache from "mustache";
import {Uploader} from "./uploader";
import * as utils from "./utils";

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
    static Defaults = {
        removingState: "removing"
    }

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

    get removing() {
        return this.root.classList.contains(this.config.removingState);
    }

    set removing(value) {
        this.root.classList.toggle(this.config.removingState, value);
    }

    init() {
        // store instance
        this.root.collectionItem = this;

        this._addListeners();
    }

    destroy() {
        this.root.collectionItem = null;
        this.root.remove();
    }

    _addListeners() {

    }

    /**
     * Анимированное удаление DOM-элемента.
     */
    removeDOM() {
        const animationPromise = new Promise(function(resolve) {
            this.root.addEventListener("animationend", () => { resolve() });
            this.removing = true;
        }.bind(this));

        const fallbackPromise = new Promise(function(resolve) {
            setTimeout(resolve, 600);
        });

        return Promise.race([animationPromise, fallbackPromise]).then(function() {
            this.destroy();
        }.bind(this));
    }
}


/**
 * Элемент-заглушка, связывающий загружаемый файл и его DOM-элемент.
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
        processingState: "processing",

        progressBar: ".progress-bar",

        cancelUploadButton: ".collection-item__cancel-button"
    });

    get file() {
        return this.config.file;
    }

    get uuid() {
        return this.collection.uploader.getUUID(this.file);
    }

    get progressBar() {
        return this.root.querySelector(this.config.progressBar);
    }

    get processing() {
        return this.root.classList.contains(this.config.processingState);
    }

    set processing(value) {
        this.root.classList.toggle(this.config.processingState, value);
    }

    init() {
        super.init();

        this.root.setAttribute("data-uuid", this.uuid);
    }

    _addListeners() {
        super._addListeners();

        this.on("progress", function(file, percentage) {
            const progressBar = this.progressBar;
            progressBar && (progressBar.style.height = percentage + "%");

            if (percentage >= 100) {
                this.processing = true;

                // Добавление минимальной задержки для стадии processing,
                // чтобы переход от стадии loading к finished был более плавным.
                this.processingPromise = new Promise(function(resolve) {
                    setTimeout(() => {resolve()}, 500);
                });
            }
        }.bind(this));

        this.on("error", function() {
            this.removeDOM();
        }.bind(this));

        this.on("complete", function(file, response) {
            const onComplete = function(response) {
                const itemType = response.itemType;

                // замена прелоадера перманентным элементом
                const itemHTML = this.collection.createItem(itemType, response);

                this.root.insertAdjacentHTML("afterend", itemHTML);
                const item = this.root.nextElementSibling;

                this.collection.initItem(itemType, item, {
                    file: file
                });
                this.destroy();
            }.bind(this);

            if (this.processingPromise) {
                this.processingPromise.then(function() {
                    this.processingPromise = null;
                    onComplete(response);
                }.bind(this));
            } else {
                // Сюда попадать не должны, но на всякий случай...
                console.warn("processingPromise undefined");
                onComplete(response);
            }
        }.bind(this));

        // отмена загрузки
        if (this.config.cancelUploadButton) {
            this.root.addEventListener("click", function(event) {
                const cancelUploadButton = event.target.closest(this.config.cancelUploadButton);
                if (cancelUploadButton) {
                    event.preventDefault();
                    this.cancel();
                    this.removeDOM();
                }
            }.bind(this));
        }
    }

    /**
     * Отмена загрузки файла.
     */
    cancel() {
        this.collection.uploader.cancel(this.file);
    }
}


class PermanentCollectionItemBase extends CollectionItemBase {
    static Defaults = Object.assign({}, super.Defaults, {
        checkbox: ".collection-item__checkbox",

        viewButton: ".collection-item__view-button",
        changeButton: ".collection-item__change-button",
        deleteButton: ".collection-item__delete-button"
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
            this.root.addEventListener("click", function(event) {
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
                                    _this.delete()
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
                    event.stopPropagation();

                    // Препятствуем открытию нескольких окон
                    changeButton.disabled = true;

                    this.fetchChangeForm(
                        //
                    ).then(function(response) {
                        if (response.errors && response.errors.length) {
                            throw response.errors;
                        }

                        modals.createModal({
                            title: gettext("Edit item"),
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

        // просмотр файла
        if (this.config.viewButton) {
            this.root.addEventListener("click", function(event) {
                const viewButton = event.target.closest(this.config.viewButton);
                if (viewButton) {
                    // отключение выделения при клике с зажатым Ctrl или Shift
                    event.stopPropagation();
                }
            }.bind(this));
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
        Object.keys(params).forEach(function(name) {
            formData.append(name, params[name]);
        });
        formData.append("collectionId", this.collection.instanceId.toString());
        formData.append("itemId", this.id.toString());
        formData.append("itemType", this.itemType.toString());

        const _this = this;
        return modals.showSmartPreloader(
            fetch(this.collection.root.dataset.deleteItemUrl, {
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

            _this.removeDOM();
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
        Object.keys(params).forEach(function(name) {
            formData.append(name, params[name]);
        });
        formData.append("collectionId", this.collection.instanceId.toString());
        formData.append("itemId", this.id.toString());
        formData.append("itemType", this.itemType.toString());

        const queryString = new URLSearchParams(formData).toString();

        return modals.showSmartPreloader(
            fetch(`${this.collection.root.dataset.changeItemUrl}?${queryString}`, {
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
        if (!this.collection.instanceId) {
            return Promise.reject("Collection doesn't exist");
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


class FileItem extends PermanentCollectionItemBase {

}


class ImageItem extends PermanentCollectionItemBase {

}


class SVGItem extends PermanentCollectionItemBase {

}


class MediaItem extends PermanentCollectionItemBase {

}


class Collection extends EventEmitter {
    static Defaults = {
        emptyState: "empty",
        loadingState: "loading",

        input: ".collection__input",
        dropzone: ".dropzone__overlay",
        dropzoneActiveClassName: "dropzone__overlay--highlighted",

        // контейнер, содержащий элементы коллекции
        container: ".collection__items",

        // селектор корневого DOM-элемента элемента коллекции
        item: ".collection__item",

        // селектор прелоадеров
        preloader: ".collection-item--preloader",

        // кнопки
        uploadItemButton: ".collection__upload-item-button",
        createCollectionButton: ".collection__create-collection-button",
        deleteCollectionButton: ".collection__delete-collection-button",

        // шаблон селектора для <template>-тэгов с шаблонами элементов коллекции
        itemTemplatePattern: ".collection__{}-item-template",

        // JSON с данными о элементах коллекции
        dataJSON: ".collection--data",

        // карта соответствий типа элемента и JS-класса
        itemClasses: {
            preloader: PreloaderItem,
            file: FileItem,
            image: ImageItem,
            svg: SVGItem,
            media: MediaItem,
        }
    }

    constructor(root, options) {
        super();

        this.config = deepmerge(this.constructor.Defaults, options || {});

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

    get container() {
        return this.root.querySelector(this.config.container);
    }

    get items() {
        return this.container.querySelectorAll(this.config.item);
    }

    get maxOrderValue() {
        let orderValues = Array.from(this.items).map(function(item) {
            const instance = item.collectionItem;
            return parseInt(instance.root.dataset.order);
        }).filter(function(order) {
            return !isNaN(order);
        });

        if (!orderValues.length) {
            return 0;
        }

        return Math.max.apply(null, orderValues);
    }

    get instanceId() {
        return this.input.value;
    }

    set instanceId(value) {
        this.input.value = value;
    }

    get empty() {
        return this.root.classList.contains(this.config.emptyState);
    }

    set empty(value) {
        this.root.classList.toggle(this.config.emptyState, value);
    }

    get loading() {
        return this.root.classList.contains(this.config.loadingState);
    }

    set loading(value) {
        this.root.classList.toggle(this.config.loadingState, value);
    }

    init() {
        this.empty = !Boolean(this.instanceId);

        // store instance
        this.root.collection = this;

        this._initItems();
        this._initUploader();
        this._initSortable();
        this._addListeners();
    }

    destroy() {
        if (this.uploader) {
            this.uploader.destroy();
        }

        this.root.collection = null;
    }

    /**
     * Создание элементов коллекции из JSON.
     * @private
     */
    _initItems() {
        const dataElement = this.root.querySelector(this.config.dataJSON);
        const data = JSON.parse(dataElement.textContent);
        for (let itemData of data) {
            const itemType = itemData.itemType;

            const itemHTML = this.createItem(itemType, itemData);

            this.container.insertAdjacentHTML("beforeend", itemHTML);
            const items = this.items;
            const item = items[items.length - 1];

            this.initItem(itemType, item);
        }
    }

    _initUploader() {
        const options = Object.assign({
            url: this.root.dataset.uploadItemUrl,
            uploadMultiple: true,
            params: function(file) {
                const params = utils.getPaperParams(this.root);
                params.collectionId = this.instanceId;

                const preloader = this.getPreloaderByFile(file);
                params.order = preloader.root.dataset.order;

                return params
            }.bind(this),

            root: this.root,
            button: this.root.querySelector(this.config.uploadItemButton),
            dropzone: this.root.querySelector(this.config.dropzone),
            dropzoneActiveClassName: this.config.dropzoneActiveClassName
        }, utils.processConfiguration(this.root.dataset.configuration));

        new Uploader(options);
    }

    _addListeners() {
        const _this = this;

        this.uploader.on("submitted", function(file) {
            if (!this.loading) {
                this.loading = true;
            }

            // создание прелоадера
            const itemHTML = this.createItem("preloader", {
                name: file.name,
                order: this.maxOrderValue + 1
            });

            this.container.insertAdjacentHTML("beforeend", itemHTML);
            const items = this.items;
            const item = items[items.length - 1];

            this.initItem("preloader", item, {
                file: file
            });
        }.bind(this));

        this.uploader.on("upload", function(file, xhr, formData) {
            const preloader = this.getPreloaderByFile(file);
            if (preloader) {
                preloader.trigger("upload", [file, xhr, formData]);
            }
        }.bind(this));

        this.uploader.on("progress", function(file, percentage) {
            const preloader = this.getPreloaderByFile(file);
            if (preloader) {
                preloader.trigger("progress", [file, percentage]);
            }
        }.bind(this));

        this.uploader.on("cancel", function(file) {
            const preloader = this.getPreloaderByFile(file);
            if (preloader) {
                preloader.trigger("cancel", [file]);
            }
        }.bind(this));

        this.uploader.on("complete", function(file, response) {
            const preloader = this.getPreloaderByFile(file);
            if (preloader) {
                preloader.trigger("complete", [file, response]);
            }
        }.bind(this));

        this.uploader.on("error", function(file, message) {
            this.collectError(message);

            const preloader = this.getPreloaderByFile(file);
            if (preloader) {
                preloader.trigger("error", [file, message]);
            }
        }.bind(this));

        this.uploader.on("all_complete", function() {
            this.loading = false;

            this.showCollectedErrors();
        }.bind(this));

        // создание коллекции
        if (this.config.createCollectionButton) {
            this.root.addEventListener("click", function(event) {
                const createCollectionButton = event.target.closest(this.config.createCollectionButton);
                if (createCollectionButton) {
                    event.preventDefault();

                    // Предотвращаем повторные нажатия
                    createCollectionButton.disabled = true;

                    this.createCollection()
                        .finally(function() {
                            createCollectionButton.disabled = false;
                        });
                }
            }.bind(this));
        }

        // удаление коллекции
        if (this.config.deleteCollectionButton) {
            this.root.addEventListener("click", function(event) {
                const deleteCollectionButton = event.target.closest(this.config.deleteCollectionButton);
                if (deleteCollectionButton) {
                    event.preventDefault();

                    // Препятствуем открытию нескольких окон
                    deleteCollectionButton.disabled = true;

                    modals.createModal({
                        modalClass: "paper-modal--warning fade",
                        title: gettext("Confirm deletion"),
                        body: gettext("Are you sure you want to <b>DELETE</b> this collection?"),
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
                                    _this.deleteCollection()
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
                            deleteCollectionButton.disabled = false;
                        }
                    });
                }
            }.bind(this));
        }

        // выделение элементов галереи
        let lastChangedItem = null;
        let lastChangedItemChecked = true;
        this.root.addEventListener("click", function(event) {
            const item = event.target.closest(_this.config.item);
            if (!item) {
                return
            }

            const instance = item.collectionItem;
            if (!(instance instanceof PermanentCollectionItemBase)) {
                return
            }

            let isCheckboxClick;
            if (instance.config.checkbox) {
                if (event.target.htmlFor) {  // <label> tag
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
                    const items = Array.from(_this.items);
                    const lastChangedItemIndex = items.indexOf(lastChangedItem);
                    const currentItemIndex = items.indexOf(item);
                    const startIndex = Math.min(lastChangedItemIndex, currentItemIndex);
                    const endIndex = Math.max(lastChangedItemIndex, currentItemIndex);
                    const item_slice = items.slice(startIndex, endIndex + 1);
                    item_slice.forEach(function(item) {
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
        this.root.addEventListener("keyup", function(event) {
            if (event.code !== "Delete") {
                return
            }

            const items = Array.from(_this.items);
            const selectedItems = items.filter(function(item) {
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
                            _this._deleteItems(selectedItems)
                        ]);
                    }
                }],
                onInit: function() {
                    this.show();
                }
            });
        });
    }

    _initSortable() {
        const _this = this;
        return Sortable.create(this.container, {
            animation: 0,
            draggable: this.config.item,
            filter: function(event, target) {
                // Отключение сортировки при нажатой Ctrl или Shift,
                // чтобы сортировка не мешала выделять элементы.
                if (event.ctrlKey || event.shiftKey) {
                    return true
                }

                // Отключение сортировки при загрузки.
                if (_this.loading) {
                    return true;
                }

                if (!target) {
                    return true
                }

                const item = target.closest(_this.config.item);
                const instance = item.collectionItem;

                // Фильтрация прелоадеров
                if (instance instanceof PreloaderItem) {
                    return true
                }

                // Фильтрация удаляемых элементов
                if (instance.root.classList.contains(instance.config.removingState)) {
                    return true
                }
            },
            handle: ".sortable-handler",
            ghostClass: "sortable-ghost",
            onEnd: function() {
                const orderList = Array.from(this.items).map(function(item) {
                    const instance = item.collectionItem;
                    if (instance instanceof PermanentCollectionItemBase) {
                        return instance.id;
                    }
                }).filter(Boolean);

                const data = new FormData();
                const params = utils.getPaperParams(this.root);
                Object.keys(params).forEach(function(name) {
                    data.append(name, params[name]);
                });
                data.append("collectionId", this.instanceId.toString());
                data.append("orderList", orderList.join(","));

                fetch(this.root.dataset.sortItemsUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    body: data
                }).then(function(response) {
                    if (!response.ok) {
                        throw `${response.status} ${response.statusText}`;
                    }
                    return response.json();
                }).then(function(response) {
                    if (response.errors && response.errors.length) {
                        throw response.errors;
                    }

                    response.orderMap = response.orderMap || {};

                    // update order
                    _this.items.forEach(function(item) {
                        const id = parseInt(item.dataset.id);
                        item.dataset.order = response.orderMap[id];
                    });
                }).catch(function(reason) {
                    if (reason instanceof Error) {
                        // JS-ошибки дублируем в консоль
                        console.error(reason);
                    }
                    modals.showErrors(reason);
                });
            }.bind(this)
        });
    }

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
     * @returns {Promise}
     */
    createCollection() {
        if (this.instanceId) {
            return Promise.reject("Collection already exists");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(function(name) {
            formData.append(name, params[name]);
        });

        const _this = this;
        return modals.showSmartPreloader(
            fetch(this.root.dataset.createCollectionUrl, {
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

            _this._initCollection(response.collection_id);
        }).catch(function(reason) {
            if (reason instanceof Error) {
                // JS-ошибки дублируем в консоль
                console.error(reason);
            }
            modals.showErrors(reason);
        });
    }

    /**
     * Инициализация коллекции заданным ID.
     * @param {Number} collectionId
     * @private
     */
    _initCollection(collectionId) {
        this.empty = false;
        this.instanceId = collectionId;
    }

    /**
     * Удаление коллекции.
     * @returns {Promise}
     */
    deleteCollection() {
        if (!this.instanceId) {
            return Promise.reject("Collection doesn't exist");
        }

        const formData = new FormData();

        const params = utils.getPaperParams(this.root);
        Object.keys(params).forEach(function(name) {
            formData.append(name, params[name]);
        });
        formData.append("pk", this.instanceId);

        // отмена загрузки всех файлов из очереди.
        this.uploader.cancelAll();

        const _this = this;
        return modals.showSmartPreloader(
            fetch(this.root.dataset.deleteCollectionUrl, {
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

            _this._disposeCollection();
            return _this._removeAllItems();
        });
    }

    /**
     * Отвязываение виджета от коллекции.
     * @private
     */
    _disposeCollection() {
        this.empty = true;
        this.instanceId = "";
    }

    /**
     * Анимированное удаление всех элементов коллекции.
     * @returns {Promise}
     * @private
     */
    _removeAllItems() {
        return Promise.all(Array.from(this.items).map(function(item) {
            const instance = item.collectionItem;
            if (instance) {
                return instance.removeDOM();
            }
        }));
    }

    /**
     * Удаление выбранных элементов.
     * @param {NodeList|HTMLElement[]} items
     * @returns {Promise}
     * @private
     */
    _deleteItems(items) {
        return allSettled(
            Array.from(items).map(function(item) {
                const instance = item.collectionItem;
                if (instance instanceof PermanentCollectionItemBase) {
                    return instance.delete();
                }
            })
        ).then(function(results) {
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
        }.bind(this));
    }

    /**
     * Рендеринг шаблона элемента галереи.
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
     * @param {String} itemType
     * @param {HTMLElement} element
     * @param {Object?} options
     * @returns {CollectionItemBase}
     */
    initItem(itemType, element, options) {
        const itemClass = this.config.itemClasses[itemType];
        return new itemClass(element, this, options);
    }

    /**
     * Получение DOM-элемента прелоадера для загружаемого файла.
     * @param {File} file
     * @returns {null|CollectionItemBase|*}
     */
    getPreloaderByFile(file) {
        const uuid = this.uploader.getUUID(file);
        const preloaders = this.container.querySelectorAll(this.config.preloader);
        const preloaderElement = Array.from(preloaders).find(function(preloader) {
            const instance = preloader.collectionItem;
            return instance && (instance.uuid === uuid);
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
            element.collection = null;
        }
    }
}


const widget = new CollectionWidget();
widget.observe(".collection");
widget.initAll(".collection");
