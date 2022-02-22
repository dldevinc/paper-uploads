from paper_uploads.views.collection import UploadFileView

from .models import ImageItem


class UploadCustomCollectionItemView(UploadFileView):
    def get_instance(self, item_type: str, **kwargs):
        instance = super().get_instance(item_type, **kwargs)
        if isinstance(instance, ImageItem):
            instance.user = self.request.user
        return instance
