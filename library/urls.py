from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    # Books (Catalog)
    path('books/', views.book_list_view, name='book_list'),
    path('books/create/', views.book_create_view, name='book_create'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit_view, name='book_edit'),

    # Book Copies
    path('copies/', views.copy_list_view, name='copy_list'),
    path('copies/create/', views.copy_create_view, name='copy_create'),
    path('copies/<int:pk>/', views.copy_detail_view, name='copy_detail'),
    path('scan/', views.copy_scan_view, name='copy_scan'),

    # Academic Years & Classes
    path('years/', views.academic_year_list_view, name='academic_year_list'),
    path('years/create/', views.academic_year_create_view, name='academic_year_create'),
    path('classrooms/', views.classroom_list_view, name='classroom_list'),
    path('classrooms/create/', views.classroom_create_view, name='classroom_create'),
    path('enrollments/', views.enrollment_list_view, name='enrollment_list'),
    path('assignments/', views.teacher_assignment_list_view, name='teacher_assignment_list'),

    # Book Requests
    path('requests/', views.book_request_list_view, name='book_request_list'),
    path('requests/create/', views.book_request_create_view, name='book_request_create'),
    path('requests/<int:pk>/approve/', views.book_request_approve_view, name='book_request_approve'),

    # Book Issues (Lost / Damaged)
    path('issues/', views.book_issue_list_view, name='book_issue_list'),
    path('issues/create/', views.book_issue_create_view, name='book_issue_create'),
    path('issues/<int:pk>/confirm/', views.book_issue_confirm_view, name='book_issue_confirm'),
]
