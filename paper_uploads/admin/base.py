from django.contrib import admin


class UploadedFileBase(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def log_addition(self, *args, **kwargs):
        return

    def log_change(self, *args, **kwargs):
        return

    def log_deletion(self, *args, **kwargs):
        return
