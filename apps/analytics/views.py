from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Count, Q, OuterRef, Subquery
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User
from apps.geography.models import Region, District, Jamoat
from apps.schools.models import School
from apps.library.models import (
    Book, BookCopy, Classroom, StudentEnrollment, TeacherClassAssignment,
    BookRequest, BookIssue, AcademicYear
)
from apps.transactions.models import BookTransaction
from apps.audit.models import AuditLog


def _copies_currently_held_by(base_qs, user, status, tx_type, holder_field):
    """Restrict a BookCopy queryset to copies whose most recent hand-off
    transaction of the given type has `holder_field` equal to user, rather
    than matching any historical transaction for that copy.
    """
    latest_tx = BookTransaction.objects.filter(
        book_copy=OuterRef('pk'),
        transaction_type=tx_type
    ).order_by('-created_at')
    return base_qs.filter(status=status).annotate(
        _current_holder_id=Subquery(latest_tx.values(holder_field)[:1])
    ).filter(_current_holder_id=user.pk)


@login_required
def dashboard_view(request):
    role = request.user.role
    urls = {
        User.Role.SUPER_ADMIN: 'analytics:super_admin_dashboard',
        User.Role.DISTRICT_CHAIRMAN: 'analytics:district_dashboard',
        User.Role.JAMOAT_CHAIRMAN: 'analytics:jamoat_dashboard',
        User.Role.SCHOOL_DIRECTOR: 'analytics:director_dashboard',
        User.Role.LIBRARIAN: 'analytics:librarian_dashboard',
        User.Role.CLASS_TEACHER: 'analytics:teacher_dashboard',
        User.Role.STUDENT: 'analytics:student_dashboard',
    }
    url_name = urls.get(role)
    if url_name:
        return redirect(url_name)
    return redirect('accounts:login')


@login_required
def super_admin_dashboard(request):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))

    context = {
        'total_regions': Region.objects.filter(is_active=True).count(),
        'total_districts': District.objects.filter(is_active=True).count(),
        'total_jamoats': Jamoat.objects.filter(is_active=True).count(),
        'total_schools': School.objects.filter(is_active=True).count(),
        'total_students': User.objects.filter(role='STUDENT', is_active=True).count(),
        'total_teachers': User.objects.filter(role='CLASS_TEACHER', is_active=True).count(),
        'total_books': BookCopy.objects.count(),
        'total_available': BookCopy.objects.filter(status__in=[BookCopy.Status.AVAILABLE, BookCopy.Status.AT_LIBRARY]).count(),
        'total_issued_teacher': BookCopy.objects.filter(status=BookCopy.Status.ISSUED_TO_TEACHER).count(),
        'total_issued_student': BookCopy.objects.filter(status=BookCopy.Status.ISSUED_TO_STUDENT).count(),
        'total_issued': BookCopy.objects.filter(status__in=[BookCopy.Status.ISSUED_TO_TEACHER, BookCopy.Status.ISSUED_TO_STUDENT]).count(),
        'total_lost': BookCopy.objects.filter(status=BookCopy.Status.LOST).count(),
        'total_damaged': BookCopy.objects.filter(status=BookCopy.Status.DAMAGED).count(),
        'total_written_off': BookCopy.objects.filter(status=BookCopy.Status.WRITTEN_OFF).count(),
        'pending_requests': BookRequest.objects.filter(status=BookRequest.Status.PENDING).count(),
        'regions_stats': Region.objects.filter(is_active=True).annotate(
            school_count=Count('districts__schools', filter=Q(districts__schools__is_active=True), distinct=True),
            book_count=Count('districts__schools__book_copies', distinct=True),
            student_count=Count('districts__schools__users', filter=Q(districts__schools__users__role='STUDENT', districts__schools__users__is_active=True), distinct=True)
        ),
        'recent_transactions': BookTransaction.objects.select_related(
            'book_copy', 'book_copy__book', 'from_user', 'to_user'
        ).order_by('-created_at')[:10],
        'recent_audit': AuditLog.objects.select_related('user').order_by('-created_at')[:8],
    }
    return render(request, 'dashboards/super_admin.html', context)


