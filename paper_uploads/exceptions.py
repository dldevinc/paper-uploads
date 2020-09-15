class InvalidRequest(Exception):
    pass


class InvalidContentType(InvalidRequest):
    pass


class InvalidObjectId(InvalidRequest):
    pass


class InstanceNotFound(InvalidRequest):
    pass


class InvalidChunking(InvalidRequest):
    pass


class InvalidUUID(InvalidRequest):
    def __init__(self, value):
        self.value = value
        super().__init__()


class ContinueUpload(Exception):
    pass


class UncompleteUpload(Exception):
    pass


class AjaxFormError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class UnsupportedFileError(Exception):
    """
    Исключение, вызываемое внутри метода `attach_file` при обнаружении
    ситуации, когда файл не может быть представлен текущей моделью.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FileNotFoundError(Exception):
    def __init__(self, file):
        self.file = file
        self.name = file.name
        super().__init__()
