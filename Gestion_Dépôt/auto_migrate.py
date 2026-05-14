import subprocess, sys, os

responses = ['n'] * 300 + ['2'] * 10
response_iter = iter(responses)

def fake_input(prompt=''):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        val = next(response_iter)
        print(val)
        return val
    except StopIteration:
        raise EOFError

import builtins
builtins.input = fake_input

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Gestion_Depot.settings')
sys.argv = ['manage.py', 'makemigrations', 'SGDS', '--name', 'refactor_coulage_par_produit']
exec(open('manage.py').read())
