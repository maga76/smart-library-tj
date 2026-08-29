from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.views import View
from .models import AuditLog


class AuditLogListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'SUPER_ADMIN':
            return HttpResponseForbidden(_('Access denied.'))

        logs = AuditLog.objects.select_related('user').all().order_by('-created_at')

        action_filter = request.GET.get('action', '')
        user_filter = request.GET.get('user', '')
        search = request.GET.get('search', '').strip()

        if action_filter:
            logs = logs.filter(action=action_filter)
        if user_filter:
            logs = logs.filter(user__username__icontains=user_filter)
        if search:
            logs = logs.filter(
                Q(description__icontains=search) |
                Q(object_type__icontains=search) |
                Q(object_id__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )

        distinct_actions = AuditLog.objects.values_list('action', flat=True).distinct().order_by('action')

        paginator = Paginator(logs, 40)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'audit/audit_log_list.html', {
            'logs': page_obj,
            'page_obj': page_obj,
            'action_filter': action_filter,
            'user_filter': user_filter,
            'search': search,
            'actions': distinct_actions,
        })
