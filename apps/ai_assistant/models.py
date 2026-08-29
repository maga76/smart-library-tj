from django.db import models


class AIChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    session_id = models.CharField(max_length=100)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    content = models.TextField()
    language = models.CharField(max_length=5, default='ru')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AI Chat Message'
        verbose_name_plural = 'AI Chat Messages'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'
