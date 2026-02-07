from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
import uuid
from .models import UserDevice

def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        messages.info(request, "You're already logged in.")
        return redirect('emails:inbox')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '✅ Account created! Please login.')
            return redirect('accounts:login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    """User login with device management"""
    # If already logged in with valid device, redirect appropriately
    if request.user.is_authenticated:
        device_id = request.session.get('device_id')
        try:
            device = UserDevice.objects.get(
                device_id=device_id,
                user=request.user,
                is_active=True
            )
            if device.can_read():
                if request.user.is_superuser or request.user.is_staff:
                    return redirect('/admin/')
                else:
                    return redirect('emails:inbox')
        except UserDevice.DoesNotExist:
            pass  # Continue to login page
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Get or create device
                device_name = request.META.get('HTTP_USER_AGENT', 'Unknown Device')[:100]
                device, created = UserDevice.get_or_create_device(user, device_name, request)
                
                if not device.is_active:
                    device.is_active = True
                    device.save()
                
                # Login user
                login(request, user)
                
                # Store device in session
                request.session['device_id'] = device.device_id
                request.session['device_name'] = device.device_name
                
                messages.success(request, f'✅ Logged in from {device.device_name}')
                
                # Redirect based on user type
                if user.is_superuser or user.is_staff:
                    return redirect('/admin/')
                else:
                    return redirect('emails:inbox')
            else:
                messages.error(request, '❌ Invalid username or password')
        else:
            messages.error(request, '❌ Invalid username or password')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    """Logout and deactivate device"""
    device_id = request.session.get('device_id')
    
    if device_id:
        try:
            device = UserDevice.objects.get(device_id=device_id, user=request.user)
            device.mark_inactive()
        except UserDevice.DoesNotExist:
            pass
    
    # Clear session
    if 'device_id' in request.session:
        del request.session['device_id']
    if 'device_name' in request.session:
        del request.session['device_name']
    
    logout(request)
    messages.success(request, '✅ Logged out successfully')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """User profile with device information"""
    device_id = request.session.get('device_id')
    current_device = None
    
    if device_id:
        current_device = UserDevice.objects.filter(
            device_id=device_id,
            user=request.user,
            is_active=True
        ).first()
    
    active_devices = UserDevice.objects.filter(
        user=request.user, 
        is_active=True
    ).order_by('-last_login')
    
    return render(request, 'accounts/profile.html', {
        'current_device': current_device,
        'active_devices': active_devices,
        'device_count': active_devices.count(),
    })

@login_required
def check_permission_api(request):
    """API to check current device permissions"""
    device_id = request.session.get('device_id')
    
    if not device_id:
        return JsonResponse({'error': 'No device found'}, status=400)
    
    try:
        device = UserDevice.objects.get(
            device_id=device_id,
            user=request.user,
            is_active=True
        )
        return JsonResponse({
            'can_read': device.can_read(),
            'can_write': device.can_write(),
            'device_name': device.device_name,
        })
    except UserDevice.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)