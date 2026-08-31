from .models import Notification


def create_notification(recipient, sender, notification_type, title, message, related_url=''):
    """Create a notification for a user."""
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message,
        related_url=related_url,
    )
