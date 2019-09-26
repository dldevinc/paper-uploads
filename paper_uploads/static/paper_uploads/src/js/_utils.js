// PaperAdmin API
const bootbox = window.paperAdmin.bootbox;

let _errors = [];


function formatErrors(errors) {
    if (Array.isArray(errors)) {
        if (errors.length === 1) {
            return errors[0]
        } else {
            let output = [
                `Please correct the following errors:`,
                `<ul class="px-4 mb-0">`,
            ];
            for (let i=0, l=errors.length; i<l; i++) {
                output.push(`<li>${errors[i]}</li>`);
            }
            output.push(`</ul>`);
            output = output.join('\n');
            return output
        }
    }
    return errors
}


/**
 * Мгновенный показ сообщения.
 *
 * @param {String|String[]} error
 */
function showError(error) {
    console.debug(`Show error: ${error}`);
    bootbox.alert({
        message: formatErrors(error)
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

    bootbox.alert({
        message: formatErrors(_errors)
    });

    _errors = [];
}

export {
    showError,
    collectError,
    showCollectedErrors
};
