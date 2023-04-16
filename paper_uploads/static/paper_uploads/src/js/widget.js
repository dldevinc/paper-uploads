/* global XClass */

import "./icons.js";
import * as file from "./widgets/file.js";
import * as image from "./widgets/image.js";
import * as collection from "./widgets/collection.js";

XClass.register("paper-upload-file", {
    init: function (element) {
        element._fileUploader = new file.FileUploader(element);
    },
    destroy: function (element) {
        if (element._fileUploader) {
            element._fileUploader.destroy();
            delete element._fileUploader;
        }
    }
});

XClass.register("paper-upload-image", {
    init: function (element) {
        element._imageUploader = new image.ImageUploader(element);
    },
    destroy: function (element) {
        if (element._imageUploader) {
            element._imageUploader.destroy();
            delete element._imageUploader;
        }
    }
});

XClass.register("paper-upload-collection", {
    init: function (element) {
        element._collectionUploader = new collection.Collection(element);
    },
    destroy: function (element) {
        if (element._collectionUploader) {
            element._collectionUploader.destroy();
            delete element._collectionUploader;
        }
    }
});

export const paperUploads = {
    file,
    image,
    collection
};
