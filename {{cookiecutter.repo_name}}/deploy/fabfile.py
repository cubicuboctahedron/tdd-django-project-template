import fabtools
import random
import string
from fabric.contrib.files import append, exists, sed
from fabric.contrib.console import confirm
from fabric.context_managers import shell_env
from fabric.api import env, local, run, put, sudo, settings, prefix

# Update these settings manually
env.port = 22 # change this if using non-default SSH port
PRODUCTION_SERVER_IP = 'set me'
REPO_URL = 'set me'
BACKUP_REPO_URL = 'set me'
DEFAULT_USER_PASSWORD = 'changeme'
# 

env.use_ssh_config = True
PROJECT_NAME = {{cookiecutter.repo_name}}
ADMIN_EMAIL = {{cookiecutter.author_name}}
{% if cookiecutter.use_websockets == "y" %}
WITH_WEBSOCKETS = True
{% else %}
WITH_WEBSOCKETS = False
{% endif %}
{% if cookiecutter.use_celery == "y" %}
WITH_CELERY = True
{% else %}
WITH_CELERY = False
{% endif %}

def _get_command(use_sudo):
    if use_sudo:
        return sudo
    else:
        return run

def _configure(host, project_name, repo_url, branch=None, source_folder=None, 
               venv_folder=None, server_port=None, staging=False, demo=False,
               dev=False, db_name=None, user=None, ip=None, backup_on_deploy=True,
               with_websockets=WITH_WEBSOCKETS, with_celery=WITH_CELERY):
    config = {
        'project_name': project_name,
        'repo': repo_url,
        'user_password': DEFAULT_USER_PASSWORD,
        'host': host,
        'staging': staging,
        'demo': demo,
        'dev': dev,
        'branch': branch,
    }
    if config['staging'] or config['demo'] or config['dev']:
        config['production'] = False
    else:
        config['production'] = True

    if ip:
        config['ip'] = ip
    else:
        config['ip'] = PRODUCTION_SERVER_IP

    if db_name:
        config['db_name'] = db_name
    else:
        config['db_name'] = host

    if user:
        config['user'] = user
    else:
        config['user'] = string.replace(host, '.', '_')

    config['server_port'] = server_port
    if not venv_folder:
        config['venv_folder'] = '/sites/'+config['host']
    else:
        config['venv_folder'] = venv_folder
    if not source_folder:
        config['source_folder'] = config['venv_folder']+'/source'
    else:
        config['source_folder'] = source_folder

    config['nginx_folder'] = '/etc/nginx'
    config['initial_data_folder'] = config['source_folder']+'/initial_data'
    config['deploy_folder'] = config['source_folder']+'/deploy'
    config['django_project_folder'] = config['source_folder']+'/'+config['project_name']
    config['django_settings_folder'] = config['django_project_folder']+'/'+config['project_name']+'/settings'
    if dev:
        config['django_settings_name'] = 'dev'
        config['email_subject_prefix'] = 'DEV: '
    elif staging:
        config['django_settings_name'] = 'staging'
    elif demo:
        config['django_settings_name'] = 'demo'
        config['email_subject_prefix'] = 'DEMO: '
    else:
        config['django_settings_name'] = 'production'

    config['django_settings_file_name'] = config['django_settings_folder']+'/'+config['django_settings_name']+'.py'

    config['django_settings_name'] = config['project_name']+'.settings.'+config['django_settings_name']

    config['configs_folder'] = config['deploy_folder']+'/configs'
    config['sources_backup_folder'] = config['venv_folder']+'/source_backup'
    config['db_backup_folder'] = config['venv_folder']+'/backup'
    config['grunt_folder'] = config['django_project_folder']+'/frontend/grunt'

    config['manage_cmd'] = (config['venv_folder']+'/bin/python '
                            +config['django_project_folder']+'/manage.py')

    config['configs'] = {
        'supervisord': config['configs_folder']+'/supervisord.conf',
        'uwsgi': config['configs_folder']+'/supervisord/uwsgi_django.conf'}

    if config['dev']:
        config['configs']['nginx'] = config['configs_folder']+'/nginx-config-template.conf'
    else:
        config['configs']['nginx'] = config['configs_folder']+'/nginx-dev-config-template.conf'

    if config['with_websockets']:
        config['configs']['websockets'] = config['configs_folder']+'/supervisord/uwsgi_websocket.conf'

    if config['with_celery']:
        config['configs']['flower'] = config['configs_folder']+'/supervisord/flower.conf'
        config['configs']['celery'] = config['configs_folder']+'/supervisord/celeryd.conf'

    return config

