from django.core.management.base import BaseCommand
from main.models import *

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        help = 'Used for faster database reseting for remote functional tests.'

    def handle(self, *args, **options):
        models = [
                  # models to delete
                 ]

        for model in models:
            model.objects.all().delete()

        User.objects.all().exclude(is_superuser=True).delete()
