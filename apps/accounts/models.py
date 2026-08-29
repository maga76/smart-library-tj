from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
        DISTRICT_CHAIRMAN = 'DISTRICT_CHAIRMAN', _('District Chairman')
        JAMOAT_CHAIRMAN = 'JAMOAT_CHAIRMAN', _('Jamoat Chairman')
        SCHOOL_DIRECTOR = 'SCHOOL_DIRECTOR', _('School Director')
        LIBRARIAN = 'LIBRARIAN', _('Librarian')
        CLASS_TEACHER = 'CLASS_TEACHER', _('Class Teacher')
        STUDENT = 'STUDENT', _('Student')

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    region = models.ForeignKey(
        'geography.Region', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users'
    )
    district = models.ForeignKey(
        'geography.District', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users'
    )
    jamoat = models.ForeignKey(
        'geography.Jamoat', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users'
    )
    school = models.ForeignKey(
        'schools.School', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'

    @property
    def dashboard_url(self):
        urls = {
            self.Role.SUPER_ADMIN: '/dashboard/super-admin/',
            self.Role.DISTRICT_CHAIRMAN: '/dashboard/district/',
            self.Role.JAMOAT_CHAIRMAN: '/dashboard/jamoat/',
            self.Role.SCHOOL_DIRECTOR: '/dashboard/director/',
            self.Role.LIBRARIAN: '/dashboard/librarian/',
            self.Role.CLASS_TEACHER: '/dashboard/teacher/',
            self.Role.STUDENT: '/dashboard/student/',
        }
        return urls.get(self.role, '/login/')
