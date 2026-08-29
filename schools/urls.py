from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('', views.school_list_view, name='school_list'),
    path('create/', views.school_create_view, name='school_create'),
    path('<int:pk>/', views.school_detail_view, name='school_detail'),
    path('<int:pk>/edit/', views.school_edit_view, name='school_edit'),
    path('<int:pk>/toggle-active/', views.school_toggle_active_view, name='school_toggle_active'),
]
