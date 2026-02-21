from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_public = models.BooleanField(default=True)
    public_password = models.CharField(max_length=255, blank=True, null=True)
    profile_photo = models.ImageField(upload_to="profiles/", null=True, blank=True)