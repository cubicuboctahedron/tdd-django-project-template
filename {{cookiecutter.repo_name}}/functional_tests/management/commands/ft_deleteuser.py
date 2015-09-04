from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(
            self.UserModel.USERNAME_FIELD)
        self.option_list = BaseCommand.option_list + (
            make_option('--{0}'.format(self.UserModel.USERNAME_FIELD), 
                dest=self.UserModel.USERNAME_FIELD, default=None,
                help='Specifies the login for the test user.'),
        )
        option_list = BaseCommand.option_list
        help = 'Used to delete a user used for remote functional tests.'

    def handle(self, *args, **options):
        username = options.get(self.UserModel.USERNAME_FIELD, None)

        User.objects.filter(email=username).delete()

