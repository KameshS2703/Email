from django.contrib import admin
from .models import EmailMessage

@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = [
        'subject_truncated',
        'sender_column',
        'recipient_column',
        'timestamp_column',
        'read_status',
    ]
    
    list_filter = [
        'read',
        'timestamp',
        'sender',
        'recipient',
    ]
    
    search_fields = [
        'subject',
        'body',
        'sender__username',
        'recipient__username',
    ]
    
    readonly_fields = [
        'sender',
        'recipient',
        'subject',
        'body',
        'timestamp',
    ]
    
    list_per_page = 30
    
    def subject_truncated(self, obj):
        return obj.subject[:50] + ('...' if len(obj.subject) > 50 else '')
    subject_truncated.short_description = 'Subject'
    
    def sender_column(self, obj):
        return obj.sender.username
    sender_column.short_description = 'From'
    sender_column.admin_order_field = 'sender__username'
    
    def recipient_column(self, obj):
        return obj.recipient.username
    recipient_column.short_description = 'To'
    recipient_column.admin_order_field = 'recipient__username'
    
    def timestamp_column(self, obj):
        return obj.timestamp.strftime("%b %d, %H:%M")
    timestamp_column.short_description = 'Sent'
    timestamp_column.admin_order_field = 'timestamp'
    
    def read_status(self, obj):
        return obj.read
    read_status.short_description = '📨 Read'
    read_status.boolean = True
    
    # Prevent modifying emails from admin
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False