from django.db import models


class School(models.Model):
    name = models.CharField(max_length=300)
    school_number = models.CharField(max_length=50, unique=True)
    region = models.ForeignKey('geography.Region', on_delete=models.CASCADE, related_name='schools')
    district = models.ForeignKey('geography.District', on_delete=models.CASCADE, related_name='schools')
    jamoat = models.ForeignKey('geography.Jamoat', on_delete=models.CASCADE, related_name='schools')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    student_capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (#{self.school_number})'
