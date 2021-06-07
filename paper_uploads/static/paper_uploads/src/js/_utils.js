// PaperAdmin API
const modals = window.paperAdmin.modals;

let _errors = [];


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
 * Единая точка входа для показа ошибок.
 * Используется для глобальной модификации параметров окна сообщений об ошибках.
 * @param {String|String[]} errors
 */
function showErrors(errors) {
    return modals.showErrors(errors);
}

/**
 * Добавление ошибки в словарь для отложенного показа.
 * @param {String|String[]} errors
 */
function collectError(errors) {
    if (typeof errors === "string") {
        _errors.push(errors);
    } else if (Array.isArray(errors)) {
        _errors = _errors.concat(errors);
    }
}

/**
 * Показ отложенных ошибок
 */
function showCollectedErrors() {
    if (!_errors || !_errors.length) {
        return
    }

    const modal = showErrors(_errors);
    _errors = [];
    return modal;
}

export {
    getPaperParams,
    showErrors,
    collectError,
    showCollectedErrors
};
