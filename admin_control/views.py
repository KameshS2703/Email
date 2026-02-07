from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.contrib import messages

from django.contrib.auth.models import User
from accounts.models import UserDevice
from email_system.device_manager import DeviceManager

def is_admin_user(user):
    """Check if user is admin (superuser or staff)"""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin_user)
def device_management_view(request):
    """
    Admin view to manage device permissions
    """
    device_manager = DeviceManager()
    
    if request.method == 'POST':
        # Process form submission
        device_ids = request.POST.getlist('device_ids')
        
        for device_id in device_ids:
            read_perm = request.POST.get(f'read_{device_id}') == 'true'
            write_perm = request.POST.get(f'write_{device_id}') == 'true'
            
            # Update permissions
            device_manager.update_permission(
                device_id,
                read_permission=read_perm,
                write_permission=write_perm
            )
        
        messages.success(request, '✅ Device permissions updated successfully!')
        return redirect('admin_control:device_management')
    
    # GET request - show device list
    all_devices = device_manager.list_devices()
    
    # Combine JSON and DB data
    devices_with_info = []
    for device in all_devices:
        # Try to get user info
        user_info = None
        try:
            user_info = User.objects.get(id=device['user_id'])
        except User.DoesNotExist:
            user_info = None
        
        devices_with_info.append({
            'device_id': device['device_id'],
            'device_name': device['device_name'],
            'user_id': device['user_id'],
            'read_permission': device.get('read_permission', True),
            'write_permission': device.get('write_permission', False),
            'is_active': device.get('is_active', True),
            'user_info': user_info,
        })
    
    context = {
        'devices': devices_with_info,
        'device_count': len(all_devices),
    }
    
    return render(request, 'admin_control/device_management.html', context)

@login_required
@user_passes_test(is_admin_user)
def force_logout_device(request, device_id):
    """
    Force logout a specific device (admin only)
    """
    device_manager = DeviceManager()
    
    # Remove from JSON manager
    success = device_manager.remove_device(device_id)
    
    # Update database
    UserDevice.objects.filter(device_id=device_id).update(is_active=False)
    
    if success:
        messages.success(request, f'✅ Device {device_id[:10]}... has been logged out')
    else:
        messages.error(request, f'❌ Device {device_id[:10]}... not found')
    
    return redirect('admin_control:device_management')