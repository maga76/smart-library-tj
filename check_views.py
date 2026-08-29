import py_compile, sys
files = [
    'apps/accounts/views.py',
    'apps/analytics/views.py',
    'apps/geography/views.py',
    'apps/library/views.py',
    'apps/schools/views.py',
    'apps/transactions/views.py',
    'apps/audit/views.py',
]
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f'OK: {f}')
    except py_compile.PyCompileError as e:
        print(f'ERROR: {f}: {e}')
        sys.exit(1)
print('All files compile OK')
