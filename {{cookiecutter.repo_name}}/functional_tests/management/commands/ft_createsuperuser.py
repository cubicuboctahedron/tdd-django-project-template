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
                help='Specifies the login for the test superuser.'),
            make_option('--password', dest='password',
                help='Specifies the password for the test superuser.'),
            ) + tuple(
            make_option('--{0}'.format(field), dest=field, default=None,
                help='Specifies the {0} for the test superuser.'.format(
                    field))
            for field in self.UserModel.REQUIRED_FIELDS
        )
        option_list = BaseCommand.option_list
        help = 'Used to create a superuser used for remote functional tests.'

    def handle(self, *args, **options):
        username = options.get(self.UserModel.USERNAME_FIELD, None)
        password = options.get('password')
        first_name = options.get('first_name')
        last_name = options.get('last_name')
        phone = options.get('phone', '')

        try:
            User.objects.get(email=username)
            print 'User {} already exists'.format(username)
        except:
            User.objects.create_superuser(
                username, password, first_name=first_name, 
                last_name=last_name, phone=phone)
            print 'Creating superuser {}'.format(username)

