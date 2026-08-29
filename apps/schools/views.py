from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from .models import School
from apps.geography.models import Region, District, Jamoat
from apps.accounts.models import User
from apps.library.models import Classroom, BookCopy
from apps.audit.utils import log_audit


@login_required
def school_list_view(request):
    user = request.user
    schools = School.objects.select_related('region', 'district', 'jamoat').all()
    
    if user.role == 'SUPER_ADMIN':
        pass
    elif user.role == 'DISTRICT_CHAIRMAN':
        schools = schools.filter(district=user.district)
    elif user.role == 'JAMOAT_CHAIRMAN':
        schools = schools.filter(jamoat=user.jamoat)
    else:
        return HttpResponseForbidden(_('Access denied.'))

    region_filter = request.GET.get('region', '')
    district_filter = request.GET.get('district', '')
    jamoat_filter = request.GET.get('jamoat', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '').strip()

    if region_filter:
        schools = schools.filter(region_id=region_filter)
    if district_filter:
        schools = schools.filter(district_id=district_filter)
    if jamoat_filter:
        schools = schools.filter(jamoat_id=jamoat_filter)
    if status_filter == 'active':
        schools = schools.filter(is_active=True)
    elif status_filter == 'inactive':
        schools = schools.filter(is_active=False)

    if search:
        schools = schools.filter(
            Q(name__icontains=search) |
            Q(school_number__icontains=search) |
            Q(address__icontains=search) |
            Q(district__name_ru__icontains=search)
        )

    schools = schools.annotate(
        books_count=Count('book_copies', distinct=True),
        students_count=Count('users', filter=Q(users__role='STUDENT', users__is_active=True), distinct=True)
    ).order_by('school_number', 'name')

    paginator = Paginator(schools, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    regions = Region.objects.filter(is_active=True)
    districts = District.objects.filter(is_active=True)
    if user.role == 'DISTRICT_CHAIRMAN' and user.district:
        districts = districts.filter(pk=user.district.pk)
    
    return render(request, 'schools/school_list.html', {
        'schools': page_obj,
        'page_obj': page_obj,
        'regions': regions,
        'districts': districts,
        'region_filter': region_filter,
        'district_filter': district_filter,
        'jamoat_filter': jamoat_filter,
        'status_filter': status_filter,
        'search': search,
    })


@login_required
def school_create_view(request):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        school_number = request.POST.get('school_number', '').strip()
        region_id = request.POST.get('region')
        district_id = request.POST.get('district')
        jamoat_id = request.POST.get('jamoat')
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        student_capacity = int(request.POST.get('student_capacity') or 0)

        if not name or not school_number or not region_id or not district_id or not jamoat_id:
            messages.error(request, _('Fill in all required fields (name, number, region, district, jamoat).'))
        elif School.objects.filter(school_number=school_number).exists():
            messages.error(request, _('A school with number %(number)s already exists.') % {'number': school_number})
        else:
            school = School.objects.create(
                name=name,
                school_number=school_number,
                region_id=region_id,
                district_id=district_id,
                jamoat_id=jamoat_id,
                address=address,
                phone=phone,
                email=email,
                student_capacity=student_capacity,
            )
            log_audit(request.user, 'SCHOOL_CREATE', 'School', school.pk, f'Created school {school.name} (#{school.school_number})')
            messages.success(request, _('School "%(name)s" (#%(number)s) has been successfully created.') % {'name': school.name, 'number': school.school_number})
            return redirect('schools:school_list')

    regions = Region.objects.filter(is_active=True)
    districts = District.objects.filter(is_active=True)
    jamoats = Jamoat.objects.filter(is_active=True)
    return render(request, 'schools/school_form.html', {
        'title': _('Create School'),
        'regions': regions,
        'districts': districts,
        'jamoats': jamoats,
    })


@login_required
def school_detail_view(request, pk):
    school = get_object_or_404(School.objects.select_related('region', 'district', 'jamoat'), pk=pk)
    user = request.user

    # Territorial permission check
    if user.role == 'SUPER_ADMIN':
        pass
    elif user.role == 'DISTRICT_CHAIRMAN' and school.district != user.district:
        return HttpResponseForbidden(_('Access denied.'))
    elif user.role == 'JAMOAT_CHAIRMAN' and school.jamoat != user.jamoat:
        return HttpResponseForbidden(_('Access denied.'))
    elif user.role in ['SCHOOL_DIRECTOR', 'LIBRARIAN', 'CLASS_TEACHER', 'STUDENT'] and school != user.school:
        return HttpResponseForbidden(_('Access denied.'))

    # Aggregate stats
    director = User.objects.filter(school=school, role='SCHOOL_DIRECTOR', is_active=True).first()
    librarians = User.objects.filter(school=school, role='LIBRARIAN', is_active=True)
    teachers_count = User.objects.filter(school=school, role='CLASS_TEACHER', is_active=True).count()
    students_count = User.objects.filter(school=school, role='STUDENT', is_active=True).count()
    
    total_books = BookCopy.objects.filter(school=school).count()
    available_books = BookCopy.objects.filter(school=school, status__in=['AVAILABLE', 'AT_LIBRARY']).count()
    issued_books = BookCopy.objects.filter(school=school, status__in=['ISSUED_TO_TEACHER', 'ISSUED_TO_STUDENT']).count()
    lost_books = BookCopy.objects.filter(school=school, status='LOST').count()
    damaged_books = BookCopy.objects.filter(school=school, status='DAMAGED').count()
    classrooms = Classroom.objects.filter(school=school).select_related('academic_year').order_by('grade', 'name')

    return render(request, 'schools/school_detail.html', {
        'school': school,
        'director': director,
        'librarians': librarians,
        'teachers_count': teachers_count,
        'students_count': students_count,
        'total_books': total_books,
        'available_books': available_books,
        'issued_books': issued_books,
        'lost_books': lost_books,
        'damaged_books': damaged_books,
        'classrooms': classrooms,
    })


@login_required
def school_edit_view(request, pk):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        school.name = request.POST.get('name', school.name).strip()
        school.school_number = request.POST.get('school_number', school.school_number).strip()
        school.region_id = request.POST.get('region', school.region_id)
        school.district_id = request.POST.get('district', school.district_id)
        school.jamoat_id = request.POST.get('jamoat', school.jamoat_id)
        school.address = request.POST.get('address', school.address).strip()
        school.phone = request.POST.get('phone', school.phone).strip()
        school.email = request.POST.get('email', school.email).strip()
        school.student_capacity = int(request.POST.get('student_capacity') or school.student_capacity)
        school.is_active = 'is_active' in request.POST
        school.save()
        log_audit(request.user, 'SCHOOL_UPDATE', 'School', school.pk, f'Updated school {school.name} (#{school.school_number})')
        messages.success(request, _('School "%(name)s" has been successfully updated.') % {'name': school.name})
        return redirect('schools:school_list')

    regions = Region.objects.filter(is_active=True)
    districts = District.objects.filter(is_active=True)
    jamoats = Jamoat.objects.filter(is_active=True)
    return render(request, 'schools/school_form.html', {
        'title': _('Edit School'),
        'school': school,
        'regions': regions,
        'districts': districts,
        'jamoats': jamoats,
    })


@login_required
def school_toggle_active_view(request, pk):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        school = get_object_or_404(School, pk=pk)
        school.is_active = not school.is_active
        school.save()
        status_text = _('activated') if school.is_active else _('deactivated')
        log_audit(request.user, 'SCHOOL_TOGGLE_ACTIVE', 'School', school.pk, f'School {school.name} is now {status_text}')
        status_text_en = _('activated') if school.is_active else _('deactivated')
        messages.success(request, _('School "%(name)s" %(status)s.') % {'name': school.name, 'status': status_text_en})
    return redirect('schools:school_list')
