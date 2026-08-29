from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('', views.SchoolListView.as_view(), name='school_list'),
    path('create/', views.SchoolCreateView.as_view(), name='school_create'),
    path('<int:pk>/', views.SchoolDetailView.as_view(), name='school_detail'),
    path('<int:pk>/edit/', views.SchoolEditView.as_view(), name='school_edit'),
    path('<int:pk>/toggle-active/', views.SchoolToggleActiveView.as_view(), name='school_toggle_active'),
]
