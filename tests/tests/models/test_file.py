import os

from django.utils.crypto import get_random_string
from examples.fields.standard.models import Page

from paper_uploads.models import UploadedFile

from .. import utils
from ..dummy import *
from ..mixins import BacklinkModelTestMixin
from .test_dummy import TestFileFieldResource as BaseTestFileFieldResource
from .test_dummy import TestFileFieldResourceAttach as BaseTestFileFieldResourceAttach
from .test_dummy import TestFileFieldResourceDelete as BaseTestFileFieldResourceDelete
from .test_dummy import TestFileFieldResourceEmpty as BaseTestFileFieldResourceEmpty
from .test_dummy import TestFileFieldResourceRename as BaseTestFileFieldResourceRename


class TestUploadedFile(BacklinkModelTestMixin, BaseTestFileFieldResource):
    resource_class = UploadedFile
    resource_attachment = AUDIO_FILEPATH
    resource_basename = "Jomy QA"
    resource_extension = "mp3"
    resource_name = "files/%Y/%m/%d/Jomy_QA{suffix}.mp3"
    resource_size = 2113939
    resource_checksum = "4792f5f997f82f225299e98a1e396c7d7e479d10ffe6976f0b487361d729a15d"
    resource_mimetype = "audio/mpeg"
    resource_field_name = "file"
    owner_fieldname = "file"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(cls.resource_attachment)
        storage.resource.save()
        yield
        storage.resource.delete_file()
        storage.resource.delete()

    def test_display_name(self, storage):
        assert storage.resource.display_name == self.resource_basename

    def test_read(self, storage):
        with storage.resource.open() as fp:
            assert fp.read(5) == b'ID3\x03\x00'

    def test_as_dict(self, storage):
        utils.compare_dicts(
            storage.resource.as_dict(),
            {
                "id": 1,
                "name": self.resource_basename,
                "extension": self.resource_extension,
                "caption": "{}.{}".format(
                    self.resource_basename,
                    self.resource_extension
                ),
                "size": self.resource_size,
                "mimetype": self.resource_mimetype,
                "url": storage.resource.url,
                "file_info": "(mp3, 2.1\xa0MB)",
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id"}
        )


class TestUploadedFileAttach(BaseTestFileFieldResourceAttach):
    resource_class = UploadedFile
    resource_attachment = VIDEO_FILEPATH
    resource_basename = "video"
    resource_extension = "avi"
    resource_size = 1496576
    resource_checksum = "68f7b2833c52df5ecfcb809509677f499acbe6a93cb1df79508a8ac0e1f7e3d3"
    resource_mimetype = "video/x-msvideo"


class TestUploadedFileRename(BacklinkModelTestMixin, BaseTestFileFieldResourceRename):
    resource_class = UploadedFile
    resource_attachment = DOCUMENT_FILEPATH
    resource_size = 3028
    resource_checksum = "93e67b2ff2140c3a3f995ff9e536c4cb58b5df482dd34d47a39cf3337393ef7e"
    resource_mimetype = "application/pdf"
    owner_fieldname = "file"
    owner_model = Page
    old_name = "old_name_{}.txt".format(get_random_string(6))
    new_name = "new_name_{}.log".format(get_random_string(6))

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(cls.resource_attachment, name=cls.old_name)
        storage.resource.save()

        storage.old_modified_at = storage.resource.modified_at
        storage.old_resource_name = storage.resource.name
        storage.old_resource_path = storage.resource.path

        storage.resource.rename(cls.new_name)
        yield

        os.unlink(storage.old_resource_path)
        storage.resource.delete_file()
        storage.resource.delete()


class TestUploadedFileDelete(BacklinkModelTestMixin, BaseTestFileFieldResourceDelete):
    resource_class = UploadedFile
    resource_attachment = EXCEL_FILEPATH
    owner_fieldname = "file"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(
            cls.resource_attachment,
            name="file_{}.jpg".format(get_random_string(6))
        )
        storage.resource.save()

        storage.old_resource_name = storage.resource.name

        storage.resource.delete_file()
        yield

        storage.resource.delete()


class TestUploadedFileEmpty(BaseTestFileFieldResourceEmpty):
    resource_class = UploadedFile
