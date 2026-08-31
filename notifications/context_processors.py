from notifications.models import Notification


def notification_count(request):
    """Add unread notification count to template context for all authenticated users."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_notification_count': count}
    return {}