def unit_test():
    config = _configure(env.host, PROJECT_NAME, REPO_URL)

    # as project user
    with settings(sudo_user=config['user']):
        _unit_test(config)

def _get_source_and_update_env(config):
    with settings(sudo_user=config['user']):
        if config['production'] and config['backup_on_deploy']:
            _backup_database(config)
            _backup_sources(config)
        _get_latest_source(config, config['branch'])
        _update_settings(config)
        _set_current_settings(config)
        _remove_test_domain_settings(config)
        if config['with_celery']:
            _change_celery_broker_queue(config)
        _update_virtualenv(config)
        if not config['production']:
            _disable_search_engine_indexing_for_site(config)

    _install_grunt(config)
    _update_static_files(config)

def update(branch=None, staging=False, demo=False, dev=False):
    config = _configure(env.host, PROJECT_NAME, REPO_URL, 
                        staging=staging, branch=branch, demo=demo, dev=dev)
    if not dev:
        sudo('supervisorctl stop uwsgi_django-'+config['host'])
    else:
        sudo('supervisorctl stop django-'+config['host'])
    
    _get_source_and_update_env(config)

    with settings(sudo_user=config['user']):
        _update_database(config)
        if not config['dev']:
            _update_config_templates(config)
        if not config['production']:
            _update_nginx_config_site_url(config)

        _update_email_subject(config)

        if config['dev']:
            sudo('rm -rf '+config['django_project_folder']+'/static/main')

    # as root
    if not config['dev']:
        _copy_supervisord_configs(config)

    _copy_nginx_config(config)
    _restart_services(config)

def deploy(branch=None, staging=False, demo=False, dev=False):
    config = _configure(env.host, PROJECT_NAME, REPO_URL, 
                        staging=staging, demo=demo, dev=dev, branch=branch)
    
    # as root
    _create_user(config)

    with settings(sudo_user=config['user']):
        _copy_deployment_key(config)

    _get_source_and_update_env(config)

    with settings(sudo_user=config['user']):
        _create_log_dirs(config)
        _create_media_dirs(config)
        _update_fixture_template(
            config, 
            fixture=config['initial_data_folder']+'/sites.json_template')
        _update_database(config)
        _load_fixtures(config, 
                       fixture=config['initial_data_folder']+'/sites.json')

        _update_config_templates(config)
        _update_email_subject(config)
        if not config['production']:
            _update_nginx_config_site_url(config)

    # as root
    _copy_supervisord_configs(config)

    _copy_nginx_config(config)
    _restart_services(config)

def ci_deploy(source_folder, venv_folder, server_port, branch=None):
    config = _configure(env.host, PROJECT_NAME, REPO_URL, 
                        source_folder=source_folder, venv_folder=venv_folder, 
                        server_port=server_port, staging=True,
                        db_name=PROJECT_NAME, user='jenkins')

    _update_virtualenv(config, use_sudo=False)
    _install_grunt(config, use_sudo=False)
    _update_settings(config, use_sudo=False)
    _set_current_settings(config, use_sudo=False)
    _update_database(config, use_sudo=False)
    _update_fixture_template(
        config, fixture=config['initial_data_folder']+'/sites.json_template', 
        use_sudo=False)
    _load_fixtures(
        config, fixture=config['initial_data_folder']+'/sites.json', 
        use_sudo=False)
    _update_static_files(config, use_sudo=False)

