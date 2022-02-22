import copy
import pickle
from examples.fields.standard.models import Page

from paper_uploads.models import UploadedFile, UploadedImage

from ..dummy import *


class TestUploadedFile:
    @classmethod
    def init_class(cls, storage):
        storage.resource = UploadedFile()
        storage.resource.set_owner_field(Page, "file")
        storage.resource.attach(EXCEL_FILEPATH)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_copy(self, storage):
        clone = copy.deepcopy(storage.resource)

        assert clone.name == storage.resource.name
        assert clone.get_owner_field() is storage.resource.get_owner_field()
        assert clone.file.storage.__class__ is storage.resource.file.storage.__class__
        assert clone.file.storage.location == storage.resource.file.storage.location

    def test_pickle(self, storage):
        clone = pickle.loads(pickle.dumps(storage.resource))

        assert clone.name == storage.resource.name
        assert clone.get_owner_field() is storage.resource.get_owner_field()
        assert clone.file.storage.__class__ is storage.resource.file.storage.__class__
        assert clone.file.storage.location == storage.resource.file.storage.location


class TestUploadedImage:
    @classmethod
    def init_class(cls, storage):
        storage.resource = UploadedImage()
        storage.resource.set_owner_field(Page, "image")
        storage.resource.attach(NASA_FILEPATH)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_copy(self, storage):
        clone = copy.deepcopy(storage.resource)

        assert clone.name == storage.resource.name
        assert clone.get_owner_field() is storage.resource.get_owner_field()
        assert clone.file.storage.__class__ is storage.resource.file.storage.__class__
        assert clone.file.storage.location == storage.resource.file.storage.location

    def test_pickle(self, storage):
        clone = pickle.loads(pickle.dumps(storage.resource))

        assert clone.name == storage.resource.name
        assert clone.get_owner_field() is storage.resource.get_owner_field()
        assert clone.file.storage.__class__ is storage.resource.file.storage.__class__
        assert clone.file.storage.location == storage.resource.file.storage.location
