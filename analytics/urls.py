from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('super-admin/', views.SuperAdminDashboardView.as_view(), name='super_admin_dashboard'),
    path('district/', views.DistrictDashboardView.as_view(), name='district_dashboard'),
    path('jamoat/', views.JamoatDashboardView.as_view(), name='jamoat_dashboard'),
    path('director/', views.DirectorDashboardView.as_view(), name='director_dashboard'),
    path('librarian/', views.LibrarianDashboardView.as_view(), name='librarian_dashboard'),
    path('teacher/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('student/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('analytics/', views.AnalyticsDetailView.as_view(), name='analytics_view'),
]
