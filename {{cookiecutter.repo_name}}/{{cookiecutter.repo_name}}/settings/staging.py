# Staging server config
import string
import logging
from {{cookiecutter.repo_name}}.settings.production import *

SECRET_KEY = '' #Update me

# Updated in deployment script
DATABASES["default"]["NAME"] = "{{cookiecutter.repo_name}}"
DATABASES["default"]["USER"] = "{{cookiecutter.repo_name}}"
DATABASES["default"]["PASSWORD"] = ""

ALLOWED_HOSTS = ['staging.{{cookiecutter.domain_name}}', ]

INSTALLED_APPS += (
    'django_nose',
    'django_jenkins',
    'integration_tests',
    'functional_tests',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pyflakes',
    'django_jenkins.tasks.run_sloccount'
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_jslint',
    'django_jenkins.tasks.run_csslint',
)

RAVEN_CONFIG = {
    'dsn': '', # Update me
}

MANDRILL_API_KEY = "" # Update me

if TEST:
    DEBUG = False
    TEMPLATE_DEBUG = False
    logging.disable(logging.CRITICAL)

    # used to check domain is set correctly, getting overriden by deploy script
    DOMAIN = 'staging.{{cookiecutter.domain_name}}'

    PORT = ':8081'
    DOMAIN += PORT
    os.environ["DJANGO_LIVE_TEST_SERVER_ADDRESS"] = DOMAIN
    if not string.count(os.environ["DJANGO_LIVE_TEST_SERVER_ADDRESS"], PORT):
        os.environ["DJANGO_LIVE_TEST_SERVER_ADDRESS"] += PORT

    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )
    TEST_EMAILS_PREFIX = ""
    TEST_EMAILS_DOMAIN = "@test.{{cookiecutter.domain_name}}"

    # Disable HTTPS for tests
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_PROXY_SSL_HEADER = ()
    USE_HTTPS = False
    os.environ['HTTPS'] = "off"

    {% if cookiecutter.use_websockets == "y" %}
    WSGI_APPLICATION = 'ws4redis.django_runserver.application'
    {% endif %}

    PROJECT_APPS = (
        'main',
    )

    SOUTH_TESTS_MIGRATE = False
