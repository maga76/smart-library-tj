from django.urls import path
from . import views

app_name = 'geography'

urlpatterns = [
    # Regions
    path('regions/', views.region_list_view, name='region_list'),
    path('regions/create/', views.region_create_view, name='region_create'),
    path('regions/<int:pk>/edit/', views.region_edit_view, name='region_edit'),
    path('regions/<int:pk>/toggle-active/', views.region_toggle_active_view, name='region_toggle_active'),
    
    # Districts
    path('districts/', views.district_list_view, name='district_list'),
    path('districts/create/', views.district_create_view, name='district_create'),
    path('districts/<int:pk>/edit/', views.district_edit_view, name='district_edit'),
    path('districts/<int:pk>/toggle-active/', views.district_toggle_active_view, name='district_toggle_active'),
    
    # Jamoats
    path('jamoats/', views.jamoat_list_view, name='jamoat_list'),
    path('jamoats/create/', views.jamoat_create_view, name='jamoat_create'),
    path('jamoats/<int:pk>/edit/', views.jamoat_edit_view, name='jamoat_edit'),
    path('jamoats/<int:pk>/toggle-active/', views.jamoat_toggle_active_view, name='jamoat_toggle_active'),
]
