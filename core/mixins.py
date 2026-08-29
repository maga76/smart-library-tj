from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only allow logged-in users whose `role` is in `allowed_roles`.

    Anonymous users are redirected to login (like @login_required did).
    Logged-in users with the wrong role get the same "Access denied"
    response the old function-based views returned.
    """
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden(_('Access denied.'))
