from __future__ import absolute_import

{% if cookiecutter.use_celery == "y" %}
from .celery import app as celery_app
{% endif %}
