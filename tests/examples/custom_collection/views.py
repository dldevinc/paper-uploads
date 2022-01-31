from paper_uploads.views.collection import CreateCollectionView


class CreateCustomCollectionView(CreateCollectionView):
    def get_instance(self):
        instance = super().get_instance()
        instance.user = self.request.user
        return instance
