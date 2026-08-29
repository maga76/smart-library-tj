import re, os

os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Find Cyrillic strings NOT wrapped in trans tags
with open('templates/accounts/login.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    # Skip empty, comments, style/script
    if not stripped:
        continue
    if stripped.startswith('{#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
        continue
    # Find Cyrillic characters
    if re.search(r'[\u0400-\u04ff\u0490-\u04ff]', stripped):
        # Check if inside a {% trans %} tag
        in_trans = '{% trans' in stripped or '{% blocktrans' in stripped
        # Check if it's in a template variable
        in_var = '{{ ' in stripped
        # Check if it's in CSS/JS
        in_css = any(x in stripped for x in ['background', 'color:', 'font-', 'border', 'padding', 'margin', 'width:', 'height:', 'display:', 'position:', 'rgba'])
        in_js = 'function' in stripped or 'var ' in stripped or 'const ' in stripped or 'let ' in stripped or 'document.' in stripped or 'window.' in stripped

        if not in_trans and not in_var and not in_css and not in_js:
            # Strip HTML tags for cleaner output
            clean = re.sub(r'<[^>]+>', '', stripped).strip()
            if clean and re.search(r'[\u0400-\u04ff\u0490-\u04ff]', clean):
                with open('cyrillic_check.txt', 'a', encoding='utf-8') as out:
                    out.write(f'Line {i}: {clean[:150]}\n')

# Clear previous results
with open('cyrillic_check.txt', 'w', encoding='utf-8') as out:
    pass

with open('templates/accounts/login.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith('{#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
        continue
    if re.search(r'[\u0400-\u04ff\u0490-\u04ff]', stripped):
        in_trans = '{% trans' in stripped or '{% blocktrans' in stripped
        in_var = '{{ ' in stripped
        in_css = any(x in stripped for x in ['background', 'color:', 'font-', 'border', 'padding', 'margin', 'width:', 'height:', 'display:', 'position:', 'rgba'])
        in_js = 'function' in stripped or 'var ' in stripped or 'const ' in stripped or 'let ' in stripped or 'document.' in stripped

        if not in_trans and not in_var and not in_css and not in_js:
            clean = re.sub(r'<[^>]+>', '', stripped).strip()
            if clean and re.search(r'[\u0400-\u04ff\u0490-\u04ff]', clean):
                with open('cyrillic_check.txt', 'a', encoding='utf-8') as out:
                    out.write(f'Line {i}: {clean[:150]}\n')

with open('cyrillic_check.txt', 'r', encoding='utf-8') as f:
    print(f.read())
