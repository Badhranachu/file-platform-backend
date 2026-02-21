from django.db import models

# Create your models here.


from django.db import models
from django.conf import settings

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
        related_name="subfolders"
    )
    is_public = models.BooleanField(default=True)
    is_listed_in_feed = models.BooleanField(default=False)
    password = models.CharField(max_length=255, blank=True, null=True)  # 🔥 NEW
    created_at = models.DateTimeField(auto_now_add=True)

class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/")
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)