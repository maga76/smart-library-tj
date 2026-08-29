from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, OuterRef, Subquery
from django.utils.translation import gettext_lazy as _
from .models import BookTransaction
from library.models import BookCopy, Classroom, StudentEnrollment, TeacherClassAssignment
from accounts.models import User
from audit.utils import log_audit


@login_required
def transaction_list_view(request):
    user = request.user
    transactions = BookTransaction.objects.select_related('book_copy', 'book_copy__book', 'from_user', 'to_user', 'created_by').all()

    if user.role == 'SUPER_ADMIN':
        pass
    elif user.role == 'DISTRICT_CHAIRMAN':
        transactions = transactions.filter(book_copy__school__district=user.district)
    elif user.role == 'JAMOAT_CHAIRMAN':
        transactions = transactions.filter(book_copy__school__jamoat=user.jamoat)
    elif user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN']:
        transactions = transactions.filter(book_copy__school=user.school)
    elif user.role == 'CLASS_TEACHER':
        transactions = transactions.filter(
            book_copy__school=user.school
        ).filter(
            Q(from_user=user) | Q(to_user=user)
        )
    elif user.role == 'STUDENT':
        transactions = transactions.filter(
            Q(from_user=user) | Q(to_user=user)
        )

    search = request.GET.get('search', '').strip()
    tx_type = request.GET.get('type', '')
    school_filter = request.GET.get('school', '')

    if search:
        transactions = transactions.filter(
            Q(book_copy__inventory_number__icontains=search) |
            Q(book_copy__barcode__icontains=search) |
            Q(book_copy__book__title__icontains=search) |
            Q(from_user__username__icontains=search) |
            Q(to_user__username__icontains=search)
        )
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)
    if school_filter and user.role in ['SUPER_ADMIN', 'DISTRICT_CHAIRMAN']:
        transactions = transactions.filter(book_copy__school_id=school_filter)

    paginator = Paginator(transactions.order_by('-created_at'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'transactions/transaction_list.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
        'search': search,
        'tx_type': tx_type,
        'school_filter': school_filter,
        'types': BookTransaction.TransactionType.choices,
    })


@login_required
def issue_to_teacher_view(request):
    if request.user.role != 'LIBRARIAN':
        return HttpResponseForbidden(_('Access denied.'))
    if not request.user.school:
        messages.error(request, _('Librarian is not assigned to a school.'))
        return redirect('analytics:dashboard')

    if request.method == 'POST':
        copy_ids = request.POST.getlist('book_copies')
        teacher_id = request.POST.get('teacher')
        note = request.POST.get('note', '').strip()

        if not copy_ids:
            # Fallback to single book_copy if submitted as single field
            single_id = request.POST.get('book_copy')
            if single_id:
                copy_ids = [single_id]

        if not copy_ids or not teacher_id:
            messages.error(request, _('Select at least one book and a class teacher.'))
            return redirect('transactions:issue_to_teacher')

        teacher = get_object_or_404(User, pk=teacher_id, role='CLASS_TEACHER', school=request.user.school)
        issued_count = 0

        for cid in copy_ids:
            copy = get_object_or_404(BookCopy, pk=cid, school=request.user.school)
            if copy.status not in [BookCopy.Status.AT_LIBRARY, BookCopy.Status.AVAILABLE]:
                continue

            copy.status = BookCopy.Status.ISSUED_TO_TEACHER
            copy.save()

            BookTransaction.objects.create(
                book_copy=copy,
                from_user=request.user,
                to_user=teacher,
                from_location=_('Library %(school)s') % {'school': request.user.school.name},
                to_location=_('Teacher %(name)s') % {'name': teacher.get_full_name()},
                transaction_type=BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER,
                created_by=request.user,
                note=note,
            )
            issued_count += 1

        log_audit(request.user, 'ISSUE_TO_TEACHER', 'BookTransaction', teacher.pk, f'Issued {issued_count} books to teacher {teacher.get_full_name()}')
        messages.success(request, _('Successfully issued %(count)s textbooks to teacher %(teacher)s.') % {'count': issued_count, 'teacher': teacher.get_full_name()})
        return redirect('transactions:transaction_list')

    copies = BookCopy.objects.filter(
        school=request.user.school,
        status__in=[BookCopy.Status.AT_LIBRARY, BookCopy.Status.AVAILABLE]
    ).select_related('book').order_by('book__grade', 'book__title', 'inventory_number')

    teachers = User.objects.filter(
        role='CLASS_TEACHER',
        school=request.user.school,
        is_active=True
    ).order_by('last_name', 'first_name')

    return render(request, 'transactions/issue_to_teacher.html', {
        'copies': copies,
        'teachers': teachers,
    })


