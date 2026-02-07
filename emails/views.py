from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserDevice
from .models import EmailMessage

def get_current_device(request):
    """Helper to get current device with validation"""
    device_id = request.session.get('device_id')
    
    if not device_id:
        return None, "No active device found. Please login again."
    
    try:
        device = UserDevice.objects.get(
            device_id=device_id,
            user=request.user,
            is_active=True
        )
        return device, None
    except UserDevice.DoesNotExist:
        return None, "Device not found or inactive. Please login again."

@login_required
def inbox_view(request):
    """Display user's inbox"""
    device, error = get_current_device(request)
    
    if error:
        messages.error(request, error)
        return redirect('accounts:login')
    
    if not device.can_read():
        messages.error(request, "❌ You don't have permission to read emails on this device.")
        return render(request, 'emails/error.html', {
            'error': 'Read permission denied',
            'device': device
        })
    
    emails = EmailMessage.get_inbox_for_user(request.user)
    
    return render(request, 'emails/inbox.html', {
        'emails': emails,
        'device': device,
        'can_write': device.can_write(),
        'page_title': 'Inbox',
        'is_inbox': True,
    })

@login_required
def sent_view(request):
    """Display user's sent emails"""
    device, error = get_current_device(request)
    
    if error:
        messages.error(request, error)
        return redirect('accounts:login')
    
    if not device.can_read():
        messages.error(request, "❌ You don't have permission to read emails on this device.")
        return render(request, 'emails/error.html', {
            'error': 'Read permission denied',
            'device': device
        })
    
    emails = EmailMessage.get_sent_for_user(request.user)
    
    return render(request, 'emails/inbox.html', {
        'emails': emails,
        'device': device,
        'can_write': device.can_write(),
        'page_title': 'Sent',
        'is_sent': True,
    })

@login_required
def email_detail_view(request, email_id):
    """View individual email"""
    device, error = get_current_device(request)
    
    if error:
        messages.error(request, error)
        return redirect('accounts:login')
    
    if not device.can_read():
        messages.error(request, "❌ You don't have permission to read emails on this device.")
        return render(request, 'emails/error.html', {
            'error': 'Read permission denied',
            'device': device
        })
    
    email = get_object_or_404(EmailMessage, id=email_id)
    
    # Check permission to view
    if not email.can_view(request.user):
        messages.error(request, "❌ You don't have permission to view this email.")
        return redirect('emails:inbox')
    
    # Mark as read if recipient
    if email.recipient == request.user:
        email.mark_as_read()
    
    return render(request, 'emails/email_detail.html', {
        'email': email,
        'device': device,
        'can_write': device.can_write(),
    })

@login_required
def compose_view(request):
    """Compose new email"""
    device, error = get_current_device(request)
    
    if error:
        messages.error(request, error)
        return redirect('accounts:login')
    
    if not device.can_write():
        messages.error(request, "❌ You don't have permission to write emails on this device.")
        return render(request, 'emails/error.html', {
            'error': 'Write permission denied',
            'device': device,
            'show_admin_link': request.user.is_superuser or request.user.is_staff
        })
    
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient', '').strip()
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        
        # Validate inputs
        if not recipient_username:
            messages.error(request, "❌ Please enter recipient's username.")
        elif not subject:
            messages.error(request, "❌ Please enter subject.")
        elif not body:
            messages.error(request, "❌ Please enter message body.")
        else:
            try:
                recipient = User.objects.get(username=recipient_username)
                
                # Check if sending to self
                if recipient == request.user:
                    messages.error(request, "❌ You cannot send email to yourself.")
                else:
                    # Create email
                    EmailMessage.objects.create(
                        sender=request.user,
                        recipient=recipient,
                        subject=subject,
                        body=body
                    )
                    
                    messages.success(request, f"✅ Email sent successfully to {recipient_username}!")
                    return redirect('emails:sent')
                    
            except User.DoesNotExist:
                messages.error(request, f"❌ User '{recipient_username}' not found.")
    
    return render(request, 'emails/compose.html', {
        'device': device,
        'can_write': device.can_write(),
    })

@login_required
def reply_view(request, email_id):
    """Reply to an email"""
    device, error = get_current_device(request)
    
    if error:
        messages.error(request, error)
        return redirect('accounts:login')
    
    if not device.can_write():
        messages.error(request, "❌ You don't have permission to write emails on this device.")
        return render(request, 'emails/error.html', {
            'error': 'Write permission denied',
            'device': device
        })
    
    # Get original email
    original = get_object_or_404(
        EmailMessage, 
        id=email_id,
        is_deleted=False,
        recipient=request.user  # Only recipient can reply
    )
    
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        
        if body:
            # Create reply
            EmailMessage.objects.create(
                sender=request.user,
                recipient=original.sender,
                subject=f"Re: {original.subject}",
                body=body
            )
            
            messages.success(request, "✅ Reply sent successfully!")
            return redirect('emails:inbox')
        else:
            messages.error(request, "❌ Please enter your reply message.")
    
    # Pre-fill reply with quoted text
    quoted_text = f"\n\n--- Original Message ---\nFrom: {original.sender.username}\nDate: {original.timestamp.strftime('%B %d, %Y at %H:%M')}\nSubject: {original.subject}\n\n{original.body}"
    
    return render(request, 'emails/compose.html', {
        'original': original,
        'quoted_text': quoted_text,
        'device': device,
        'can_write': device.can_write(),
        'is_reply': True,
    })

@login_required
def delete_email_view(request, email_id):
    """Delete an email (soft delete)"""
    device, error = get_current_device(request)
    
    if error:
        messages.error(request, error)
        return redirect('accounts:login')
    
    if not device.can_read():
        messages.error(request, "❌ You don't have permission to manage emails.")
        return redirect('emails:inbox')
    
    email = get_object_or_404(EmailMessage, id=email_id)
    
    if email.delete_email(request.user):
        messages.success(request, "✅ Email deleted successfully.")
    else:
        messages.error(request, "❌ You don't have permission to delete this email.")
    
    # Redirect to appropriate page
    if email.sender == request.user:
        return redirect('emails:sent')
    else:
        return redirect('emails:inbox')

@login_required
def mark_as_read_view(request, email_id):
    """Mark email as read"""
    device, error = get_current_device(request)
    
    if error:
        return JsonResponse({'error': error}, status=400)
    
    if not device.can_read():
        return JsonResponse({'error': 'Read permission denied'}, status=403)
    
    email = get_object_or_404(EmailMessage, id=email_id, recipient=request.user)
    email.mark_as_read()
    
    return JsonResponse({'success': True})