def update_fixtures():
    config = _configure(env.host, PROJECT_NAME, REPO_URL, staging=True)

    _update_email_prefix_in_fixtures(config)

def shutdown():
    config = _configure(env.host, PROJECT_NAME, REPO_URL)

    _shutdown_site(config)

def _create_user(config):
    if not fabtools.user.exists(config['user']):
        fabtools.user.create(config['user'], create_home=True, system=True,
                             extra_groups=['www-data',])
        fabtools.postgres.create_user(
            config['user'], password=config['user_password'], createdb=True)
        
def _copy_deployment_key(config):
    ssh_dir = '/home/{}/.ssh'.format(config['user'])
    key_file_name = config['project_name']+'_deployment.key'
    if not exists(ssh_dir):
        sudo('mkdir -p %s' % ssh_dir)
        sudo('chmod 700 %s' % ssh_dir)
    if not exists(ssh_dir+'/'+key_file_name):
        with settings(sudo_user='root'):
            put('keys/deployment.key', 
                ssh_dir+'/'+key_file_name, use_sudo=True, mode=0600)
            sudo('chown {user}:{group} {ssh_dir}/{key}'.format(
                user=config['user'], group=config['user'], 
                ssh_dir=ssh_dir, key=key_file_name))

        bitbucket_config = ('Host bitbucket.org\n'
                            '    HostName bitbucket.org\n'
                            '    IdentityFile '+ssh_dir+'/'+key_file_name+'\n')
        sudo('echo \''+bitbucket_config+'\' >> '+ssh_dir+'/config')

        github_config = ('Host github.com\n'
                         '    HostName github.com\n'
                         '    IdentityFile '+ssh_dir+'/'+key_file_name+'\n')
        sudo('echo \''+github_config+'\' >> '+ssh_dir+'/config')

def _get_latest_source(config, branch):
    if exists(config['source_folder'] + '/.git'):
        sudo('cd %s && git reset --hard' % config['source_folder'])
        sudo('cd %s && git clean -fd' % config['source_folder'])
        sudo('cd %s && git submodule foreach --recursive git reset --hard' % config['source_folder'])
        sudo('cd %s && git submodule foreach --recursive git clean -fd' % config['source_folder'])
        sudo('cd %s && git fetch --recurse-submodules=yes' % config['source_folder'])
        sudo('cd %s && git submodule update --init --remote --recursive' % config['source_folder'])
    else:
        if branch:
            sudo('git clone --recursive -b %s %s %s' % (branch, config['repo'], 
                                            config['source_folder']))
        else:
            sudo('git clone --recursive %s %s' % (config['repo'], 
                                                  config['source_folder']))
    current_commit = local("git log -n 1 --format=%H", capture=True)
    sudo('cd %s && git reset --hard %s' % (config['source_folder'], 
         current_commit))

def _update_settings(config, use_sudo=True):
    sed(config['django_settings_file_name'],
        'DATABASES\[\"default\"\]\[\"NAME\"\] =.+$',
        'DATABASES\[\"default\"\]\[\"NAME\"\] = \"{}\"'.format(config['db_name']),
        use_sudo=use_sudo)
    sed(config['django_settings_file_name'],
        'DATABASES\[\"default\"\]\[\"USER\"\] =.+$',
        'DATABASES\[\"default\"\]\[\"USER\"\] = \"{}\"'.format(config['user']),
        use_sudo=use_sudo)
    sed(config['django_settings_file_name'],
        'DATABASES\[\"default\"\]\[\"PASSWORD\"\] =.+$',
        'DATABASES\[\"default\"\]\[\"PASSWORD\"\] = \"{}\"'.format(
            config['user_password']),
        use_sudo=use_sudo)

    sed(config['django_settings_file_name'], ' DOMAIN = .+$', 
        ' DOMAIN = "%s"' % config['host'], use_sudo=use_sudo)
    sed(config['django_settings_file_name'],
        'ALLOWED_HOSTS =.+$',
        'ALLOWED_HOSTS = ["{0}", "www.{0}", ]'.format(
            config['host']), use_sudo=use_sudo)