@login_required
def issue_to_student_view(request):
    if request.user.role != 'CLASS_TEACHER':
        return HttpResponseForbidden(_('Access denied.'))
    if not request.user.school:
        messages.error(request, _('Teacher is not assigned to a school.'))
        return redirect('analytics:dashboard')

    if request.method == 'POST':
        copy_id = request.POST.get('book_copy')
        student_id = request.POST.get('student')
        note = request.POST.get('note', '').strip()

        if not copy_id or not student_id:
            messages.error(request, _('Select a book and a student.'))
            return redirect('transactions:issue_to_student')

        # Verify copy belongs to this teacher
        copy = get_object_or_404(
            BookCopy,
            pk=copy_id,
            school=request.user.school,
            status=BookCopy.Status.ISSUED_TO_TEACHER
        )

        last_teacher_tx = copy.transactions.filter(
            transaction_type=BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER
        ).first()
        if not last_teacher_tx or last_teacher_tx.to_user_id != request.user.pk:
            return HttpResponseForbidden(_('Access denied.'))

        # Verify student is in teacher's assigned classroom
        my_classrooms = Classroom.objects.filter(
            teacher_assignments__teacher=request.user,
            teacher_assignments__is_class_teacher=True
        )

        student = get_object_or_404(
            User,
            pk=student_id,
            role='STUDENT',
            school=request.user.school,
            enrollments__classroom__in=my_classrooms,
            enrollments__is_active=True
        )

        copy.status = BookCopy.Status.ISSUED_TO_STUDENT
        copy.save()

        active_enrollment = student.enrollments.filter(is_active=True).first()
        class_name = active_enrollment.classroom.name if active_enrollment else ''

        BookTransaction.objects.create(
            book_copy=copy,
            from_user=request.user,
            to_user=student,
            from_location=_('Class Teacher %(name)s') % {'name': request.user.get_full_name()},
            to_location=_('Student %(name)s (%(class)s)') % {'name': student.get_full_name(), 'class': class_name},
            transaction_type=BookTransaction.TransactionType.TEACHER_TO_STUDENT,
            created_by=request.user,
            note=note,
        )

        log_audit(request.user, 'ISSUE_TO_STUDENT', 'BookTransaction', student.pk, f'Issued book {copy.inventory_number} ({copy.book.title}) to student {student.get_full_name()}')
        messages.success(request, _('Textbook "%(title)s" (%(inv)s) has been successfully issued to student %(student)s.') % {'title': copy.book.title, 'inv': copy.inventory_number, 'student': student.get_full_name()})
        return redirect('transactions:transaction_list')

    # Available copies currently held by this teacher (based on the latest hand-off, not any historical one)
    latest_teacher_tx = BookTransaction.objects.filter(
        book_copy=OuterRef('pk'),
        transaction_type=BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER
    ).order_by('-created_at')
    my_copies = BookCopy.objects.filter(
        school=request.user.school,
        status=BookCopy.Status.ISSUED_TO_TEACHER,
    ).annotate(
        current_teacher_id=Subquery(latest_teacher_tx.values('to_user_id')[:1])
    ).filter(current_teacher_id=request.user.pk).select_related('book').order_by('book__title', 'inventory_number')

    # Students from teacher's classes
    my_classrooms = Classroom.objects.filter(
        teacher_assignments__teacher=request.user,
        teacher_assignments__is_class_teacher=True
    )

    students = User.objects.filter(
        role='STUDENT',
        school=request.user.school,
        enrollments__classroom__in=my_classrooms,
        enrollments__is_active=True,
        is_active=True
    ).select_related('school').prefetch_related('enrollments__classroom').distinct().order_by('last_name', 'first_name')

    return render(request, 'transactions/issue_to_student.html', {
        'copies': my_copies,
        'students': students,
    })


