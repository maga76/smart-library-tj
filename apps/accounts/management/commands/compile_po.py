"""
Compiles every locale/*/LC_MESSAGES/django.po file into a .mo file using the
pure-Python `polib` library.

Django's own `compilemessages` command shells out to the GNU `msgfmt` binary,
which is not installed in this environment. This command provides the same
end result (a compiled .mo catalog Django's translation engine can load)
without requiring any system-level gettext tools.
"""
from pathlib import Path

import polib
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Compile locale/*/LC_MESSAGES/django.po files to .mo using polib (no gettext binary required).'

    def handle(self, *args, **options):
        compiled = 0
        for locale_path in settings.LOCALE_PATHS:
            locale_path = Path(locale_path)
            if not locale_path.exists():
                continue
            for po_path in sorted(locale_path.glob('*/LC_MESSAGES/django.po')):
                po = polib.pofile(str(po_path))
                mo_path = po_path.with_suffix('.mo')
                po.save_as_mofile(str(mo_path))
                self.stdout.write(self.style.SUCCESS(f'Compiled {po_path} -> {mo_path} ({len(po)} entries)'))
                compiled += 1

        if compiled == 0:
            self.stdout.write(self.style.WARNING('No .po files found under LOCALE_PATHS.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDone. Compiled {compiled} locale file(s).'))
