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
    pass


class ContinueUpload(Exception):
    pass


class UncompleteUpload(Exception):
    pass


class AjaxFormError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FileNotFoundError(Exception):
    def __init__(self, file):
        self.file = file
        self.name = file.name
        super().__init__()
