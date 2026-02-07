from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import timedelta
from django.utils import timezone

class UserDevice(models.Model):
    """
    Device model with permissions
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=100, unique=True)
    device_name = models.CharField(max_length=200)
    read_permission = models.BooleanField(default=True)
    write_permission = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_login']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
    
    def can_read(self):
        """Check if device can read"""
        return self.read_permission and self.is_active and not self.is_expired()
    
    def can_write(self):
        """Check if device can write (requires read permission first)"""
        return self.write_permission and self.can_read()
    
    def is_expired(self):
        """Check if device session expired (older than 7 days)"""
        return timezone.now() - self.last_login > timedelta(days=7)
    
    def mark_inactive(self):
        """Mark device as inactive"""
        self.is_active = False
        self.save()
    
    def update_last_login(self):
        """Update last login time"""
        self.last_login = timezone.now()
        self.save()
    
    @classmethod
    def get_or_create_device(cls, user, device_name, request):
        """
        Get existing active device or create new one
        Returns: (device, created)
        """
        # Try to find existing active device for this user+browser
        existing = cls.objects.filter(
            user=user,
            device_name=device_name,
            is_active=True
        ).first()
        
        if existing:
            existing.update_last_login()
            return existing, False
        
        # Create new device
        device_id = str(uuid.uuid4())
        is_admin = user.is_superuser or user.is_staff
        
        device = cls.objects.create(
            user=user,
            device_id=device_id,
            device_name=device_name,
            read_permission=True,
            write_permission=is_admin,  # Admin gets write by default
            is_active=True
        )
        
        return device, True
    
    @classmethod
    def cleanup_old_devices(cls, days=7):
        """Clean up devices older than X days"""
        cutoff = timezone.now() - timedelta(days=days)
        cls.objects.filter(last_login__lt=cutoff, is_active=True).update(is_active=False)