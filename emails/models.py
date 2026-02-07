from django.db import models
from django.contrib.auth.models import User

class EmailMessage(models.Model):
    """
    Email message model
    """
    sender = models.ForeignKey(
        User, 
        related_name='sent_emails', 
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        User, 
        related_name='received_emails', 
        on_delete=models.CASCADE
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Email'
        verbose_name_plural = 'Emails'
    
    def __str__(self):
        return f"{self.subject[:50]}..."
    
    def mark_as_read(self):
        """Mark email as read"""
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])
    
    def delete_email(self, user):
        """Soft delete email for a user"""
        if user == self.sender or user == self.recipient:
            self.is_deleted = True
            self.save(update_fields=['is_deleted'])
            return True
        return False
    
    def can_view(self, user):
        """Check if user can view this email"""
        return (user == self.sender or user == self.recipient) and not self.is_deleted
    
    @classmethod
    def get_inbox_for_user(cls, user):
        """Get all emails in user's inbox"""
        return cls.objects.filter(
            recipient=user,
            is_deleted=False
        )
    
    @classmethod
    def get_sent_for_user(cls, user):
        """Get all emails sent by user"""
        return cls.objects.filter(
            sender=user,
            is_deleted=False
        )