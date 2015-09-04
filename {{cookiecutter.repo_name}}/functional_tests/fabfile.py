import string
from fabric.api import env, run, settings, sudo

env.use_ssh_config = True
env.port = 404

def _get_base_folder(host):
    return '/sites/' + host

def _get_initial_data_folder(host):
    return '{path}/source/initial_data'.format(
        path=_get_base_folder(host)
    )

def _get_manage_dot_py(host):
    return '{path}/bin/python {path}/source/{{cookiecutter.repo_name}}/manage.py'.format(
        path=_get_base_folder(host)
    )

def _get_username(host):
    return string.replace(host, '.', '_')

def reset_database():
    with settings(sudo_user=_get_username(env.host)):
        sudo('{manage_py} ft_reset_database'.format(
            manage_py=_get_manage_dot_py(env.host)
        ))
    
def create_superuser(email, password, first_name, last_name):
    with settings(sudo_user=_get_username(env.host)):
        sudo('{manage_py} ft_createsuperuser --email={email} '
            '--password={password} --first_name={first_name} '
            '--last_name={last_name}'.format(
                manage_py=_get_manage_dot_py(env.host),
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
        ))

def delete_user(email):
    with settings(sudo_user=_get_username(env.host)):
        sudo('{manage_py} ft_deleteuser --email={email}'.format(
                manage_py=_get_manage_dot_py(env.host), email=email,
        ))

def load_fixture(fixture_path):
    with settings(sudo_user=_get_username(env.host)):
        sudo('{manage_py} loaddata {path}/source/{{cookiecutter.repo_name}}/'
             'functional_tests/fixtures/{fixture}'.format(
                manage_py=_get_manage_dot_py(env.host),
                fixture=fixture_path,
                path=_get_base_folder(env.host)
        ))
    
