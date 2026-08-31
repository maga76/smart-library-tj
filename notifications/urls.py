from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('read-all/', views.NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('unread-count/', views.NotificationUnreadCountView.as_view(), name='notification_unread_count'),
]
