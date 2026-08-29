from django.db import models


class AnalyticsSnapshot(models.Model):
    snapshot_date = models.DateField(auto_now_add=True)
    total_books = models.PositiveIntegerField(default=0)
    available_books = models.PositiveIntegerField(default=0)
    issued_to_teachers = models.PositiveIntegerField(default=0)
    issued_to_students = models.PositiveIntegerField(default=0)
    returned_books = models.PositiveIntegerField(default=0)
    lost_books = models.PositiveIntegerField(default=0)
    damaged_books = models.PositiveIntegerField(default=0)
    written_off_books = models.PositiveIntegerField(default=0)

    region = models.ForeignKey('geography.Region', on_delete=models.CASCADE, null=True, blank=True, related_name='analytics')
    district = models.ForeignKey('geography.District', on_delete=models.CASCADE, null=True, blank=True, related_name='analytics')
    jamoat = models.ForeignKey('geography.Jamoat', on_delete=models.CASCADE, null=True, blank=True, related_name='analytics')
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, null=True, blank=True, related_name='analytics')

    class Meta:
        verbose_name = 'Analytics Snapshot'
        verbose_name_plural = 'Analytics Snapshots'
        ordering = ['-snapshot_date']

    def __str__(self):
        return f'Snapshot {self.snapshot_date}'
