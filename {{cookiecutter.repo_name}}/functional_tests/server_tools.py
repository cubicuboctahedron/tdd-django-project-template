from os import path
import subprocess
THIS_FOLDER = path.abspath(path.dirname(__file__))

def reset_database(host):
    subprocess.check_call(
        ['fab', 
         '--hide=everything,status', 
         'reset_database:host={host}'.format(host=host, )],
        cwd=THIS_FOLDER
    )

def create_superuser(host, email, password, first_name, last_name):
    subprocess.check_call(
        ['fab', 
         '--hide=everything,status', 
         'create_superuser:email="{email}",password="{password}",'
         'first_name="{first_name}",last_name="{last_name}",host={host}'.format(
                host=host, email=email, password=password,
                first_name=first_name, last_name=last_name)],
        cwd=THIS_FOLDER
    )

def delete_user(host, email):
    subprocess.check_call(
        ['fab', 
         '--hide=everything,status', 
         'delete_user:email="{email}",host={host}'.format(
                host=host, email=email)],
        cwd=THIS_FOLDER
    )

def load_fixture(host, fixture_path):
    subprocess.check_call(
        ['fab', 
         '--hide=everything,status', 
         'load_fixture:fixture_path="{fixture_path}",host={host}'.format(
                host=host, fixture_path=fixture_path)],
        cwd=THIS_FOLDER
    )