@login_required
def return_from_student_view(request):
    if request.user.role != 'CLASS_TEACHER':
        return HttpResponseForbidden(_('Access denied.'))

    if request.method == 'POST':
        copy_id = request.POST.get('book_copy')
        note = request.POST.get('note', '').strip()

        copy = get_object_or_404(
            BookCopy,
            pk=copy_id,
            school=request.user.school,
            status=BookCopy.Status.ISSUED_TO_STUDENT
        )

        last_tx = copy.transactions.filter(
            transaction_type=BookTransaction.TransactionType.TEACHER_TO_STUDENT
        ).first()

        if not last_tx or last_tx.from_user_id != request.user.pk:
            return HttpResponseForbidden(_('Access denied.'))

        student = last_tx.to_user

        copy.status = BookCopy.Status.ISSUED_TO_TEACHER
        copy.save()

        BookTransaction.objects.create(
            book_copy=copy,
            from_user=student,
            to_user=request.user,
            from_location=_('Student %(name)s') % {'name': student.get_full_name() if student else _('Student')},
            to_location=_('Class Teacher %(name)s') % {'name': request.user.get_full_name()},
            transaction_type=BookTransaction.TransactionType.STUDENT_RETURN,
            created_by=request.user,
            note=note,
        )

        log_audit(request.user, 'RETURN_FROM_STUDENT', 'BookTransaction', copy.pk, f'Received return of copy {copy.inventory_number} ({copy.book.title}) from {student.get_full_name() if student else "student"}')
        messages.success(request, _('Textbook "%(title)s" (%(inv)s) has been successfully returned from the student.') % {'title': copy.book.title, 'inv': copy.inventory_number})
        return redirect('transactions:transaction_list')

    # Copies currently held by a student this teacher issued to (based on the latest hand-off)
    latest_student_tx = BookTransaction.objects.filter(
        book_copy=OuterRef('pk'),
        transaction_type=BookTransaction.TransactionType.TEACHER_TO_STUDENT
    ).order_by('-created_at')
    my_issued_copies = BookCopy.objects.filter(
        school=request.user.school,
        status=BookCopy.Status.ISSUED_TO_STUDENT,
    ).annotate(
        current_from_teacher_id=Subquery(latest_student_tx.values('from_user_id')[:1])
    ).filter(current_from_teacher_id=request.user.pk).select_related('book').order_by('book__title', 'inventory_number')

    return render(request, 'transactions/return_from_student.html', {
        'copies': my_issued_copies,
    })


@login_required
def return_from_teacher_view(request):
    if request.user.role != 'LIBRARIAN':
        return HttpResponseForbidden(_('Access denied.'))

    if request.method == 'POST':
        copy_ids = request.POST.getlist('book_copies')
        if not copy_ids:
            single_id = request.POST.get('book_copy')
            if single_id:
                copy_ids = [single_id]

        if not copy_ids:
            messages.error(request, _('Select at least one book to return.'))
            return redirect('transactions:return_from_teacher')

        returned_count = 0
        for cid in copy_ids:
            copy = get_object_or_404(
                BookCopy,
                pk=cid,
                school=request.user.school,
                status=BookCopy.Status.ISSUED_TO_TEACHER
            )

            last_tx = copy.transactions.filter(
                transaction_type=BookTransaction.TransactionType.LIBRARIAN_TO_TEACHER
            ).first()

            teacher = last_tx.to_user if last_tx else None

            copy.status = BookCopy.Status.AT_LIBRARY
            copy.save()

            BookTransaction.objects.create(
                book_copy=copy,
                from_user=teacher,
                to_user=request.user,
                from_location=_('Teacher %(name)s') % {'name': teacher.get_full_name() if teacher else ''},
                to_location=_('Library %(school)s') % {'school': request.user.school.name},
                transaction_type=BookTransaction.TransactionType.TEACHER_RETURN,
                created_by=request.user,
                note=_('Return batch to library fund')
            )
            returned_count += 1

        log_audit(request.user, 'RETURN_FROM_TEACHER', 'BookTransaction', request.user.school.pk, f'Received {returned_count} books back from teacher into library')
        messages.success(request, _('Successfully accepted %(count)s textbooks back into the library.') % {'count': returned_count})
        return redirect('transactions:transaction_list')

    copies = BookCopy.objects.filter(
        school=request.user.school,
        status=BookCopy.Status.ISSUED_TO_TEACHER
    ).select_related('book').order_by('book__title', 'inventory_number')

    return render(request, 'transactions/return_from_teacher.html', {
        'copies': copies,
    })