@login_required
def district_dashboard(request):
    if request.user.role != 'DISTRICT_CHAIRMAN':
        return HttpResponseForbidden(_('Access denied.'))

    district = request.user.district
    if not district:
        return render(request, 'dashboards/district.html', {'district': None, 'error': _('District is not assigned.')})

    schools = School.objects.filter(district=district, is_active=True).annotate(
        book_count=Count('book_copies', distinct=True),
        available_count=Count('book_copies', filter=Q(book_copies__status__in=['AVAILABLE', 'AT_LIBRARY']), distinct=True),
        issued_count=Count('book_copies', filter=Q(book_copies__status__in=['ISSUED_TO_TEACHER', 'ISSUED_TO_STUDENT']), distinct=True),
        lost_count=Count('book_copies', filter=Q(book_copies__status='LOST'), distinct=True),
        damaged_count=Count('book_copies', filter=Q(book_copies__status='DAMAGED'), distinct=True),
        student_count=Count('users', filter=Q(users__role='STUDENT', users__is_active=True), distinct=True)
    )

    total_books = BookCopy.objects.filter(school__district=district).count()
    total_students = User.objects.filter(role='STUDENT', school__district=district, is_active=True).count()

    # Calculate estimated deficit (assuming standard target of 10 textbooks per student)
    target_books = total_students * 10
    deficit = max(0, target_books - total_books)
    surplus = max(0, total_books - target_books)

    school_ranking = []
    for s in schools:
        target = (s.student_count or 0) * 10
        if target > 0:
            coverage_pct = min(100, round((s.book_count / target) * 100))
        else:
            coverage_pct = 100 if s.book_count else 0
        school_ranking.append({'school': s, 'coverage_pct': coverage_pct})
    school_ranking.sort(key=lambda x: x['coverage_pct'], reverse=True)

    context = {
        'district': district,
        'total_schools': schools.count(),
        'total_students': total_students,
        'total_books': total_books,
        'total_available': BookCopy.objects.filter(school__district=district, status__in=['AVAILABLE', 'AT_LIBRARY']).count(),
        'total_issued': BookCopy.objects.filter(school__district=district, status__in=['ISSUED_TO_TEACHER', 'ISSUED_TO_STUDENT']).count(),
        'total_lost': BookCopy.objects.filter(school__district=district, status=BookCopy.Status.LOST).count(),
        'total_damaged': BookCopy.objects.filter(school__district=district, status=BookCopy.Status.DAMAGED).count(),
        'deficit': deficit,
        'surplus': surplus,
        'schools': schools,
        'school_ranking': school_ranking,
    }
    return render(request, 'dashboards/district.html', context)


@login_required
def jamoat_dashboard(request):
    if request.user.role != 'JAMOAT_CHAIRMAN':
        return HttpResponseForbidden(_('Access denied.'))

    jamoat = request.user.jamoat
    if not jamoat:
        return render(request, 'dashboards/jamoat.html', {'jamoat': None, 'error': _('Jamoat is not assigned.')})

    schools = School.objects.filter(jamoat=jamoat, is_active=True).annotate(
        book_count=Count('book_copies', distinct=True),
        available_count=Count('book_copies', filter=Q(book_copies__status__in=['AVAILABLE', 'AT_LIBRARY']), distinct=True),
        issued_count=Count('book_copies', filter=Q(book_copies__status__in=['ISSUED_TO_TEACHER', 'ISSUED_TO_STUDENT']), distinct=True),
        lost_count=Count('book_copies', filter=Q(book_copies__status='LOST'), distinct=True),
        damaged_count=Count('book_copies', filter=Q(book_copies__status='DAMAGED'), distinct=True),
        student_count=Count('users', filter=Q(users__role='STUDENT', users__is_active=True), distinct=True)
    )

    total_books = BookCopy.objects.filter(school__jamoat=jamoat).count()
    total_students = User.objects.filter(role='STUDENT', school__jamoat=jamoat, is_active=True).count()
    target_books = total_students * 10
    deficit = max(0, target_books - total_books)

    school_ranking = []
    for s in schools:
        target = (s.student_count or 0) * 10
        if target > 0:
            coverage_pct = min(100, round((s.book_count / target) * 100))
        else:
            coverage_pct = 100 if s.book_count else 0
        school_ranking.append({'school': s, 'coverage_pct': coverage_pct})
    school_ranking.sort(key=lambda x: x['coverage_pct'], reverse=True)

    context = {
        'jamoat': jamoat,
        'total_schools': schools.count(),
        'total_students': total_students,
        'total_books': total_books,
        'total_available': BookCopy.objects.filter(school__jamoat=jamoat, status__in=['AVAILABLE', 'AT_LIBRARY']).count(),
        'total_issued': BookCopy.objects.filter(school__jamoat=jamoat, status__in=['ISSUED_TO_TEACHER', 'ISSUED_TO_STUDENT']).count(),
        'total_lost': BookCopy.objects.filter(school__jamoat=jamoat, status=BookCopy.Status.LOST).count(),
        'total_damaged': BookCopy.objects.filter(school__jamoat=jamoat, status=BookCopy.Status.DAMAGED).count(),
        'deficit': deficit,
        'schools': schools,
        'school_ranking': school_ranking,
    }
    return render(request, 'dashboards/jamoat.html', context)


