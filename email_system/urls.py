from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # FIX: Smart redirect - if logged in, go to inbox, else login
    path('', lambda request: RedirectView.as_view(
        pattern_name='emails:inbox' if request.user.is_authenticated else 'accounts:login',
        permanent=False
    )(request)),
    
    path('accounts/', include('accounts.urls')),
    path('emails/', include('emails.urls')),
]

# Customize admin site
admin.site.site_header = "📱 Device Permission Manager"
admin.site.site_title = "Device Management System"
admin.site.index_title = "Manage Device Permissions"