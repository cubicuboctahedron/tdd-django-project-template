from {{cookiecutter.repo_name}}.settings.staging import *

SECRET_KEY = '' # Update me

DATABASES["default"]["NAME"] = "{{cookiecutter.repo_name}}"
DATABASES["default"]["USER"] = "{{cookiecutter.repo_name}}"
DATABASES["default"]["PASSWORD"] = ""

DEBUG = True
TEMPLATE_DEBUG = True
INTERNAL_IPS = ['127.0.0.1', '{{cookiecutter.vm_ip}}', ]

# Disable django-compressor for dev environment 
COMPRESS_ENABLED = False
COMPRESS_OUTPUT_DIR = ''
#COMPRESS_PRECOMPILERS = ()
COMPRESS_JS_FILTERS = []
COMPRESS_CSS_FILTERS = []
        
ALLOWED_HOSTS = ['{{cookiecutter.vm_ip}}', ]

if not TEST:
    INSTALLED_APPS += (
        "debug_toolbar",
    )

    MIDDLEWARE_CLASSES = (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ) + MIDDLEWARE_CLASSES

    DEBUG_TOOLBAR_PATCH_SETTINGS = False

# do not post events to sentry
RAVEN_CONFIG = {
    'dsn': ''
}

# log to console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'django': {
            'handlers': ['console', ],
        },
        'south': {
            'handlers': None,
        },
        'main': {
            'handlers': ['console', ],
            'level': 'DEBUG',
        },
        'celery': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

{% if cookiecutter.use_websockets == "y" %}
WSGI_APPLICATION = 'ws4redis.django_runserver.application'
{% endif %}

if TEST:
    COMPRESS_ENABLED = True
    DOMAIN = '{{cookiecutter.vm_ip}}:8081'
    os.environ["DJANGO_LIVE_TEST_SERVER_ADDRESS"] = DOMAIN
    
    # to use postgres in tests, set env variable use_postgres
    # example: use_postgres=1 ./manage.py test
    try:
        os.environ['use_postgres']
        print 'Using postrgresql'
    except:
        # sqlite
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }

    logging.disable(logging.CRITICAL)