@login_required
def director_dashboard(request):
    if request.user.role != 'SCHOOL_DIRECTOR':
        return HttpResponseForbidden(_('Access denied.'))

    school = request.user.school
    if not school:
        return render(request, 'dashboards/director.html', {'school': None, 'error': _('School is not assigned to the director.')})

    current_year = AcademicYear.objects.filter(is_current=True).first()

    classrooms = Classroom.objects.filter(school=school)
    if current_year:
        classrooms = classrooms.filter(academic_year=current_year)

    classrooms = classrooms.annotate(
        student_count=Count('enrollments', filter=Q(enrollments__is_active=True), distinct=True)
    ).order_by('grade', 'name')

    total_students_count = User.objects.filter(role='STUDENT', school=school, is_active=True).count()
    subject_rows = BookCopy.objects.filter(school=school).values('book__subject').annotate(
        copies=Count('id')
    ).order_by('-copies')[:8]
    subject_coverage = []
    for row in subject_rows:
        if total_students_count > 0:
            pct = min(100, round((row['copies'] / total_students_count) * 100))
        else:
            pct = 100 if row['copies'] else 0
        subject_coverage.append({'subject': row['book__subject'], 'copies': row['copies'], 'pct': pct})

    context = {
        'school': school,
        'current_year': current_year,
        'total_students': total_students_count,
        'subject_coverage': subject_coverage,
        'total_classrooms': classrooms.count(),
        'total_teachers': User.objects.filter(role='CLASS_TEACHER', school=school, is_active=True).count(),
        'total_books': BookCopy.objects.filter(school=school).count(),
        'total_available': BookCopy.objects.filter(school=school, status__in=[BookCopy.Status.AVAILABLE, BookCopy.Status.AT_LIBRARY]).count(),
        'total_issued_teacher': BookCopy.objects.filter(school=school, status=BookCopy.Status.ISSUED_TO_TEACHER).count(),
        'total_issued_student': BookCopy.objects.filter(school=school, status=BookCopy.Status.ISSUED_TO_STUDENT).count(),
        'total_lost': BookCopy.objects.filter(school=school, status=BookCopy.Status.LOST).count(),
        'total_damaged': BookCopy.objects.filter(school=school, status=BookCopy.Status.DAMAGED).count(),
        'pending_requests': BookRequest.objects.filter(school=school, status=BookRequest.Status.PENDING).count(),
        'classrooms': classrooms,
        'recent_requests': BookRequest.objects.filter(school=school).select_related('book').order_by('-created_at')[:5],
    }
    return render(request, 'dashboards/director.html', context)


@login_required
def librarian_dashboard(request):
    if request.user.role != 'LIBRARIAN':
        return HttpResponseForbidden(_('Access denied.'))

    school = request.user.school
    if not school:
        return render(request, 'dashboards/librarian.html', {'school': None, 'error': _('Librarian is not assigned to a school.')})

    context = {
        'school': school,
        'total_books': BookCopy.objects.filter(school=school).count(),
        'total_available': BookCopy.objects.filter(school=school, status__in=[BookCopy.Status.AVAILABLE, BookCopy.Status.AT_LIBRARY]).count(),
        'total_at_library': BookCopy.objects.filter(school=school, status=BookCopy.Status.AT_LIBRARY).count(),
        'total_issued_teacher': BookCopy.objects.filter(school=school, status=BookCopy.Status.ISSUED_TO_TEACHER).count(),
        'total_issued_student': BookCopy.objects.filter(school=school, status=BookCopy.Status.ISSUED_TO_STUDENT).count(),
        'total_lost': BookCopy.objects.filter(school=school, status=BookCopy.Status.LOST).count(),
        'total_damaged': BookCopy.objects.filter(school=school, status=BookCopy.Status.DAMAGED).count(),
        'total_written_off': BookCopy.objects.filter(school=school, status=BookCopy.Status.WRITTEN_OFF).count(),
        'pending_issues': BookIssue.objects.filter(book_copy__school=school, status=BookIssue.IssueStatus.PENDING).count(),
        'recent_transactions': BookTransaction.objects.filter(
            book_copy__school=school
        ).select_related('book_copy', 'book_copy__book', 'from_user', 'to_user').order_by('-created_at')[:10],
    }
    return render(request, 'dashboards/librarian.html', context)


