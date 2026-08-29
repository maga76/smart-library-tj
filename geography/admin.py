from django.contrib import admin
from .models import Region, District, Jamoat


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name_ru', 'name_tj', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name_ru', 'name_tj', 'code']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name_ru', 'name_tj', 'code', 'region', 'is_active']
    list_filter = ['region', 'is_active']
    search_fields = ['name_ru', 'name_tj', 'code']


@admin.register(Jamoat)
class JamoatAdmin(admin.ModelAdmin):
    list_display = ['name_ru', 'name_tj', 'district', 'is_active']
    list_filter = ['district', 'is_active']
    search_fields = ['name_ru', 'name_tj']
