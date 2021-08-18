/* global gettext */
/* global interpolate */

// PaperAdmin API
const modals = window.paperAdmin.modals;

let _errors = {};


/**
 * Чтение файла в формате dataURL.
 * @param {File} file
 * @returns {Promise}
 */
function readFile(file) {
    if (typeof file.dataURL !== "undefined") {
        return Promise.resolve(file);
    }

    return new Promise(function(resolve) {
        const fileReader = new FileReader();
        fileReader.onload = function() {
            file.dataURL = fileReader.result;
            resolve(file);
        }
        fileReader.readAsDataURL(file);
    });
}

/**
 * Вычленение из data-атрибутов тех, которые начинаются с "data-paper-".
 * @param element
 * @returns {Object}
 */
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


/**
 * Добавление ошибки в словарь для отложенного показа.
 * @param {String} key
 * @param {String|String[]} errors
 */
function collectError(key, errors) {
    if (typeof _errors[key] === "undefined") {
        _errors[key] = [];
    }

    if (typeof errors === "string") {
        _errors[key].push(errors);
    } else if (Array.isArray(errors)) {
        _errors[key] = _errors[key].concat(errors);
    }
}


/**
 * Показ отложенных ошибок.
 * @param {String} key
 * @returns {PaperModal|*}
 */
function showCollectedErrors(key) {
    if (!_errors[key] || !_errors[key].length) {
        return
    }

    const modal = modals.showErrors(_errors[key]);
    _errors[key] = [];
    return modal;
}


/**
 * Перенос конфигурации из JSON-формата в набор параметров класса Uploader.
 * @param {Object|String} configuration
 * @returns {Object}
 */
function processConfiguration(configuration) {
    if (typeof configuration === "string") {
        configuration = JSON.parse(configuration);
    }

    const options = {
        filters: []
    };

    if (configuration.allowedExtensions) {
        // Extensions
        configuration.allowedExtensions.map(function(ext) {
            if (ext[0] !== ".") {
                options.filters.push(`.${ext}`);
            } else {
                options.filters.push(ext);
            }
        })
    }

    if (configuration.acceptFiles) {
        // MIME types
        configuration.acceptFiles.forEach(function(item) {
            options.filters.push(item);
        });
    }

    if (configuration.sizeLimit) {
        // File size
        options.maxFilesize = configuration.sizeLimit;
    }

    // Если значение переменной true и файл не удалось загрузить в тег <img>,
    // то файл не загружается на сервер. В противном случае ответственность
    // за валидацию передаётся серверу.
    let strictImageValidation = configuration.strictImageValidation === true;

    if (configuration.minImageWidth || configuration.minImageHeight || configuration.maxImageWidth || configuration.maxImageHeight) {
        options.filters.push(function checkImage(file) {
            return readFile(file)
                .then(function(file) {
                    return new Promise(function(resolve, reject) {
                        // Not using `new Image` here because of a bug in latest Chrome versions.
                        // See https://github.com/enyo/dropzone/pull/226
                        let img = document.createElement("img");

                        img.onload = function() {
                            resolve(img);
                        }

                        img.onerror = function() {
                            if (strictImageValidation) {
                                reject(
                                    interpolate(
                                        gettext("File `%(name)s` is not an image"),
                                        {
                                            "name": file.name
                                        },
                                        true
                                    )
                                );
                            } else {
                                reject();
                            }
                        }

                        img.src = file.dataURL;
                    });
                })
                .then(function(img) {
                    let width = img.width;
                    let height = img.height;

                    const notWideEnough = configuration.minImageWidth && (width < configuration.minImageWidth);
                    const notTallEnough = configuration.minImageHeight && (height < configuration.minImageHeight);
                    const tooSmall = notWideEnough && notTallEnough;
                    const tooWide = configuration.maxImageWidth && (width > configuration.maxImageWidth);
                    const tooTall = configuration.maxImageHeight && (height > configuration.maxImageHeight);
                    const tooBig = tooWide && tooTall;

                    if (tooSmall) {
                        throw interpolate(
                            gettext("Image `%(name)s` is too small. Image should be at least %(width_limit)sx%(height_limit)s pixels."),
                            {
                                "name": file.name,
                                "width_limit": configuration.minImageWidth,
                                "height_limit": configuration.minImageHeight
                            },
                            true
                        )
                    } else if (notWideEnough) {
                        throw interpolate(
                            gettext("Image `%(name)s` is not wide enough. The minimum width is %(width_limit)s pixels."),
                            {
                                "name": file.name,
                                "width_limit": configuration.minImageWidth
                            },
                            true
                        )
                    } else if (notTallEnough) {
                        throw interpolate(
                            gettext("Image `%(name)s` is not tall enough. The minimum height is %(height_limit)s pixels."),
                            {
                                "name": file.name,
                                "height_limit": configuration.minImageHeight
                            },
                            true
                        )
                    }

                    if (tooBig) {
                        throw interpolate(
                            gettext("Image `%(name)s` is too big. Image should be at most %(width_limit)sx%(height_limit)s pixels."),
                            {
                                "name": file.name,
                                "width_limit": configuration.maxImageWidth,
                                "height_limit": configuration.maxImageHeight
                            },
                            true
                        )
                    } else if (tooWide) {
                        throw interpolate(
                            gettext("Image `%(name)s` is too wide. The maximum width is %(width_limit)s pixels."),
                            {
                                "name": file.name,
                                "width_limit": configuration.maxImageWidth
                            },
                            true
                        )
                    } else if (tooTall) {
                        throw interpolate(
                            gettext("Image `%(name)s` is too tall. The maximum height is %(height_limit)s pixels."),
                            {
                                "name": file.name,
                                "height_limit": configuration.maxImageHeight
                            },
                            true
                        )
                    }
                });
        }.bind(this));
    }

    return options;
}


export {
    getPaperParams,
    collectError,
    showCollectedErrors,
    readFile,
    processConfiguration
}
