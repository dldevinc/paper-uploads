import os
from decimal import Decimal

from django.utils.crypto import get_random_string
from examples.fields.standard.models import Page

from paper_uploads.models import UploadedSVGFile

from .. import utils
from ..dummy import *
from ..mixins import BacklinkModelTestMixin
from .test_dummy import TestFileFieldResource as BaseTestFileFieldResource
from .test_dummy import TestFileFieldResourceAttach as BaseTestFileFieldResourceAttach
from .test_dummy import TestFileFieldResourceDelete as BaseTestFileFieldResourceDelete
from .test_dummy import TestFileFieldResourceEmpty as BaseTestFileFieldResourceEmpty
from .test_dummy import TestFileFieldResourceRename as BaseTestFileFieldResourceRename


class TestUploadedSVGFile(BacklinkModelTestMixin, BaseTestFileFieldResource):
    resource_class = UploadedSVGFile
    resource_attachment = MEDITATION_FILEPATH
    resource_basename = "Meditation"
    resource_extension = "svg"
    resource_name = "files/%Y/%m/%d/Meditation{suffix}.svg"
    resource_size = 47193
    resource_checksum = "7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d"
    resource_mimetype = "image/svg+xml"
    resource_field_name = "file"
    owner_fieldname = "svg"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class(
            title="SVG image",
            description="Example SVG image",
        )
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
            assert fp.read(5) == b'<?xml'

    def test_width(self, storage):
        assert storage.resource.width == Decimal("626")

    def test_height(self, storage):
        assert storage.resource.height == Decimal("660.0532")

    def test_ratio(self, storage):
        assert storage.resource.ratio == Decimal("0.9484084")

    def test_hw_ratio(self, storage):
        assert storage.resource.hw_ratio == Decimal("1.05439808")

    def test_srcset(self, storage):
        assert utils.match_path(
            storage.resource.srcset,
            "/media/{} 626w".format(self.resource_name),
        )

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
                "width": "626",
                "height": "660.0532",
                "title": "SVG image",
                "description": "Example SVG image",
                "url": storage.resource.url,
                "file_info": "(svg, 47.2\xa0KB)",
                "created": storage.resource.created_at.isoformat(),
                "modified": storage.resource.modified_at.isoformat(),
                "uploaded": storage.resource.uploaded_at.isoformat(),
            },
            ignore={"id"}
        )

    def test_get_content(self, storage):
        content = storage.resource.get_content()
        assert "<svg" in content


class TestUploadedFileAttach(BaseTestFileFieldResourceAttach):
    resource_class = UploadedSVGFile
    resource_attachment = MEDITATION_FILEPATH
    resource_basename = "Meditation"
    resource_extension = "svg"
    resource_size = 47193
    resource_checksum = "7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d"
    resource_mimetype = "image/svg+xml"


class TestUploadedFileRename(BacklinkModelTestMixin, BaseTestFileFieldResourceRename):
    resource_class = UploadedSVGFile
    resource_attachment = MEDITATION_FILEPATH
    resource_size = 47193
    resource_checksum = "7bdd00038ba30f3a691971de5a32084b18f4af93d4bb91616419ae3828e0141d"
    resource_mimetype = "image/svg+xml"
    owner_fieldname = "svg"
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
    resource_class = UploadedSVGFile
    resource_attachment = MEDITATION_FILEPATH
    owner_fieldname = "svg"
    owner_model = Page

    @classmethod
    def init_class(cls, storage):
        storage.resource = cls.resource_class()
        storage.resource.set_owner_field(cls.owner_model, cls.owner_fieldname)
        storage.resource.attach(
            cls.resource_attachment,
            name="file_{}.svg".format(get_random_string(6))
        )
        storage.resource.save()

        storage.old_resource_name = storage.resource.name

        storage.resource.delete_file()
        yield

        storage.resource.delete()


class TestUploadedFileEmpty(BaseTestFileFieldResourceEmpty):
    resource_class = UploadedSVGFile
