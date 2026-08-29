from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('district/', views.district_dashboard, name='district_dashboard'),
    path('jamoat/', views.jamoat_dashboard, name='jamoat_dashboard'),
    path('director/', views.director_dashboard, name='director_dashboard'),
    path('librarian/', views.librarian_dashboard, name='librarian_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('analytics/', views.analytics_view, name='analytics_view'),
]
