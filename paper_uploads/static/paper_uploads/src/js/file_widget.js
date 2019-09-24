import {BaseWidget} from "./base_widget";

// PaperAdmin API
const whenDomReady = window.paperAdmin.whenDomReady;
const emitters = window.paperAdmin.emitters;


// CSS
import "../css/widget_file.scss";


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
    }).on('upload:error', function(id, messages) {
        let output;
        if (typeof messages === 'string') {
            output = `<b>Error</b>: ${messages}`;
        } else if (Array.isArray(messages)) {
            output = [
                `Please correct the following errors:`,
                `<ul class="px-4 mb-0">`,
            ];
            for (let i=0, l=messages.length; i<l; i++) {
                output.push(`<li>${messages[i]}</li>`);
            }
            output.push(`</ul>`);
            output = output.join('\n');
        }

        bootbox.alert({
            message: output
        });
    });
}


function initWidgets(root = document.body) {
    let file_selector = '.file-uploader';
    root.matches(file_selector) && initWidget(root);
    root.querySelectorAll(file_selector).forEach(initWidget);
}


whenDomReady(initWidgets);
emitters.dom.on('mutate', initWidgets);
