/**
 * Класс ошибки валидации файла при событии onSubmit()
 * @constructor
 */
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = this.constructor.name;
    }
}

export {
    ValidationError
}
