from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list_view, name='transaction_list'),
    path('issue-teacher/', views.issue_to_teacher_view, name='issue_to_teacher'),
    path('issue-student/', views.issue_to_student_view, name='issue_to_student'),
    path('return-student/', views.return_from_student_view, name='return_from_student'),
    path('return-teacher/', views.return_from_teacher_view, name='return_from_teacher'),
    path('report-lost/', views.report_lost_view, name='report_lost'),
    path('report-damaged/', views.report_damaged_view, name='report_damaged'),
    path('write-off/<int:pk>/', views.write_off_view, name='write_off'),
]
