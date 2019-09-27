import "./file_widget";
import "./image_widget";
import "./collection_widget";

// Images
function importAll(r) {
    return r.keys().map(r);
}
importAll(require.context('../img/files/', false, /\.svg$/));
