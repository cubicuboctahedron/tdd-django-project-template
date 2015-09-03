# Base config, everything is inherited from it
import os
import sys
gettext = lambda s: s
BASE_DIR = os.path.dirname(os.path.realpath(os.path.dirname(__file__) + "/.."))

SITE_ID = 1

DEBUG = False
TEMPLATE_DEBUG = False

# Application definition
INSTALLED_APPS = (
    'django.contrib.auth',
    'main',
    'polymorphic',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangobower',
    'django.contrib.sitemaps',
    'robots',
    'sekizai',
    'south',
    'djrill',
    'compressor',
    #'crispy_forms',
    #'reversion',
    #'ws4redis',
    {% if cookiecutter.use_rest_framework == "y" %}
    'oauth2_provider',
    'rest_framework',
    {% endif %}
    #'bootstrap_pagination',
    {% if cookiecutter.use_websockets == "y" %}
    "ws4redis",
    {% endif %}
    {% if cookiecutter.use_celery == "y" %}
    'kombu.transport.django',
    'djcelery_email',
    {% endif %}
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sekizai.context_processors.sekizai',
                {% if cookiecutter.use_websockets == "y" %}
                'ws4redis.context_processors.default',
                {% endif %}
            ],
        },
    },
]

ROOT_URLCONF = '{{cookiecutter.repo_name}}.urls'

WSGI_APPLICATION = '{{cookiecutter.repo_name}}.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (using separate repository for frontend)
STATICFILES_DIRS = (
    ('main', os.path.abspath(os.path.join(BASE_DIR, 'frontend/static'))),
)
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'static'))
STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'compressor.finders.CompressorFinder',
    'djangobower.finders.BowerFinder',
)

# Bower
BOWER_COMPONENTS_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'components'))
BOWER_INSTALLED_APPS = (
)

# Django-compressor
COMPRESS_OUTPUT_DIR = 'cache'
COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)
COMPRESS_JS_FILTERS = [
    'compressor.filters.template.TemplateFilter',
    'compressor.filters.yuglify.YUglifyJSFilter',
]
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.yuglify.YUglifyCSSFilter',
]

# Crispy-forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Media folders
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'media'))
MEDIA_URL = '/media/'
PRIVATE_FILES_MEDIA_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, 'private_media'))

# Email
MANDRILL_API_KEY = "" # Used in production
MANDRILL_TEST_API_KEY = "" # Used in integration tests
{% if cookiecutter.use_celery == "n" %}
# Send emails via Mandrill (djrill package)
EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"
{% else %}
# Send emails with celery delayed task via Mandrill (djrill package)
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERY_EMAIL_BACKEND = "djrill.mail.backends.djrill.DjrillBackend"
# Celery Email Backend 
CELERY_EMAIL_TASK_CONFIG = {
    'default_retry_delay': 600, 
    'max_retries': 3,
}
CELERY_EMAIL_CHUNK_SIZE = 10
{% endif %}

SERVER_EMAIL = 'error-reporting@{{cookiecutter.domain_name}}'
DEFAULT_FROM_EMAIL = '{{cookiecutter.project_name}} <info@{{cookiecutter.domain_name}}>'
ADMINS = (
    ("""{{cookiecutter.author_name}}""", '{{cookiecutter.email}}'),
)
MANAGERS = ADMINS

# Auth
AUTH_USER_MODEL = 'main.User'

LOGIN_URL = '/user/login'
LOGIN_REDIRECT_URL = 'main:index'

{% if cookiecutter.use_websockets == "y" %}
# Websockets
WEBSOCKET_URL = '/ws/'
WS4REDIS_PREFIX = 'ws'
WS4REDIS_EXPIRE = 0
WS4REDIS_HEARTBEAT = 'heartbeat'
from main.websockets import get_allowed_websocket_channels
WS4REDIS_ALLOWED_CHANNELS = get_allowed_websocket_channels
{% endif %}

{% if cookiecutter.use_rest_framework == "y" %}
# REST-Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
}
{% endif %}

# Date formatting
DATETIME_FIELD_FORMAT = '%-d %b %Y %H:%M'

# Testing
if os.path.basename(sys.argv[0]) == 'manage.py' and \
        (sys.argv[1] == 'test' or sys.argv[1] == 'jenkins'):
    TEST = True
else:
    TEST = False
