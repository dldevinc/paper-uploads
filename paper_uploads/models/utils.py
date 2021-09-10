import datetime
import posixpath


def generate_filename(instance, filename):
    upload_to = instance.get_file_folder()
    dirname = datetime.datetime.now().strftime(upload_to)
    return posixpath.join(dirname, filename)
