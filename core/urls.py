from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.conf.urls.i18n import i18n_patterns
from accounts import views as account_views


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect(request.user.dashboard_url)
    return redirect('accounts:login')


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root'),
    path('login/', account_views.LoginView.as_view(), name='login'),
    path('logout/', account_views.LogoutView.as_view(), name='logout'),
    path('profile/', account_views.ProfileView.as_view(), name='profile'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('analytics.urls', namespace='analytics')),
    path('geography/', include('geography.urls', namespace='geography')),
    path('schools/', include('schools.urls', namespace='schools')),
    path('library/', include('library.urls', namespace='library')),
    path('transactions/', include('transactions.urls', namespace='transactions')),
    path('ai/', include('ai_assistant.urls', namespace='ai_assistant')),
    path('audit/', include('audit.urls', namespace='audit')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