def _set_current_settings(config, use_sudo=True):
    cmd = _get_command(use_sudo)
    cmd('ln -fs '+config['django_settings_file_name']+' '
         +config['django_project_folder']+'/'
         +config['project_name']+'/current_settings.py')
    
def _remove_test_domain_settings(config, use_sudo=True):
    sed(config['django_settings_file_name'], "DOMAIN \+= PORT", "", 
        use_sudo=use_sudo)
    sed(config['django_settings_file_name'], 
        'os.environ["DJANGO_LIVE_TEST_SERVER_ADDRESS"] .+$', 
        "", use_sudo=use_sudo)

def _update_email_subject(config, use_sudo=True):
    sed(config['django_settings_file_name'], "EMAIL_SUBJECT_PREFIX =.+$", 
        "EMAIL_SUBJECT_PREFIX = \""+config['email_subject_prefix']+"\"", 
        use_sudo=use_sudo)

def _change_celery_broker_queue(config):
    celery_config_path = config['django_settings_folder']+'/../celery.py'
    sed(celery_config_path, '"default"', '"{}"'.format(config['host']), 
        use_sudo=True)

def _update_config_templates(config):
    for config_file in config['configs'].itervalues():
        sed(config_file, "SITE_NAME", config['host'], use_sudo=True)
        sed(config_file, "SITE_IP", config['ip'], use_sudo=True)
        sed(config_file, "USER", config['user'], use_sudo=True)
        sed(config_file, "PROJECT_NAME", config['project_name'], use_sudo=True)
        sed(config_file, "PROJECT_DIRECTORY", config['django_project_folder'], 
            use_sudo=True)
        sed(config_file, "VIRTUALENV_DIRECTORY", config['venv_folder'], 
            use_sudo=True)
        sed(config_file, "DEPLOY_DIRECTORY", config['deploy_folder'], 
            use_sudo=True)
        sed(config_file, "ADMIN_EMAIL", ADMIN_EMAIL, use_sudo=True)

def _update_fixture_template(config, fixture, use_sudo=True):
    new_fixture_path = fixture.replace('_template', '')
    sed(fixture, "SITE_NAME", config['host'], use_sudo=use_sudo)
    try: 
        port = ':'+config['server_port']
    except:
        port = ''
    sed(fixture, "PORT", port, use_sudo=use_sudo)
    sed(fixture, "PROJECT_NAME", config['project_name'], use_sudo=use_sudo)

    cmd = _get_command(use_sudo)
    cmd('mv '+fixture+' '+new_fixture_path)

def _disable_search_engine_indexing_for_site(config, use_sudo=True):
    sed(config['django_project_folder']+'/templates/base.html', 
        '<head>', '<head><meta name="robots" content="none" />',
        use_sudo=use_sudo)

def _update_nginx_config_site_url(config):
    sed(config['configs']['nginx'], "www\.", "", use_sudo=True)

def _copy_nginx_config(config):
    sudo('cp '+config['configs']['nginx']+' '+config['nginx_folder']+'/conf.d/'+config['host']+'.conf')

def _copy_supervisord_config(config):
    configs = config['configs'].copy()
    configs.pop('nginx')
    sudo('cp '+configs.pop('supervisord')+' /etc/supervisor/supervisord.conf')

    config_dir = '/etc/supervisor/conf.d/{}'.format(config['host'])
    sudo('mkdir -p {}'.format(config_dir))

    for config in configs.itervalues():
        sudo('cp '+config+' '+config_dir+'/')

