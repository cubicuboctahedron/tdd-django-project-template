# Production server config
from {{cookiecutter.repo_name}}.settings.base import *

SECRET_KEY = ''

ALLOWED_HOSTS = ['{{cookiecutter.domain_name}}', 'www.{{cookiecutter.domain_name}}', ]

# Updated in deployment script
DATABASES["default"]["NAME"] = '{{cookiecutter.repo_name}}'
DATABASES["default"]["USER"] = '{{cookiecutter.repo_name}}'
DATABASES["default"]["PASSWORD"] = ''

# HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
USE_HTTPS = True
os.environ['HTTPS'] = "on"

EMAIL_SUBJECT_PREFIX = '' # Used to distinguish emails in multiple server setup; set by deployment script

if not TEST:
    # Use sentry
    INSTALLED_APPS += (
        'raven.contrib.django.raven_compat',
    )

    MIDDLEWARE_CLASSES = (
        'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
        'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware'
    ) + MIDDLEWARE_CLASSES

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            }
        },
        'root': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'handlers': ['sentry'],
        },
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
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler',
                'include_html': True,
            },
        },
        'loggers': {
            'django.db.backends': {
                'level': 'ERROR',
                'handlers': ['console'],
                'propagate': False,
            },
            'raven': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
            'sentry.errors': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            },
            'django': {
                'handlers': ['console', 'mail_admins', ],
            },
            'main': {
                'handlers': ['console', 'mail_admins', ],
                'level': 'INFO',
            },
            'south': {
                'handlers': None,
            },
            'celery': {
                'level': 'INFO',
                'handlers': ['console', 'sentry'],
                'propagate': False,
            },
        },
    }

    RAVEN_CONFIG = {
        'dsn': '', # Update me
    }
