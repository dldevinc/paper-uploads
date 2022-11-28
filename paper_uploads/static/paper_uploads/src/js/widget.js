import * as file from "./widgets/file.js";
import * as image from "./widgets/image.js";
import * as collection from "./widgets/collection.js";

// import all SVG images
function importAll(r) {
    return r.keys().map(r);
}
importAll(require.context("../img/files/", false, /\.svg$/));

const fileWidget = new file.FileUploaderWidget();
fileWidget.initAll(".file-uploader");
fileWidget.observe(".file-uploader");

const imageWidget = new image.ImageUploaderWidget();
imageWidget.initAll(".image-uploader");
imageWidget.observe(".image-uploader");

const collectionWidget = new collection.CollectionWidget();
collectionWidget.initAll(".collection");
collectionWidget.observe(".collection");

export const paperUploads = {
    file,
    image,
    collection
};
