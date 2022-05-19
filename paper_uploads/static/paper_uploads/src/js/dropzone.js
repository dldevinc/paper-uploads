/* global gettext */
/* global interpolate */

import Dropzone from "dropzone";

// Отмена автоматической инициализации на .dropzone элементах.
Dropzone.autoDiscover = false;


const without = (list, rejectedItem) =>
    list.filter((item) => item !== rejectedItem).map((item) => item);

// Вызов события cancel не только для файлов, которые в процессе загрузки,
// но и для тех, которые находятся в очереди.
Dropzone.prototype.removeFile = function(file) {
    if (
        (file.status === Dropzone.ADDED) ||
        (file.status === Dropzone.QUEUED) ||
        (file.status === Dropzone.UPLOADING)
    ) {
        this.cancelUpload(file);
    }

    this.files = without(this.files, file);

    this.emit("removedfile", file);
    if (this.files.length === 0) {
        return this.emit("reset");
    }
}


// 1) Формат опции maxFilesize изменен с 'MB' на 'B'.
// 2) Форматирование размеров файла.
// 3) Тексты ошибок изменены на аналоги с языковой поддержкой.
// 4) Разделение метода isValidFile на проверку расширения и MIME type
//    для вывода разных ошибок.
Dropzone.prototype.accept = function(file, done) {
    if (
        this.options.maxFilesize &&
        file.size > this.options.maxFilesize
    ) {
        done(
            interpolate(
                gettext("File `%(name)s` is too large. Maximum file size is %(limit_value)s."),
                {
                    "name": file.name,
                    "limit_value": this.filesize(this.options.maxFilesize)
                },
                true
            )
        );
    } else if (!Dropzone.isValidExtension(file, this.options.acceptedFiles)) {
        done(
            interpolate(
                gettext("File `%(name)s` has an invalid extension. Valid extension(s): %(allowed)s"),
                {
                    "name": file.name,
                    "allowed": this.options.acceptedFiles.split(",").filter(function(validType) {
                        return validType.charAt(0) === ".";
                    }).map(function(ext) {
                        return ext.toLowerCase().substr(1);
                    }).join(", ")
                },
                true
            )
        );
    } else if (!Dropzone.isValidMIME(file, this.options.acceptedFiles)) {
        done(
            interpolate(
                gettext("File `%(name)s` has an invalid mimetype '%(mimetype)s'"),
                {
                    "name": file.name,
                    "mimetype": file.type
                },
                true
            )
        );
    } else if (
        this.options.maxFiles != null &&
        this.getAcceptedFiles().length >= this.options.maxFiles
    ) {
        done(
            this.options.dictMaxFilesExceeded.replace(
                "{{maxFiles}}",
                this.options.maxFiles
            )
        );
        this.emit("maxfilesexceeded", file);
    } else {
        this.options.accept.call(this, file, done);
    }
}

Dropzone.isValidExtension = function (file, acceptedFiles) {
    if (!acceptedFiles) {
        return true;
    }

    acceptedFiles = acceptedFiles.split(",").filter(function(validType) {
        return validType.charAt(0) === ".";
    });

    if (!acceptedFiles.length) {
        return true;
    }

    for (let validType of acceptedFiles) {
        validType = validType.trim();
        if (validType.charAt(0) === ".") {
            if (
                file.name
                .toLowerCase()
                .indexOf(
                    validType.toLowerCase(),
                    file.name.length - validType.length
                ) !== -1
            ) {
                return true;
            }
        }
    }

    return false;
};


Dropzone.isValidMIME = function (file, acceptedFiles) {
    if (!acceptedFiles) {
        return true;
    }

    acceptedFiles = acceptedFiles.split(",").filter(function(validType) {
        return validType.charAt(0) !== ".";
    });

    if (!acceptedFiles.length) {
        return true;
    }

    let mimeType = file.type;
    let baseMimeType = mimeType.replace(/\/.*$/, "");

    for (let validType of acceptedFiles) {
        validType = validType.trim();
        if (/\/\*$/.test(validType)) {
            // This is something like a image/* mime type
            if (baseMimeType === validType.replace(/\/.*$/, "")) {
                return true;
            }
        } else {
            if (mimeType === validType) {
                return true;
            }
        }
    }

    return false;
};

export {
    Dropzone
}