@login_required
def teacher_dashboard(request):
    if request.user.role != 'CLASS_TEACHER':
        return HttpResponseForbidden(_('Access denied.'))

    user = request.user
    my_assignments = TeacherClassAssignment.objects.filter(
        teacher=user
    ).select_related('classroom', 'academic_year').order_by('-academic_year__is_current', 'classroom__grade')

    my_class_ids = my_assignments.filter(is_class_teacher=True).values_list('classroom_id', flat=True)

    # Books in teacher custody (received from librarian and not yet handed to students)
    my_copies = _copies_currently_held_by(
        BookCopy.objects.filter(school=user.school), user,
        BookCopy.Status.ISSUED_TO_TEACHER,
        BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER,
        'to_user_id'
    ).select_related('book')

    # Books currently issued to students by this teacher
    issued_to_students = _copies_currently_held_by(
        BookCopy.objects.filter(school=user.school), user,
        BookCopy.Status.ISSUED_TO_STUDENT,
        BookTransaction.TransactionType.TEACHER_TO_STUDENT,
        'from_user_id'
    ).select_related('book')

    total_students = User.objects.filter(
        role='STUDENT',
        enrollments__classroom_id__in=my_class_ids,
        enrollments__is_active=True,
        is_active=True
    ).distinct().count()

    reported_lost = BookIssue.objects.filter(reported_by=user, issue_type=BookIssue.IssueType.LOST).count()
    reported_damaged = BookIssue.objects.filter(reported_by=user, issue_type=BookIssue.IssueType.DAMAGED).count()
    books_returned = BookTransaction.objects.filter(
        to_user=user, transaction_type=BookTransaction.TransactionType.STUDENT_RETURN
    ).count()

    context = {
        'assignments': my_assignments,
        'my_classes_count': my_assignments.filter(is_class_teacher=True).count(),
        'students_count': total_students,
        'books_in_hand': my_copies.count(),
        'books_issued': issued_to_students.count(),
        'books_received': my_copies.count() + issued_to_students.count(),
        'books_returned': books_returned,
        'reported_lost': reported_lost,
        'reported_damaged': reported_damaged,
        'my_copies': my_copies[:15],
        'issued_to_students': issued_to_students[:15],
    }
    return render(request, 'dashboards/teacher.html', context)


@login_required
def student_dashboard(request):
    if request.user.role != 'STUDENT':
        return HttpResponseForbidden(_('Access denied.'))

    user = request.user
    # All books currently in student's possession
    my_books = _copies_currently_held_by(
        BookCopy.objects.all(), user,
        BookCopy.Status.ISSUED_TO_STUDENT,
        BookTransaction.TransactionType.TEACHER_TO_STUDENT,
        'to_user_id'
    ).select_related('book', 'school')

    returned_books = BookTransaction.objects.filter(
        from_user=user,
        transaction_type=BookTransaction.TransactionType.STUDENT_RETURN
    ).select_related('book_copy', 'book_copy__book').order_by('-created_at')[:10]

    my_issues = BookIssue.objects.filter(student=user).select_related('book_copy', 'book_copy__book').order_by('-reported_at')

    context = {
        'total_books': my_books.count(),
        'total_returned': BookTransaction.objects.filter(from_user=user, transaction_type=BookTransaction.TransactionType.STUDENT_RETURN).count(),
        'total_lost': BookCopy.objects.filter(transactions__to_user=user, status=BookCopy.Status.LOST).distinct().count(),
        'total_damaged': BookCopy.objects.filter(transactions__to_user=user, status=BookCopy.Status.DAMAGED).distinct().count(),
        'my_books': my_books,
        'returned_books': returned_books,
        'my_issues': my_issues,
    }
    return render(request, 'dashboards/student.html', context)


@login_required
def analytics_view(request):
    if request.user.role not in ['SUPER_ADMIN', 'DISTRICT_CHAIRMAN']:
        return HttpResponseForbidden(_('Access denied.'))

    copies_qs = BookCopy.objects.all()
    if request.user.role == 'DISTRICT_CHAIRMAN':
        copies_qs = copies_qs.filter(school__district=request.user.district)

    total_books = copies_qs.count()
    by_status = copies_qs.values('status').annotate(count=Count('id')).order_by('-count')

    by_grade = Book.objects.values('grade').annotate(
        copies_count=Count('copies', filter=Q(copies__in=copies_qs), distinct=True)
    ).order_by('grade')

    by_subject = Book.objects.values('subject').annotate(
        copies_count=Count('copies', filter=Q(copies__in=copies_qs), distinct=True)
    ).order_by('-copies_count')[:10]

    regions_data = Region.objects.filter(is_active=True).annotate(
        schools_count=Count('districts__schools', filter=Q(districts__schools__is_active=True), distinct=True),
        books_count=Count('districts__schools__book_copies', distinct=True),
        students_count=Count('districts__schools__users', filter=Q(districts__schools__users__role='STUDENT', districts__schools__users__is_active=True), distinct=True)
    )

    context = {
        'total_books': total_books,
        'by_status': by_status,
        'by_grade': by_grade,
        'by_subject': by_subject,
        'regions_data': regions_data,
    }
    return render(request, 'analytics/analytics_detail.html', context)
