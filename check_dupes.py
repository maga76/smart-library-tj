import polib
from collections import Counter

for lang in ['en', 'ru', 'tg']:
    po = polib.pofile(f'locale/{lang}/LC_MESSAGES/django.po')
    ids = [e.msgid for e in po]
    dupes = [(k,v) for k,v in Counter(ids).items() if v > 1]
    if dupes:
        print(f'{lang}: DUPLICATES:')
        for d, c in dupes:
            print(f'  "{d}" x{c}')
    else:
        print(f'{lang}: no duplicates, {len(po)} entries')
