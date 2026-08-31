from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    # Books (Catalog)
    path('books/', views.BookListView.as_view(), name='book_list'),
    path('books/create/', views.BookCreateView.as_view(), name='book_create'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('books/<int:pk>/edit/', views.BookEditView.as_view(), name='book_edit'),

    # Book Copies
    path('copies/', views.CopyListView.as_view(), name='copy_list'),
    path('copies/create/', views.CopyCreateView.as_view(), name='copy_create'),
    path('copies/<int:pk>/', views.CopyDetailView.as_view(), name='copy_detail'),
    path('scan/', views.CopyScanView.as_view(), name='copy_scan'),

    # Academic Years & Classes
    path('years/', views.AcademicYearListView.as_view(), name='academic_year_list'),
    path('years/create/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('classrooms/', views.ClassroomListView.as_view(), name='classroom_list'),
    path('classrooms/create/', views.ClassroomCreateView.as_view(), name='classroom_create'),
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('assignments/', views.TeacherAssignmentListView.as_view(), name='teacher_assignment_list'),

    # Book Requests
    path('requests/', views.BookRequestListView.as_view(), name='book_request_list'),
    path('requests/create/', views.BookRequestCreateView.as_view(), name='book_request_create'),
    path('requests/<int:pk>/approve/', views.BookRequestApproveView.as_view(), name='book_request_approve'),

    # Book Issues (Lost / Damaged)
    path('issues/', views.BookIssueListView.as_view(), name='book_issue_list'),
    path('issues/create/', views.BookIssueCreateView.as_view(), name='book_issue_create'),
    path('issues/<int:pk>/confirm/', views.BookIssueConfirmView.as_view(), name='book_issue_confirm'),

    # Student Book Requests
    path('student-requests/', views.StudentBookRequestListView.as_view(), name='student_book_request_list'),
    path('student-requests/create/', views.StudentBookRequestCreateView.as_view(), name='student_book_request_create'),
    path('student-requests/<int:pk>/review/', views.StudentBookRequestReviewView.as_view(), name='student_book_request_review'),
]
