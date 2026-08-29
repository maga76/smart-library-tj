from django.urls import path
from . import views

app_name = 'geography'

urlpatterns = [
    # Regions
    path('regions/', views.RegionListView.as_view(), name='region_list'),
    path('regions/create/', views.RegionCreateView.as_view(), name='region_create'),
    path('regions/<int:pk>/edit/', views.RegionEditView.as_view(), name='region_edit'),
    path('regions/<int:pk>/toggle-active/', views.RegionToggleActiveView.as_view(), name='region_toggle_active'),

    # Districts
    path('districts/', views.DistrictListView.as_view(), name='district_list'),
    path('districts/create/', views.DistrictCreateView.as_view(), name='district_create'),
    path('districts/<int:pk>/edit/', views.DistrictEditView.as_view(), name='district_edit'),
    path('districts/<int:pk>/toggle-active/', views.DistrictToggleActiveView.as_view(), name='district_toggle_active'),

    # Jamoats
    path('jamoats/', views.JamoatListView.as_view(), name='jamoat_list'),
    path('jamoats/create/', views.JamoatCreateView.as_view(), name='jamoat_create'),
    path('jamoats/<int:pk>/edit/', views.JamoatEditView.as_view(), name='jamoat_edit'),
    path('jamoats/<int:pk>/toggle-active/', views.JamoatToggleActiveView.as_view(), name='jamoat_toggle_active'),
]
