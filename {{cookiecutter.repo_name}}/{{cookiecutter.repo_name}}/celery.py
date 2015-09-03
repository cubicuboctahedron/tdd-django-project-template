from __future__ import absolute_import
import os
from celery import Celery
from kombu import Queue, Exchange
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{{cookiecutter.repo_name}}.current_settings')

app = Celery('main')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.update(
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0",
    BROKER_URL = "redis://localhost:6379/0",
    CELERY_ENABLE_UTC=True,
    CELERY_DEFAULT_QUEUE = "default",
    CELERY_QUEUES = (
        Queue("default", Exchange('celery'), routing_key='direct'),
    ),
    )
if settings.TEST:
    app.conf.update(
        CELERY_RESULT_BACKEND='djcelery.backends.cache:CacheBackend',
        BROKER_URL = 'django://',
    )

