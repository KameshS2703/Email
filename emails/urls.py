from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    path('inbox/', views.inbox_view, name='inbox'),
    path('sent/', views.sent_view, name='sent'),
    path('compose/', views.compose_view, name='compose'),
    path('email/<int:email_id>/', views.email_detail_view, name='detail'),
    path('reply/<int:email_id>/', views.reply_view, name='reply'),
    path('delete/<int:email_id>/', views.delete_email_view, name='delete'),
    path('mark-read/<int:email_id>/', views.mark_as_read_view, name='mark_read'),
]