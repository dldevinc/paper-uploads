from paper_uploads.views.collection import UploadFileView


class UploadCustomCollectionItemView(UploadFileView):
    def get_instance(self, item_type: str, **kwargs):
        if item_type == "image":
            kwargs["user"] = self.request.user
        return super().get_instance(item_type, **kwargs)
