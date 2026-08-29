from django.contrib import admin
from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'school_number', 'region', 'district', 'is_active']
    list_filter = ['region', 'district', 'is_active']
    search_fields = ['name', 'school_number']
