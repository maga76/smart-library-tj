from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from .models import Notification


def _is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user)[:50]
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

        return render(request, 'notifications/notification_list.html', {
            'notifications': notifications,
            'unread_count': unread_count,
        })


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = Notification.objects.filter(pk=pk, recipient=request.user).first()
        if notification:
            notification.is_read = True
            notification.save()
        if _is_ajax(request):
            return JsonResponse({'ok': True})
        return redirect('notifications:notification_list')


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        if _is_ajax(request):
            return JsonResponse({'ok': True})
        return redirect('notifications:notification_list')


class NotificationUnreadCountView(LoginRequiredMixin, View):
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'count': count})
