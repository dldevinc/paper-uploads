import {BaseWidget} from "./base_widget";

// PaperAdmin API
const whenDomReady = window.paperAdmin.whenDomReady;
const emitters = window.paperAdmin.emitters;


// CSS
import "../css/file_widget.scss";


function initWidget(element) {
    if (element.closest('.empty-form')) {
        return
    }

    new BaseWidget(element, {
        input: '.file-uploader__input',
        uploadButton: '.file-uploader__upload-button',
        changeButton: '.file-uploader__change-button',
        deleteButton: '.file-uploader__delete-button',
        link: '.file-uploader__link',
        urls: {
            upload: element.dataset.uploadUrl,
            change: element.dataset.changeUrl,
            delete: element.dataset.deleteUrl,
        }
    });
}


function initWidgets(root = document.body) {
    let file_selector = '.file-uploader';
    root.matches(file_selector) && initWidget(root);
    root.querySelectorAll(file_selector).forEach(initWidget);
}


whenDomReady(initWidgets);
emitters.dom.on('mutate', initWidgets);
