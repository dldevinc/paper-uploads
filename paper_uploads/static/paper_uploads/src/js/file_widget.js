import {BaseWidget} from "./base_widget";

// PaperAdmin API
const emitters = window.paperAdmin.emitters;


// CSS
import "../css/file_widget.scss";


function initWidget(element) {
    new BaseWidget(element, {
        input: ".file-uploader__input",
        uploadButton: ".file-uploader__upload-button",
        cancelButton: ".file-uploader__cancel-button",
        changeButton: ".file-uploader__change-button",
        deleteButton: ".file-uploader__delete-button",
        link: ".file-uploader__view-button",
        urls: {
            upload: element.dataset.uploadUrl,
            change: element.dataset.changeUrl,
            delete: element.dataset.deleteUrl,
        }
    });
}


function initWidgets(root = document.body) {
    let file_selector = ".file-uploader";
    root.matches(file_selector) && initWidget(root);
    root.querySelectorAll(file_selector).forEach(initWidget);
}


initWidgets();
emitters.dom.on("mutate", initWidgets);
