import {BaseWidget} from "./base_widget";

// PaperAdmin API
const emitters = window.paperAdmin.emitters;

// CSS
import "../css/image_widget.scss";


function initWidget(element) {
    new BaseWidget(element, {
        input: '.image-uploader__input',
        uploadButton: '.image-uploader__upload-button',
        cancelButton: '.image-uploader__cancel-button',
        changeButton: '.image-uploader__change-button',
        deleteButton: '.image-uploader__delete-button',
        link: '.image-uploader__link',
        urls: {
            upload: element.dataset.uploadUrl,
            change: element.dataset.changeUrl,
            delete: element.dataset.deleteUrl,
        }
    });
}


function initWidgets(root = document.body) {
    let file_selector = '.image-uploader';
    root.matches(file_selector) && initWidget(root);
    root.querySelectorAll(file_selector).forEach(initWidget);
}


initWidgets();
emitters.dom.on('mutate', initWidgets);
