import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django
django.setup()
from django.utils import translation

# Test Tajik
translation.activate('tg')
tests = {
    'Dashboard': translation.gettext('Dashboard'),
    'Sign In': translation.gettext('Sign In'),
    'Schools': translation.gettext('Schools'),
    'Access denied': translation.gettext('Access denied.'),
}
for k, v in tests.items():
    print(f"  tg {k}: {v.encode('utf-8')}")
translation.deactivate()

# Test English
translation.activate('en')
tests2 = {
    'Dashboard': translation.gettext('Dashboard'),
    'Sign In': translation.gettext('Sign In'),
    'Schools': translation.gettext('Schools'),
    'Access denied': translation.gettext('Access denied.'),
}
for k, v in tests2.items():
    print(f"  en {k}: {v}")
translation.deactivate()
