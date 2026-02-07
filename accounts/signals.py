from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserDevice

@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """Handle user save events"""
    if created and instance.is_superuser:
        # Ensure superuser is also staff
        instance.is_staff = True
        instance.save(update_fields=['is_staff'])