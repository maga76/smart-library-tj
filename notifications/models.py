from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        BOOK_REQUEST = 'BOOK_REQUEST', _('Book Request')
        RETURN_REQUEST = 'RETURN_REQUEST', _('Return Request')
        REQUEST_APPROVED = 'REQUEST_APPROVED', _('Request Approved')
        REQUEST_REJECTED = 'REQUEST_REJECTED', _('Request Rejected')
        GENERAL = 'GENERAL', _('General')

    recipient = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='notifications'
    )
    sender = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices, default=NotificationType.GENERAL
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient.get_full_name()} - {self.title}'

    @property
    def icon(self):
        icons = {
            self.NotificationType.BOOK_REQUEST: 'bi-envelope-paper',
            self.NotificationType.RETURN_REQUEST: 'bi-arrow-counterclockwise',
            self.NotificationType.REQUEST_APPROVED: 'bi-check-circle',
            self.NotificationType.REQUEST_REJECTED: 'bi-x-circle',
            self.NotificationType.GENERAL: 'bi-bell',
        }
        return icons.get(self.notification_type, 'bi-bell')

    @property
    def color(self):
        colors = {
            self.NotificationType.BOOK_REQUEST: 'text-primary',
            self.NotificationType.RETURN_REQUEST: 'text-success',
            self.NotificationType.REQUEST_APPROVED: 'text-success',
            self.NotificationType.REQUEST_REJECTED: 'text-danger',
            self.NotificationType.GENERAL: 'text-muted',
        }
        return colors.get(self.notification_type, 'text-muted')
