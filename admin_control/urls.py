from django.urls import path
from . import views

app_name = 'admin_control'

urlpatterns = [
    path('devices/', views.device_management_view, name='device_management'),
    path('devices/logout/<str:device_id>/', views.force_logout_device, name='force_logout'),
]