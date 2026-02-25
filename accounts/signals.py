from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile,AdminProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_based_on_role(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            AdminProfile.objects.create(user=instance)
        else:
            UserProfile.objects.create(user=instance)