from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.sessions.models import Session
from django.contrib.contenttypes.models import ContentType
from .models import UserDevice

# ============================================
# HIDE UNWANTED MODELS FROM ADMIN
# ============================================

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.unregister(ContentType)

# ============================================
# DEVICE ADMIN WITH CHECKBOX EDITING
# ============================================

@admin.register(UserDevice)
class DeviceAdmin(admin.ModelAdmin):
    # List view
    list_display = [
        'username_column',
        'device_name_column', 
        'read_checkbox',
        'write_checkbox', 
        'active_checkbox',
        'last_login_column'
    ]
    
    list_editable = ['read_checkbox', 'write_checkbox', 'active_checkbox']
    
    list_filter = [
        'read_permission', 
        'write_permission', 
        'is_active',
        ('user__is_superuser', admin.BooleanFieldListFilter),
    ]
    
    search_fields = [
        'user__username',
        'device_name',
        'device_id',
    ]
    
    readonly_fields = [
        'device_id',
        'username_display',
        'device_name_display',
        'created_at',
        'last_login',
    ]
    
    list_per_page = 25
    
    # Fieldsets for edit page
    fieldsets = (
        ('Device Information', {
            'fields': (
                'username_display',
                'device_id',
                'device_name_display',
                'created_at',
                'last_login',
            )
        }),
        ('Permissions Control', {
            'fields': ('read_permission', 'write_permission', 'is_active'),
            'description': '✅ Check = Allow, ❌ Uncheck = Block'
        }),
    )
    
    # Custom columns for list view
    def username_column(self, obj):
        return obj.user.username
    username_column.short_description = '👤 Username'
    username_column.admin_order_field = 'user__username'
    
    def device_name_column(self, obj):
        return obj.device_name
    device_name_column.short_description = '📱 Device'
    
    def read_checkbox(self, obj):
        return obj.read_permission
    read_checkbox.short_description = '📖 Read'
    read_checkbox.boolean = True
    
    def write_checkbox(self, obj):
        return obj.write_permission
    write_checkbox.short_description = '✏️ Write'
    write_checkbox.boolean = True
    
    def active_checkbox(self, obj):
        return obj.is_active
    active_checkbox.short_description = '✅ Active'
    active_checkbox.boolean = True
    
    def last_login_column(self, obj):
        return obj.last_login.strftime("%b %d, %H:%M")
    last_login_column.short_description = '🕒 Last Login'
    last_login_column.admin_order_field = 'last_login'
    
    # Display fields for edit view
    def username_display(self, obj):
        return obj.user.username
    username_display.short_description = 'Username'
    
    def device_name_display(self, obj):
        return obj.device_name
    device_name_display.short_description = 'Device Name'
    
    # Bulk actions
    actions = [
        'enable_read_for_selected',
        'disable_read_for_selected',
        'enable_write_for_selected',
        'disable_write_for_selected',
        'activate_selected',
        'deactivate_selected',
        'logout_selected_devices',
    ]
    
    def enable_read_for_selected(self, request, queryset):
        count = queryset.update(read_permission=True)
        self.message_user(request, f"✅ Enabled READ permission for {count} device(s)")
    enable_read_for_selected.short_description = "📖 Enable Read"
    
    def disable_read_for_selected(self, request, queryset):
        count = queryset.update(read_permission=False)
        self.message_user(request, f"❌ Disabled READ permission for {count} device(s)")
    disable_read_for_selected.short_description = "📖 Disable Read"
    
    def enable_write_for_selected(self, request, queryset):
        count = queryset.update(write_permission=True)
        self.message_user(request, f"✅ Enabled WRITE permission for {count} device(s)")
    enable_write_for_selected.short_description = "✏️ Enable Write"
    
    def disable_write_for_selected(self, request, queryset):
        count = queryset.update(write_permission=False)
        self.message_user(request, f"❌ Disabled WRITE permission for {count} device(s)")
    disable_write_for_selected.short_description = "✏️ Disable Write"
    
    def activate_selected(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"✅ Activated {count} device(s)")
    activate_selected.short_description = "✅ Activate"
    
    def deactivate_selected(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"❌ Deactivated {count} device(s)")
    deactivate_selected.short_description = "❌ Deactivate"
    
    def logout_selected_devices(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"🚪 Logged out {count} device(s)")
    logout_selected_devices.short_description = "🚪 Logout Devices"
    
    # Prevent manual device creation
    def has_add_permission(self, request):
        return False
    
    # Clean up old devices periodically
    def changelist_view(self, request, extra_context=None):
        # Auto-cleanup old devices when admin visits
        UserDevice.cleanup_old_devices()
        return super().changelist_view(request, extra_context)