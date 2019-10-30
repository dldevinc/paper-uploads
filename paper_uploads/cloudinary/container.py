import hashlib
import requests
import cloudinary.api
import cloudinary.uploader
import cloudinary.exceptions
from requests.models import ITER_CHUNK_SIZE
from django.core.files import File
from django.core.exceptions import ValidationError
from ..logging import logger
from ..models.containers import ContainerMixinBase, ProxyAttributesContainerMixin


class CloudinaryContainerMixin(ProxyAttributesContainerMixin, ContainerMixinBase):
    PROXY_FILE_ATTRIBUTES = {
        'url',
    }

    cloudinary_type = 'upload'
    cloudinary_resource_type = 'raw'

    def get_public_id(self) -> str:
        """
        Для картинок и видео public_id не учитывает расширения.
        Для raw - учитывает.
        """
        if self.cloudinary_resource_type in {'image', 'video'}:
            return self.file.public_id
        elif self.cloudinary_resource_type == 'raw':
            public_id = self.file.public_id
            if self.file.format:
                public_id += '.' + self.file.format
            return public_id

    def _attach_file(self, file: File, **options):
        if file.size >= 100 * 1024 * 1024:
            upload = cloudinary.uploader.upload_large
        else:
            upload = cloudinary.uploader.upload

        cloudinary_options = options.get('cloudinary', {})

        try:
            result = upload(
                file,
                type=self.cloudinary_type,
                resource_type=self.cloudinary_resource_type,
                **cloudinary_options
            )
        except cloudinary.exceptions.Error as e:
            raise ValidationError(*e.args)

        resource = cloudinary.CloudinaryResource(
            result["public_id"], version=str(result["version"]),
            format=result.get("format"), type=result["type"],
            resource_type=result["resource_type"], metadata=result
        )
        self.file = resource
        return result

    def rename_file(self, new_name: str):
        try:
            result = cloudinary.uploader.rename(
                self.get_public_id(),
                new_name,
                type=self.cloudinary_type,
                resource_type=self.cloudinary_resource_type
            )
        except cloudinary.exceptions.Error:
            logger.exception("Couldn't rename Cloudinary file: {}".format(self.get_file_name()))
            return
        else:
            resource = cloudinary.CloudinaryResource(
                result["public_id"], version=str(result["version"]),
                format=result.get("format"), type=result["type"],
                resource_type=result["resource_type"], metadata=result
            )
            self.file = resource

    def _delete_file(self):
        if self.file:
            try:
                result = cloudinary.uploader.destroy(
                    self.get_public_id(),
                    type=self.cloudinary_type,
                    resource_type=self.cloudinary_resource_type
                )
            except cloudinary.exceptions.Error:
                logger.exception("Couldn't delete Cloudinary file: {}".format(self.get_file_name()))
                return

            status = result.get('result')
            if status == 'ok':
                pass
            else:
                logger.warning(
                    "Unable to delete Cloudinary file `{}`: {}".format(
                        self.get_file_name(),
                        status
                    )
                )
            self.file = None

    def get_file_name(self) -> str:
        filename = self.file.public_id
        if self.file.format:
            filename += '.' + self.file.format
        return filename

    def get_file_size(self) -> int:
        response = requests.head(self.get_file_url())
        response.raise_for_status()
        return int(response.headers['content-length'])

    def get_file_url(self) -> str:
        return self.file.url

    def file_exists(self) -> bool:
        if self.file is None:
            return False
        response = requests.head(self.get_file_url())
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def get_file_hash(self) -> str:
        """
        Generate a SHA-1 hash from a file's contents
        """
        response = requests.get(self.get_file_url(), stream=True)
        response.raise_for_status()
        sha1 = hashlib.sha1()
        for chunk in response.iter_content(chunk_size=ITER_CHUNK_SIZE):
            sha1.update(chunk)
        return sha1.hexdigest()
