import * as file from "./widgets/file.js";
import * as image from "./widgets/image.js";
import * as collection from "./widgets/collection.js";

// import all SVG images
function importAll(r) {
    return r.keys().map(r);
}
importAll(require.context("../img/files/", false, /\.svg$/));

const fileWidget = new file.FileUploaderWidget();
if (typeof fileWidget.bind === "function") {
    // new-style widgets
    fileWidget.bind(".file-uploader");
    fileWidget.attach();
} else {
    // old-style widgets
    fileWidget.initAll(".file-uploader");
    fileWidget.observe(".file-uploader");
}

const imageWidget = new image.ImageUploaderWidget();
if (typeof imageWidget.bind === "function") {
    // new-style widgets
    imageWidget.bind(".image-uploader");
    imageWidget.attach();
} else {
    // old-style widgets
    imageWidget.initAll(".image-uploader");
    imageWidget.observe(".image-uploader");
}

const collectionWidget = new collection.CollectionWidget();
if (typeof collectionWidget.bind === "function") {
    // new-style widgets
    collectionWidget.bind(".collection--default");
    collectionWidget.attach();
} else {
    // old-style widgets
    collectionWidget.initAll(".collection--default");
    collectionWidget.observe(".collection--default");
}

export const paperUploads = {
    file,
    image,
    collection
};
