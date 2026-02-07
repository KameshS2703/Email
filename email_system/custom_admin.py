from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.sessions.models import Session
from django.contrib.contenttypes.models import ContentType

class CleanAdminSite(AdminSite):
    """
    Custom admin site that shows only what we need
    """
    site_header = "📱 Device Permission Manager"
    site_title = "Device Management"
    index_title = "Manage Device Permissions"
    
    def get_app_list(self, request):
        """
        Show only Devices in admin, hide everything else
        """
        app_list = super().get_app_list(request)
        
        # Filter to show only our custom apps
        filtered_apps = []
        for app in app_list:
            if app['app_label'] == 'accounts':
                # Only show Devices model, hide auth models
                filtered_models = []
                for model in app['models']:
                    if model['object_name'] == 'UserDevice':
                        filtered_models.append(model)
                
                if filtered_models:
                    app['models'] = filtered_models
                    filtered_apps.append(app)
        
        return filtered_apps

# Create custom admin instance
custom_admin = CleanAdminSite(name='custom_admin')