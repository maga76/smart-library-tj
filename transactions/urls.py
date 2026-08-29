from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('issue-teacher/', views.IssueToTeacherView.as_view(), name='issue_to_teacher'),
    path('issue-student/', views.IssueToStudentView.as_view(), name='issue_to_student'),
    path('return-student/', views.ReturnFromStudentView.as_view(), name='return_from_student'),
    path('return-teacher/', views.ReturnFromTeacherView.as_view(), name='return_from_teacher'),
    path('report-lost/', views.ReportLostView.as_view(), name='report_lost'),
    path('report-damaged/', views.ReportDamagedView.as_view(), name='report_damaged'),
    path('write-off/<int:pk>/', views.WriteOffView.as_view(), name='write_off'),
]
