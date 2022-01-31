import warnings


class InvalidParameter(Exception):
    def __init__(self, value):
        self.value = value
        super().__init__()


class InvalidContentType(InvalidParameter):
    pass


class InvalidItemType(InvalidParameter):
    pass


class InvalidObjectId(InvalidParameter):
    pass


class ContinueUpload(Exception):
    pass


class UncompleteUpload(Exception):
    pass


class InvalidUUID(Exception):
    def __init__(self, value):
        self.value = value
        super().__init__()


class InvalidChunking(Exception):
    pass


class UnsupportedResource(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class UnsupportedFileError(UnsupportedResource):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "UnsupportedFileError is deprecated in favor of UnsupportedResource",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
