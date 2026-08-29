"""
Extracts translatable msgid strings referenced via {% trans %} / {% blocktrans %}
across every project template, without requiring the GNU gettext `xgettext`
binary that Django's own `makemessages` command shells out to (and which is
not installed in this environment).

This is a pragmatic regex-based extractor, not a full Django template parser.
It understands the specific subset of i18n tag usage actually used in this
project:
  - {% trans "text" %}
  - {% trans "text" as var %}
  - {% blocktrans %}...{{ var }}...{% endblocktrans %}
  - {% blocktrans asvar name %}...{{ var }}...{% endblocktrans %}
  - {% blocktrans with a=x b=y %}...{{ a }}...{{ b }}...{% endblocktrans %}

For blocktrans blocks, each simple `{{ name }}` reference is rewritten to
Django's actual internal placeholder form `%(name)s`, matching what
BlockTranslateNode builds as its msgid at render time.

Prints the sorted, de-duplicated msgid list. Pass --diff to only show
msgids not already present in locale/ru/LC_MESSAGES/django.po.
"""
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

TRANS_RE = re.compile(r'{%\s*trans\s+"((?:[^"\\]|\\.)*)"')
TRANS_RE_SQ = re.compile(r"{%\s*trans\s+'((?:[^'\\]|\\.)*)'")
BLOCKTRANS_RE = re.compile(r'{%\s*blocktrans[^%]*%}(.*?){%\s*endblocktrans\s*%}', re.DOTALL)
VAR_RE = re.compile(r'{{\s*(\w+)\s*}}')

PY_GETTEXT_RE = re.compile(r'(?<!\w)(?:_|gettext|gettext_lazy)\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
PY_GETTEXT_RE_SQ = re.compile(r"(?<!\w)(?:_|gettext|gettext_lazy)\(\s*'((?:[^'\\]|\\.)*)'\s*\)")


def extract_from_text(text):
    msgids = []
    for m in TRANS_RE.finditer(text):
        msgids.append(m.group(1))
    for m in TRANS_RE_SQ.finditer(text):
        msgids.append(m.group(1))
    for m in BLOCKTRANS_RE.finditer(text):
        block = m.group(1).strip()
        block = re.sub(r'\s+', ' ', block)
        block = VAR_RE.sub(lambda mm: f'%({mm.group(1)})s', block)
        if block:
            msgids.append(block)
    return msgids


class Command(BaseCommand):
    help = 'Extract {% trans %} / {% blocktrans %} msgids from all templates (no gettext binary required).'

    def add_arguments(self, parser):
        parser.add_argument('--diff', action='store_true', help='Only show msgids missing from locale/ru/LC_MESSAGES/django.po')

    def handle(self, *args, **options):
        template_dirs = [Path(settings.BASE_DIR) / 'templates']
        all_msgids = set()
        for td in template_dirs:
            for path in td.rglob('*.html'):
                text = path.read_text(encoding='utf-8')
                for msgid in extract_from_text(text):
                    all_msgids.add(msgid)

        app_names = ['accounts', 'ai_assistant', 'analytics', 'audit', 'geography', 'library', 'schools', 'transactions']
        for app_name in app_names:
            app_dir = Path(settings.BASE_DIR) / app_name
            for path in app_dir.rglob('*.py'):
                if '__pycache__' in path.parts or 'migrations' in path.parts:
                    continue
                text = path.read_text(encoding='utf-8')
                for m in PY_GETTEXT_RE.finditer(text):
                    all_msgids.add(m.group(1))
                for m in PY_GETTEXT_RE_SQ.finditer(text):
                    all_msgids.add(m.group(1))

        if options['diff']:
            import polib
            po_path = Path(settings.BASE_DIR) / 'locale' / 'ru' / 'LC_MESSAGES' / 'django.po'
            existing = set()
            if po_path.exists():
                po = polib.pofile(str(po_path))
                existing = {e.msgid for e in po}
            missing = sorted(all_msgids - existing)
            self.stdout.write(f'{len(missing)} msgid(s) not yet in locale/ru/LC_MESSAGES/django.po:\n')
            for m in missing:
                self.stdout.write(m)
        else:
            self.stdout.write(f'{len(all_msgids)} unique msgid(s) found:\n')
            for m in sorted(all_msgids):
                self.stdout.write(m)
