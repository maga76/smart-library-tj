from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden('Access denied.')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def school_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role in ['SUPER_ADMIN', 'DISTRICT_CHAIRMAN', 'JAMOAT_CHAIRMAN']:
            return view_func(request, *args, **kwargs)
        if not request.user.school:
            return HttpResponseForbidden('No school assigned.')
        return view_func(request, *args, **kwargs)
    return wrapper
