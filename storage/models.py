import uuid

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Folder(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subfolders",
    )
    is_public = models.BooleanField(default=True)
    is_listed_in_feed = models.BooleanField(default=True)
    folder_code = models.CharField(max_length=12, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    liked_by = models.ManyToManyField(User, blank=True, related_name="liked_folders")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.folder_code:
            self.folder_code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
            code = uuid.uuid4().hex[:8].upper()
            if not Folder.objects.filter(folder_code=code).exists():
                return code


class FolderView(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="folder_views")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("folder", "user")


class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/")
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class FolderComment(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="comments")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class FileComment(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name="comments")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class FolderMessage(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="messages")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