def _update_virtualenv(config, use_sudo=True):
    cmd = _get_command(use_sudo)
    if not exists(config['venv_folder'] + '/bin/pip'):
        cmd('virtualenv %s' % (config['venv_folder'],))

    cmd('%s/bin/pip install -r %s/requirements.txt' % (
            config['venv_folder'], config['source_folder']
    ))

def _update_static_files(config, use_sudo=True):
    cmds = (config['manage_cmd']+" bower install",
            "cd "+config['grunt_folder']+" && grunt all --noinput",
            config['manage_cmd']+" collectstatic --noinput")

    for cmd in cmds:
        if use_sudo:
            sudo("su - {username} -c '{command}'".format(username=config['user'],
                                                         command=cmd))
        else:
            run(cmd)

def _backup_database(config, use_sudo=True):
    cmd = _get_command(use_sudo)
    if fabtools.postgres.database_exists(config['db_name']):
        fabtools.require.git.working_copy(BACKUP_REPO_URL, 
                                          path=config['db_backup_folder'],
                                          update=True,
                                          use_sudo=use_sudo)
        cmd('pg_dump -U {} -Fc {} > {}'.format(
            config['user'], config['db_name'],
            config['db_backup_folder']+'/'+config['db_name']+'.dump'))
        try:
            cmd('cd {} && git -c user.name="Fabric" -c user.email={}@{} '
                'commit -a -m "backing up before deploy"'.format(
                    config['db_backup_folder'], config['project_name'], 
                    config['host']))
        except:
            pass
        cmd('cd {} && git push'.format(config['db_backup_folder']))

def _backup_sources(config, use_sudo=True):
    cmd = _get_command(use_sudo)
    cmd('rm -rf {}'.format(config['sources_backup_folder']))
    cmd('cp -rf {} {}'.format(config['django_project_folder'], 
                              config['sources_backup_folder']))

def _update_database(config, use_sudo=True):
    cmd = _get_command(use_sudo)
    if not fabtools.postgres.database_exists(config['db_name']):
        fabtools.postgres.create_database(config['db_name'], config['user'])
        cmd(config['manage_cmd']+' syncdb --all --noinput')
        cmd(config['manage_cmd']+' migrate --fake --noinput')
    else:
        cmd(config['manage_cmd']+' migrate --noinput')

def _load_fixtures(config, fixture, use_sudo=True):
    cmd = _get_command(use_sudo)
    cmd(config['manage_cmd']+' loaddata '+fixture)

def _create_log_dirs(config):
    sudo('mkdir -p '+config['venv_folder']+'/logs')

def _create_media_dirs(config):
    sudo('mkdir -p '+config['django_project_folder']+'/media/uploads')

def _restart_services(config):
    if not sudo('pgrep supervisord'):
        sudo('service start supervisord')

    sudo('supervisorctl reread')
    sudo('supervisorctl update')
    if not config['dev']:
        sudo('supervisorctl restart uwsgi_django-'+config['host'])
        sudo('supervisorctl restart uwsgi_websocket-'+config['host'])
    else:
        sudo('supervisorctl restart django-'+config['host'])
    sudo('supervisorctl restart celery-'+config['host'])

    if not sudo('pgrep nginx'):
        sudo('service nginx start')
    else:
        print "Nginx already running"
        sudo('service nginx reload')

def _shutdown_site(config):
    sudo('supervisorctl stop uwsgi_django-'+config['host'])
    sudo('supervisorctl stop uwsgi_websocket-'+config['host'])
    sudo('supervisorctl stop celery-'+config['host'])

def _unit_test(config):
    sudo('cd '+config['django_project_folder']+' && '
         +config['manage_cmd']+' test --noinput main.tests')
    sudo('cd '+config['django_project_folder']+' && '
         +config['manage_cmd']+' test --noinput integration_tests')

def _install_grunt(config, use_sudo=True):
    cmd = 'cd '+config['grunt_folder']+' && npm install'
    if use_sudo:
        sudo("su - {username} -c '{command}'".format(username=config['user'],
                                                     command=cmd))
    else:
        run(cmd)
