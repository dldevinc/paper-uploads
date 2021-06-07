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
 * Мгновенный показ сообщения.
 * @param {String|String[]} error
 */
function showError(error) {
    console.debug(`Show error: ${error}`);
    return modals.showErrors(error, {
        title: 'Error'
    });
}

/**
 * Добавление ошибки в словарь для отложенного показа.
 * @param {String|String[]} error
 */
function collectError(error) {
    console.debug(`Collect error: ${error}`);
    if (typeof error === 'string') {
        _errors.push(error);
    } else if (Array.isArray(error)) {
        _errors = _errors.concat(error);
    }
}

/**
 * Показ отложенных ошибок
 */
function showCollectedErrors() {
    if (!_errors || !_errors.length) {
        return
    }

    const modal = modals.showErrors(_errors, {
        title: 'Error'
    });

    _errors = [];
    return modal;
}

export {
    getPaperParams,
    showError,
    collectError,
    showCollectedErrors
};