@login_required
def report_lost_view(request):
    if request.user.role not in ['CLASS_TEACHER', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))

    if request.method == 'POST':
        copy_id = request.POST.get('book_copy')
        note = request.POST.get('note', '').strip()
        copy = get_object_or_404(BookCopy, pk=copy_id, school=request.user.school)

        copy.status = BookCopy.Status.LOST
        copy.save()

        BookTransaction.objects.create(
            book_copy=copy,
            from_user=request.user,
            to_user=None,
            from_location=f'{request.user.get_role_display()} {request.user.get_full_name()}',
            to_location=_('Lost / Гумшуда'),
            transaction_type=BookTransaction.TransactionType.LOST,
            created_by=request.user,
            note=note,
        )

        log_audit(request.user, 'REPORT_LOST', 'BookCopy', copy.pk, f'Marked copy {copy.inventory_number} ({copy.book.title}) as LOST. Note: {note}')
        messages.warning(request, _('Textbook "%(title)s" (%(inv)s) has been marked as lost.') % {'title': copy.book.title, 'inv': copy.inventory_number})
        return redirect('transactions:transaction_list')

    if request.user.role == 'LIBRARIAN':
        copies = BookCopy.objects.filter(school=request.user.school).exclude(
            status__in=[BookCopy.Status.LOST, BookCopy.Status.WRITTEN_OFF]
        ).select_related('book')
    else:
        copies = BookCopy.objects.filter(
            school=request.user.school,
            status__in=[BookCopy.Status.ISSUED_TO_TEACHER, BookCopy.Status.ISSUED_TO_STUDENT]
        ).select_related('book')

    return render(request, 'transactions/report_lost.html', {'copies': copies})


@login_required
def report_damaged_view(request):
    if request.user.role not in ['CLASS_TEACHER', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))

    if request.method == 'POST':
        copy_id = request.POST.get('book_copy')
        note = request.POST.get('note', '').strip()
        copy = get_object_or_404(BookCopy, pk=copy_id, school=request.user.school)

        copy.status = BookCopy.Status.DAMAGED
        copy.save()

        BookTransaction.objects.create(
            book_copy=copy,
            from_user=request.user,
            to_user=None,
            from_location=f'{request.user.get_role_display()} {request.user.get_full_name()}',
            to_location=_('Damaged / Зарардида'),
            transaction_type=BookTransaction.TransactionType.DAMAGED,
            created_by=request.user,
            note=note,
        )

        log_audit(request.user, 'REPORT_DAMAGED', 'BookCopy', copy.pk, f'Marked copy {copy.inventory_number} ({copy.book.title}) as DAMAGED. Note: {note}')
        messages.warning(request, _('Textbook "%(title)s" (%(inv)s) has been marked as damaged.') % {'title': copy.book.title, 'inv': copy.inventory_number})
        return redirect('transactions:transaction_list')

    if request.user.role == 'LIBRARIAN':
        copies = BookCopy.objects.filter(school=request.user.school).exclude(
            status__in=[BookCopy.Status.DAMAGED, BookCopy.Status.WRITTEN_OFF]
        ).select_related('book')
    else:
        copies = BookCopy.objects.filter(
            school=request.user.school,
            status__in=[BookCopy.Status.ISSUED_TO_TEACHER, BookCopy.Status.ISSUED_TO_STUDENT]
        ).select_related('book')

    return render(request, 'transactions/report_damaged.html', {'copies': copies})


@login_required
def write_off_view(request, pk):
    if request.user.role not in ['SUPER_ADMIN', 'LIBRARIAN']:
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        copy = get_object_or_404(BookCopy, pk=pk)
        if request.user.role == 'LIBRARIAN' and copy.school != request.user.school:
            return HttpResponseForbidden(_('Access denied.'))

        reason = request.POST.get('reason', '').strip()
        copy.status = BookCopy.Status.WRITTEN_OFF
        copy.save()

        BookTransaction.objects.create(
            book_copy=copy,
            from_user=request.user,
            to_user=None,
            from_location=f'Библиотека {copy.school.name}',
            to_location=_('Written off from fund / Аз ҳисоб бароварда шуд'),
            transaction_type=BookTransaction.TransactionType.WRITTEN_OFF,
            created_by=request.user,
            note=reason or _('Write-off of unfit or lost copy'),
        )

        log_audit(request.user, 'WRITE_OFF', 'BookCopy', copy.pk, f'Written off copy {copy.inventory_number} ({copy.book.title}). Reason: {reason}')
        messages.info(request, _('Copy "%(title)s" (%(inv)s) has been written off from the library fund.') % {'title': copy.book.title, 'inv': copy.inventory_number})
        return redirect('library:copy_detail', pk=copy.pk)

    return redirect('library:copy_list')
