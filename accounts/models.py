from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'   # ✅ add this
    )    
    is_public = models.BooleanField(default=True)
    public_password = models.CharField(max_length=255, blank=True, null=True)
    profile_photo = models.ImageField(upload_to="profiles/", null=True, blank=True)
    follows = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followers",
        blank=True,
    )

    REQUIRED_FIELDS = ['email', 'role']
    def __str__(self):
        name = self.get_full_name()
        if name:
            return f"{name} ({self.role})"
        return f"{self.username} ({self.role})"




class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)


class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admin_code = models.CharField(max_length=100, blank=True, null=True)


class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
