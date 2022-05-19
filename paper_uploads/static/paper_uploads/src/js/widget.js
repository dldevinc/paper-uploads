import {Uploader} from "./uploader.js";
import * as file from "./widgets/file.js";
import * as image from "./widgets/image.js";
import * as collection from "./widgets/collection.js";

// import all SVG images
function importAll(r) {
    return r.keys().map(r);
}
importAll(require.context("../img/files/", false, /\.svg$/));


const fileWidget = new file.FileUploaderWidget();
fileWidget.observe(".file-uploader");
fileWidget.initAll(".file-uploader");


const imageWidget = new image.ImageUploaderWidget();
imageWidget.observe(".image-uploader");
imageWidget.initAll(".image-uploader");


const collectionWidget = new collection.CollectionWidget();
collectionWidget.observe(".collection");
collectionWidget.initAll(".collection");


export const paperUploads = {
    Uploader,
    file,
    image,
    collection
}
