from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import (
    AcademicYear, Classroom, StudentEnrollment, TeacherClassAssignment,
    Book, BookCopy, BookRequest, BookIssue
)
from schools.models import School
from accounts.models import User
from transactions.models import BookTransaction
from audit.utils import log_audit


def _copies_currently_held_by(base_qs, user, status, tx_type, holder_field):
    """Restrict a BookCopy queryset to copies whose most recent hand-off
    transaction of the given type has `holder_field` equal to user.

    Filtering on status plus any historical transaction match is not enough:
    a copy keeps matching an old holder even after it has since been
    reassigned to someone else. So we check each copy's latest matching
    transaction one by one and keep only the ones that match.
    """
    matching_ids = []
    for copy in base_qs.filter(status=status):
        last_tx = copy.transactions.filter(transaction_type=tx_type).order_by('-created_at').first()
        if last_tx and getattr(last_tx, holder_field) == user.pk:
            matching_ids.append(copy.pk)
    return base_qs.filter(pk__in=matching_ids)


# ==============================
# BOOKS (CATALOG)
# ==============================

@login_required
def book_list_view(request):
    user = request.user
    books = Book.objects.all()

    if user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN']:
        if user.school:
            books = books.filter(copies__school=user.school).distinct()
        else:
            books = Book.objects.none()
    elif user.role == 'CLASS_TEACHER':
        if user.school:
            my_copy_ids = _copies_currently_held_by(
                BookCopy.objects.filter(school=user.school), user,
                BookCopy.Status.ISSUED_TO_TEACHER,
                BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER,
                'to_user_id'
            ).values_list('pk', flat=True)
            books = books.filter(copies__id__in=my_copy_ids).distinct()
        else:
            books = Book.objects.none()
    elif user.role == 'STUDENT':
        my_copy_ids = _copies_currently_held_by(
            BookCopy.objects.all(), user,
            BookCopy.Status.ISSUED_TO_STUDENT,
            BookTransaction.TransactionType.TEACHER_TO_STUDENT,
            'to_user_id'
        ).values_list('pk', flat=True)
        books = books.filter(copies__id__in=my_copy_ids).distinct()

    search = request.GET.get('search', '').strip()
    grade = request.GET.get('grade', '')
    subject = request.GET.get('subject', '')
    language = request.GET.get('language', '')

    if search:
        books = books.filter(
            Q(title__icontains=search) |
            Q(author__icontains=search) |
            Q(isbn__icontains=search) |
            Q(publisher__icontains=search)
        )
    if grade:
        books = books.filter(grade=grade)
    if subject:
        books = books.filter(subject__icontains=subject)
    if language:
        books = books.filter(language=language)

    books = books.annotate(
        total_copies=Count('copies', distinct=True)
    ).order_by('grade', 'title')

    paginator = Paginator(books, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    subjects = Book.objects.values_list('subject', flat=True).distinct().order_by('subject')

    return render(request, 'library/book_list.html', {
        'books': page_obj,
        'page_obj': page_obj,
        'search': search,
        'grade': grade,
        'subject': subject,
        'language': language,
        'subjects': subjects,
        'grades': range(1, 12),
    })


@login_required
def book_create_view(request):
    if request.user.role not in ['SUPER_ADMIN', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        subject = request.POST.get('subject', '').strip()
        grade = request.POST.get('grade', 1)
        language = request.POST.get('language', 'tj')
        isbn = request.POST.get('isbn', '').strip()
        publisher = request.POST.get('publisher', '').strip()
        pub_year = request.POST.get('publication_year') or None

        if not title or not author or not subject:
            messages.error(request, _('Fill in the required fields: title, author, subject.'))
        else:
            book = Book.objects.create(
                title=title,
                author=author,
                subject=subject,
                grade=int(grade),
                language=language,
                isbn=isbn,
                publisher=publisher,
                publication_year=int(pub_year) if pub_year else None,
            )
            log_audit(request.user, 'BOOK_CREATE', 'Book', book.pk, f'Created catalog book "{book.title}" ({book.author})')
            messages.success(request, _('Textbook "%(title)s" has been successfully added to the catalog.') % {'title': book.title})
            return redirect('library:book_list')

    return render(request, 'library/book_form.html', {
        'title': _('Add Textbook to Catalog'),
        'grades': range(1, 12),
    })


@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    user = request.user
    copies = book.copies.select_related('school').all()

    if user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN', 'CLASS_TEACHER'] and user.school:
        copies = copies.filter(school=user.school)

    stats = {
        'total': copies.count(),
        'available': copies.filter(status__in=[BookCopy.Status.AVAILABLE, BookCopy.Status.AT_LIBRARY]).count(),
        'issued_teacher': copies.filter(status=BookCopy.Status.ISSUED_TO_TEACHER).count(),
        'issued_student': copies.filter(status=BookCopy.Status.ISSUED_TO_STUDENT).count(),
        'lost': copies.filter(status=BookCopy.Status.LOST).count(),
        'damaged': copies.filter(status=BookCopy.Status.DAMAGED).count(),
        'written_off': copies.filter(status=BookCopy.Status.WRITTEN_OFF).count(),
    }

    paginator = Paginator(copies.order_by('inventory_number'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'library/book_detail.html', {
        'book': book,
        'copies': page_obj,
        'page_obj': page_obj,
        'stats': stats,
    })


@login_required
def book_edit_view(request, pk):
    if request.user.role not in ['SUPER_ADMIN', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.title = request.POST.get('title', book.title).strip()
        book.author = request.POST.get('author', book.author).strip()
        book.subject = request.POST.get('subject', book.subject).strip()
        book.grade = int(request.POST.get('grade', book.grade))
        book.language = request.POST.get('language', book.language)
        book.isbn = request.POST.get('isbn', book.isbn).strip()
        book.publisher = request.POST.get('publisher', book.publisher).strip()
        pub_year = request.POST.get('publication_year')
        book.publication_year = int(pub_year) if pub_year else None
        book.save()
        log_audit(request.user, 'BOOK_UPDATE', 'Book', book.pk, f'Updated catalog book "{book.title}"')
        messages.success(request, _('Textbook "%(title)s" has been successfully updated.') % {'title': book.title})
        return redirect('library:book_detail', pk=book.pk)

    return render(request, 'library/book_form.html', {
        'title': _('Edit Textbook'),
        'book': book,
        'grades': range(1, 12),
    })


# ==============================
# BOOK COPIES
# ==============================

@login_required
def copy_list_view(request):
    user = request.user
    copies = BookCopy.objects.select_related('book', 'school').all()

    if user.role == 'SUPER_ADMIN':
        pass
    elif user.role == 'DISTRICT_CHAIRMAN':
        copies = copies.filter(school__district=user.district)
    elif user.role == 'JAMOAT_CHAIRMAN':
        copies = copies.filter(school__jamoat=user.jamoat)
    elif user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN']:
        copies = copies.filter(school=user.school)
    elif user.role == 'CLASS_TEACHER':
        copies = _copies_currently_held_by(
            copies.filter(school=user.school), user,
            BookCopy.Status.ISSUED_TO_TEACHER,
            BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER,
            'to_user_id'
        )
    elif user.role == 'STUDENT':
        copies = _copies_currently_held_by(
            copies, user,
            BookCopy.Status.ISSUED_TO_STUDENT,
            BookTransaction.TransactionType.TEACHER_TO_STUDENT,
            'to_user_id'
        )

    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    school_filter = request.GET.get('school', '')
    grade_filter = request.GET.get('grade', '')

    if search:
        copies = copies.filter(
            Q(inventory_number__icontains=search) |
            Q(barcode__icontains=search) |
            Q(book__title__icontains=search) |
            Q(book__author__icontains=search)
        )
    if status_filter:
        copies = copies.filter(status=status_filter)
    if school_filter and user.role in ['SUPER_ADMIN', 'DISTRICT_CHAIRMAN', 'JAMOAT_CHAIRMAN']:
        copies = copies.filter(school_id=school_filter)
    if grade_filter:
        copies = copies.filter(book__grade=grade_filter)

    paginator = Paginator(copies.order_by('inventory_number'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    schools = School.objects.filter(is_active=True)
    if user.role == 'DISTRICT_CHAIRMAN' and user.district:
        schools = schools.filter(district=user.district)
    elif user.role == 'JAMOAT_CHAIRMAN' and user.jamoat:
        schools = schools.filter(jamoat=user.jamoat)

    return render(request, 'library/copy_list.html', {
        'copies': page_obj,
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'school_filter': school_filter,
        'grade_filter': grade_filter,
        'statuses': BookCopy.Status.choices,
        'schools': schools,
        'grades': range(1, 12),
    })


@login_required
def copy_create_view(request):
    if request.user.role not in ['SUPER_ADMIN', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        school = request.user.school if request.user.role == 'LIBRARIAN' else None
        if request.user.role == 'SUPER_ADMIN':
            school_id = request.POST.get('school')
            school = get_object_or_404(School, pk=school_id) if school_id else None

        if not school:
            messages.error(request, _('You must select a school.'))
            books = Book.objects.all().order_by('grade', 'title')
            schools = School.objects.filter(is_active=True)
            return render(request, 'library/copy_form.html', {'title': _('Create Copies'), 'books': books, 'schools': schools})

        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1 or quantity > 500:
            messages.error(request, _('Quantity must be between 1 and 500 copies at a time.'))
            return redirect('library:copy_create')

        book = get_object_or_404(Book, pk=request.POST.get('book'))
        prefix_inv = request.POST.get('inventory_number_prefix', '').strip() or f'TJ-S{school.pk:03d}-B{book.pk:04d}-'
        prefix_barcode = request.POST.get('barcode_prefix', '').strip() or f'BC{school.pk:03d}{book.pk:04d}'

        # Determine last sequence
        last_copy = BookCopy.objects.filter(book=book, school=school).order_by('-pk').first()
        start_idx = 1
        if last_copy:
            start_idx = BookCopy.objects.filter(book=book, school=school).count() + 1

        created_count = 0
        for i in range(quantity):
            seq = str(start_idx + i).zfill(5)
            inv_num = f'{prefix_inv}{seq}'
            bc = f'{prefix_barcode}{seq}'

            # Ensure uniqueness
            while BookCopy.objects.filter(inventory_number=inv_num).exists():
                start_idx += 1
                seq = str(start_idx + i).zfill(5)
                inv_num = f'{prefix_inv}{seq}'
                bc = f'{prefix_barcode}{seq}'

            copy = BookCopy.objects.create(
                book=book,
                inventory_number=inv_num,
                barcode=bc,
                school=school,
                status=BookCopy.Status.AT_LIBRARY,
            )
            # Log initial reception transaction
            BookTransaction.objects.create(
                book_copy=copy,
                from_user=None,
                to_user=request.user,
                from_location=_('Central Warehouse / Intake'),
                to_location=_('Library %(school)s') % {'school': school.name},
                transaction_type='WAREHOUSE_TO_SCHOOL',
                created_by=request.user,
                note=_('Initial intake of batch (%(quantity)s pcs.)') % {'quantity': quantity}
            )
            created_count += 1

        log_audit(request.user, 'BOOK_COPIES_CREATE', 'BookCopy', book.pk, f'Registered {created_count} copies of "{book.title}" in {school.name}')
        messages.success(request, _('Successfully registered %(count)s copies of textbook "%(title)s".') % {'count': created_count, 'title': book.title})
        return redirect('library:copy_list')

    books = Book.objects.all().order_by('grade', 'title')
    schools = School.objects.filter(is_active=True)
    return render(request, 'library/copy_form.html', {
        'title': _('Create Textbook Copies'),
        'books': books,
        'schools': schools,
    })


@login_required
def copy_detail_view(request, pk):
    copy = get_object_or_404(BookCopy.objects.select_related('book', 'school'), pk=pk)
    user = request.user

    # Permission scoping
    if user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN'] and copy.school != user.school:
        return HttpResponseForbidden(_('Access denied.'))

    transactions = copy.transactions.select_related('from_user', 'to_user', 'created_by').order_by('-created_at')
    issues = copy.issues.select_related('student', 'reported_by', 'confirmed_by').order_by('-reported_at')

    return render(request, 'library/copy_detail.html', {
        'copy': copy,
        'transactions': transactions,
        'issues': issues,
    })


@login_required
def copy_scan_view(request):
    search = request.GET.get('code', '').strip()
    copy = None
    if search:
        user = request.user
        qs = BookCopy.objects.select_related('book', 'school')
        if user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN', 'CLASS_TEACHER'] and user.school:
            qs = qs.filter(school=user.school)
        copy = qs.filter(Q(barcode=search) | Q(inventory_number=search)).first()

    return render(request, 'library/copy_scan.html', {
        'copy': copy,
        'search': search,
    })


# ==============================
# ACADEMIC YEARS & CLASSROOMS
# ==============================

@login_required
def academic_year_list_view(request):
    if request.user.role not in ['SUPER_ADMIN', 'SCHOOL_DIRECTOR', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))
    years = AcademicYear.objects.all().order_by('-start_date')
    return render(request, 'library/academic_year_list.html', {'years': years})


@login_required
def academic_year_create_view(request):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = 'is_current' in request.POST
        if not name or not start_date or not end_date:
            messages.error(request, _('Fill in all fields.'))
        else:
            year = AcademicYear.objects.create(
                name=name,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
            )
            log_audit(request.user, 'ACADEMIC_YEAR_CREATE', 'AcademicYear', year.pk, f'Created academic year {year.name}')
            messages.success(request, _('Academic year "%(name)s" has been successfully created.') % {'name': year.name})
            return redirect('library:academic_year_list')
    return render(request, 'library/academic_year_form.html', {'title': _('Create Academic Year')})


@login_required
def classroom_list_view(request):
    user = request.user
    classrooms = Classroom.objects.select_related('school', 'academic_year').all()

    if user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN', 'CLASS_TEACHER']:
        classrooms = classrooms.filter(school=user.school)
    elif user.role == 'SUPER_ADMIN':
        pass
    else:
        return HttpResponseForbidden(_('Access denied.'))

    classrooms = classrooms.annotate(
        students_count=Count('enrollments', filter=Q(enrollments__is_active=True), distinct=True)
    ).order_by('grade', 'name')

    return render(request, 'library/classroom_list.html', {'classrooms': classrooms})


@login_required
def classroom_create_view(request):
    if request.user.role not in ['SUPER_ADMIN', 'SCHOOL_DIRECTOR']:
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        school = request.user.school if request.user.role == 'SCHOOL_DIRECTOR' else None
        if request.user.role == 'SUPER_ADMIN':
            school_id = request.POST.get('school')
            school = get_object_or_404(School, pk=school_id) if school_id else None

        name = request.POST.get('name', '').strip()
        grade = request.POST.get('grade', 1)
        year_id = request.POST.get('academic_year')

        if not school or not name or not year_id:
            messages.error(request, _('Fill in all fields.'))
        elif Classroom.objects.filter(school=school, name=name, academic_year_id=year_id).exists():
            messages.error(request, _('Class %(name)s already exists in this academic year.') % {'name': name})
        else:
            classroom = Classroom.objects.create(
                school=school,
                name=name,
                grade=int(grade),
                academic_year_id=year_id,
            )
            log_audit(request.user, 'CLASSROOM_CREATE', 'Classroom', classroom.pk, f'Created classroom {classroom.name} (Grade {classroom.grade}) at {school.name}')
            messages.success(request, _('Class "%(name)s" has been successfully created.') % {'name': classroom.name})
            return redirect('library:classroom_list')

    years = AcademicYear.objects.filter(is_current=True)
    if not years.exists():
        years = AcademicYear.objects.all()
    schools = School.objects.filter(is_active=True)
    return render(request, 'library/classroom_form.html', {
        'title': _('Create Class'),
        'years': years,
        'schools': schools,
        'grades': range(1, 12),
    })


# ==============================
# ENROLLMENTS & ASSIGNMENTS
# ==============================

@login_required
def enrollment_list_view(request):
    user = request.user
    enrollments = StudentEnrollment.objects.select_related('student', 'classroom', 'classroom__school', 'academic_year').filter(is_active=True)

    if user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN']:
        enrollments = enrollments.filter(classroom__school=user.school)
    elif user.role == 'CLASS_TEACHER':
        enrollments = enrollments.filter(
            classroom__teacher_assignments__teacher=user,
            classroom__teacher_assignments__is_class_teacher=True
        )
    elif user.role == 'SUPER_ADMIN':
        pass
    else:
        return HttpResponseForbidden(_('Access denied.'))

    search = request.GET.get('search', '').strip()
    class_filter = request.GET.get('classroom', '')

    if search:
        enrollments = enrollments.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__username__icontains=search)
        )
    if class_filter:
        enrollments = enrollments.filter(classroom_id=class_filter)

    enrollments = enrollments.order_by('classroom__grade', 'classroom__name', 'student__last_name')
    paginator = Paginator(enrollments, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    classrooms = Classroom.objects.filter(school=user.school) if user.school else Classroom.objects.all()

    return render(request, 'library/enrollment_list.html', {
        'enrollments': page_obj,
        'page_obj': page_obj,
        'search': search,
        'class_filter': class_filter,
        'classrooms': classrooms,
    })


@login_required
def teacher_assignment_list_view(request):
    user = request.user
    assignments = TeacherClassAssignment.objects.select_related('teacher', 'classroom', 'academic_year').all()

    if user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN']:
        assignments = assignments.filter(classroom__school=user.school)
    elif user.role == 'CLASS_TEACHER':
        assignments = assignments.filter(teacher=user)
    elif user.role == 'SUPER_ADMIN':
        pass
    else:
        return HttpResponseForbidden(_('Access denied.'))

    assignments = assignments.order_by('classroom__grade', 'classroom__name')
    return render(request, 'library/teacher_assignment_list.html', {'assignments': assignments})


# ==============================
# BOOK REQUESTS
# ==============================

@login_required
def book_request_list_view(request):
    user = request.user
    if user.role == 'SUPER_ADMIN':
        book_requests = BookRequest.objects.select_related('school', 'book', 'created_by', 'approved_by').all()
    elif user.role == 'DISTRICT_CHAIRMAN':
        book_requests = BookRequest.objects.filter(school__district=user.district).select_related('school', 'book', 'created_by')
    elif user.role == 'SCHOOL_DIRECTOR':
        book_requests = BookRequest.objects.filter(school=user.school).select_related('school', 'book', 'created_by')
    else:
        return HttpResponseForbidden(_('Access denied.'))

    status_filter = request.GET.get('status', '')
    if status_filter:
        book_requests = book_requests.filter(status=status_filter)

    paginator = Paginator(book_requests.order_by('-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'library/book_request_list.html', {
        'book_requests': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'statuses': BookRequest.Status.choices,
    })


@login_required
def book_request_create_view(request):
    if request.user.role != 'SCHOOL_DIRECTOR':
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        book_id = request.POST.get('book')
        requested_quantity = int(request.POST.get('requested_quantity', 1))
        reason = request.POST.get('reason', '').strip()

        book = get_object_or_404(Book, pk=book_id)
        current_avail = BookCopy.objects.filter(book=book, school=request.user.school, status__in=['AVAILABLE', 'AT_LIBRARY']).count()

        req = BookRequest.objects.create(
            school=request.user.school,
            book=book,
            requested_quantity=requested_quantity,
            available_quantity=current_avail,
            reason=reason,
            created_by=request.user,
        )
        log_audit(request.user, 'BOOK_REQUEST_CREATE', 'BookRequest', req.pk, f'School {request.user.school.name} requested {requested_quantity} copies of {book.title}')
        messages.success(request, _('Request for %(quantity)s copies of textbook "%(title)s" has been successfully created.') % {'quantity': requested_quantity, 'title': book.title})
        return redirect('library:book_request_list')

    books = Book.objects.all().order_by('grade', 'title')
    return render(request, 'library/book_request_form.html', {'books': books})


@login_required
def book_request_approve_view(request, pk):
    if request.user.role not in ['SUPER_ADMIN', 'DISTRICT_CHAIRMAN']:
        return HttpResponseForbidden(_('Access denied.'))
    book_request = get_object_or_404(BookRequest, pk=pk)
    if request.user.role == 'DISTRICT_CHAIRMAN' and book_request.school.district_id != request.user.district_id:
        return HttpResponseForbidden(_('Access denied.'))

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            book_request.status = BookRequest.Status.APPROVED
            book_request.approved_by = request.user
            book_request.approved_at = timezone.now()
            book_request.save()
            log_audit(request.user, 'BOOK_REQUEST_APPROVE', 'BookRequest', book_request.pk, f'Approved request for {book_request.requested_quantity} copies of {book_request.book.title} for {book_request.school.name}')
            messages.success(request, _('Request has been successfully approved.'))
        elif action == 'reject':
            book_request.status = BookRequest.Status.REJECTED
            book_request.approved_by = request.user
            book_request.approved_at = timezone.now()
            book_request.save()
            log_audit(request.user, 'BOOK_REQUEST_REJECT', 'BookRequest', book_request.pk, f'Rejected request for {book_request.book.title} from {book_request.school.name}')
            messages.info(request, _('Request has been rejected.'))
    return redirect('library:book_request_list')


# ==============================
# BOOK ISSUES (LOST & DAMAGED)
# ==============================

@login_required
def book_issue_list_view(request):
    user = request.user
    issues = BookIssue.objects.select_related('book_copy', 'book_copy__book', 'student', 'reported_by', 'confirmed_by').all()

    if user.role == 'SUPER_ADMIN':
        pass
    elif user.role == 'DISTRICT_CHAIRMAN':
        issues = issues.filter(book_copy__school__district=user.district)
    elif user.role == 'JAMOAT_CHAIRMAN':
        issues = issues.filter(book_copy__school__jamoat=user.jamoat)
    elif user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN']:
        issues = issues.filter(book_copy__school=user.school)
    elif user.role == 'CLASS_TEACHER':
        issues = issues.filter(
            student__enrollments__classroom__teacher_assignments__teacher=user,
            student__enrollments__classroom__teacher_assignments__is_class_teacher=True
        ).distinct()
    elif user.role == 'STUDENT':
        issues = issues.filter(student=user)

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    if status_filter:
        issues = issues.filter(status=status_filter)
    if type_filter:
        issues = issues.filter(issue_type=type_filter)

    paginator = Paginator(issues.order_by('-reported_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'library/book_issue_list.html', {
        'issues': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'type_filter': type_filter,
    })


@login_required
def book_issue_create_view(request):
    if request.user.role not in ['CLASS_TEACHER', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        copy_id = request.POST.get('book_copy')
        student_id = request.POST.get('student')
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description', '').strip()

        if request.user.role == 'CLASS_TEACHER':
            my_classrooms = Classroom.objects.filter(
                teacher_assignments__teacher=request.user,
                teacher_assignments__is_class_teacher=True
            )
            student = get_object_or_404(
                User, pk=student_id, role='STUDENT',
                school=request.user.school,
                enrollments__classroom__in=my_classrooms,
                enrollments__is_active=True
            )
            copy = get_object_or_404(
                BookCopy,
                pk=copy_id,
                school=request.user.school,
                status=BookCopy.Status.ISSUED_TO_STUDENT,
            )
            last_tx = copy.transactions.filter(
                transaction_type=BookTransaction.TransactionType.TEACHER_TO_STUDENT
            ).order_by('-created_at').first()
            if not last_tx or last_tx.from_user_id != request.user.pk:
                return HttpResponseForbidden(_('Access denied.'))
        else:
            student = get_object_or_404(User, pk=student_id, role='STUDENT', school=request.user.school)
            copy = get_object_or_404(BookCopy, pk=copy_id, school=request.user.school)

        issue = BookIssue.objects.create(
            book_copy=copy,
            student=student,
            issue_type=issue_type,
            description=description,
            reported_by=request.user,
        )
        log_audit(request.user, 'BOOK_ISSUE_REPORT', 'BookIssue', issue.pk, f'Reported {issue_type} for copy {copy.inventory_number} (student: {student.get_full_name()})')
        messages.success(request, _('Textbook issue report has been successfully created and submitted to the librarian for review.'))
        return redirect('library:book_issue_list')

    # Provide copies and students
    if request.user.role == 'CLASS_TEACHER':
        my_classrooms = User.objects.filter(
            pk=request.user.pk,
            class_assignments__is_class_teacher=True
        ).values_list('class_assignments__classroom', flat=True)

        students = User.objects.filter(
            role='STUDENT',
            enrollments__classroom__in=my_classrooms,
            enrollments__is_active=True,
            is_active=True
        ).distinct()

        copies = _copies_currently_held_by(
            BookCopy.objects.filter(school=request.user.school), request.user,
            BookCopy.Status.ISSUED_TO_STUDENT,
            BookTransaction.TransactionType.TEACHER_TO_STUDENT,
            'from_user_id'
        )
    else:
        students = User.objects.filter(role='STUDENT', school=request.user.school, is_active=True)
        copies = BookCopy.objects.filter(school=request.user.school).exclude(status=BookCopy.Status.WRITTEN_OFF)

    return render(request, 'library/book_issue_form.html', {
        'title': _('Report Lost or Damaged'),
        'copies': copies,
        'students': students,
    })


@login_required
def book_issue_confirm_view(request, pk):
    if request.user.role not in ['SUPER_ADMIN', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))
    issue = get_object_or_404(BookIssue, pk=pk)
    if request.user.role == 'LIBRARIAN' and issue.book_copy.school_id != request.user.school_id:
        return HttpResponseForbidden(_('Access denied.'))

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            issue.status = BookIssue.IssueStatus.CONFIRMED
            issue.confirmed_by = request.user
            issue.confirmed_at = timezone.now()
            issue.save()

            # Update book copy status
            copy = issue.book_copy
            old_status = copy.status
            new_status = BookCopy.Status.LOST if issue.issue_type == BookIssue.IssueType.LOST else BookCopy.Status.DAMAGED
            copy.status = new_status
            copy.save()

            # Record in transaction log
            BookTransaction.objects.create(
                book_copy=copy,
                from_user=issue.student,
                to_user=request.user,
                from_location=_('Student %(name)s') % {'name': issue.student.get_full_name()},
                to_location=_('Library %(school)s') % {'school': request.user.school.name},
                transaction_type=new_status,
                created_by=request.user,
                note=_('Confirmed act %(type)s: %(desc)s') % {'type': issue.get_issue_type_display(), 'desc': issue.description}
            )

            log_audit(request.user, 'BOOK_ISSUE_CONFIRM', 'BookIssue', issue.pk, f'Confirmed {issue.issue_type} for copy {copy.inventory_number}. Status updated from {old_status} to {new_status}')
            messages.success(request, _('Report confirmed. Status of copy %(inv)s has been updated to "%(status)s".') % {'inv': copy.inventory_number, 'status': copy.get_status_display()})

        elif action == 'reject':
            issue.status = BookIssue.IssueStatus.REJECTED
            issue.confirmed_by = request.user
            issue.confirmed_at = timezone.now()
            issue.save()
            log_audit(request.user, 'BOOK_ISSUE_REJECT', 'BookIssue', issue.pk, f'Rejected issue #{issue.pk} for copy {issue.book_copy.inventory_number}')
            messages.info(request, _('Report has been rejected.'))

    return redirect('library:book_issue_list')
