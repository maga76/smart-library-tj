from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import User
from .forms import LoginForm, UserForm
from apps.audit.utils import log_audit


def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.dashboard_url)
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_audit(user, 'USER_LOGIN', 'User', user.pk, f'User {user.username} logged in.')
            return redirect(user.dashboard_url)
        else:
            messages.error(request, _('Invalid username or password.'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_audit(request.user, 'USER_LOGOUT', 'User', request.user.pk, f'User {request.user.username} logged out.')
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def user_list_view(request):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    
    users = User.objects.all().select_related('region', 'district', 'jamoat', 'school').order_by('-date_joined')
    role_filter = request.GET.get('role', '')
    school_filter = request.GET.get('school', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '').strip()

    if role_filter:
        users = users.filter(role=role_filter)
    if school_filter:
        users = users.filter(school_id=school_filter)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/user_list.html', {
        'users': page_obj,
        'page_obj': page_obj,
        'role_filter': role_filter,
        'school_filter': school_filter,
        'status_filter': status_filter,
        'search': search,
        'roles': User.Role.choices,
    })


@login_required
def user_create_view(request):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            log_audit(
                request.user,
                'USER_CREATE',
                'User',
                new_user.pk,
                f'Created user {new_user.username} with role {new_user.role}.'
            )
            messages.success(request, _('User %(username)s has been successfully created.') % {'username': new_user.username})
            return redirect('accounts:user_list')
    else:
        form = UserForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': _('Create User')})


@login_required
def user_edit_view(request, pk):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    user_obj = get_object_or_404(User, pk=pk)
    old_role = user_obj.role
    old_active = user_obj.is_active

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            updated_user = form.save()
            changes = []
            if old_role != updated_user.role:
                changes.append(f'Role changed from {old_role} to {updated_user.role}')
            if old_active != updated_user.is_active:
                changes.append(f'Active state changed to {updated_user.is_active}')
            
            log_audit(
                request.user,
                'USER_UPDATE',
                'User',
                updated_user.pk,
                f'Updated user {updated_user.username}. {"; ".join(changes)}'
            )
            messages.success(request, _('User %(username)s has been successfully updated.') % {'username': updated_user.username})
            return redirect('accounts:user_list')
    else:
        form = UserForm(instance=user_obj)
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': _('Edit User'),
        'user_obj': user_obj,
    })


@login_required
def user_toggle_active_view(request, pk):
    if request.user.role != 'SUPER_ADMIN':
        return HttpResponseForbidden(_('Access denied.'))
    if request.method == 'POST':
        user_obj = get_object_or_404(User, pk=pk)
        if user_obj == request.user:
            messages.error(request, _('You cannot deactivate yourself.'))
            return redirect('accounts:user_list')
        
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        status_text = _('activated') if user_obj.is_active else _('deactivated')
        log_audit(
            request.user,
            'USER_TOGGLE_ACTIVE',
            'User',
            user_obj.pk,
            f'User {user_obj.username} is now {status_text}.'
        )
        status_text_en = _('activated') if user_obj.is_active else _('deactivated')
        messages.success(request, _('User %(username)s %(status)s.') % {'username': user_obj.username, 'status': status_text_en})
    return redirect('accounts:user_list')
