import urllib
from inspect import getmembers, isfunction, ismethod
from django.test import TestCase
from django.core.urlresolvers import resolve, reverse
from django.test.client import RequestFactory
from django.contrib.auth.models import update_last_login
from model_mommy import mommy
from main.models import *
from functional_tests.initial_data import *


class ObjectManagementMixin(object):

    def create_superuser(self, *args, **kwargs):
        superuser = mommy.make(User, is_active=True, is_staff=True,
                               is_superuser=True, **kwargs)

        superuser.set_password(DEFAULT_PASSWORD)
        superuser.save()

        return superuser

    def user_login(self, user, password=DEFAULT_PASSWORD):
        self.client.login(username=user.email, password=password)
        update_last_login(self, user)


class EmailTestAssertsMixin(object):

    def assert_email_equal(self, email1, email2):
        self.assertEqual(email1.to, email2.to)
        self.assertEqual(email1.subject, email2.subject)
        self.assertEqual(email1.body, email2.body)
        self.assertEqual(email1.from_email, email2.from_email)
        self.assertEqual(email1.to, email2.to)

    def assert_contains_email_in(self, email, email_list):
        for current_email in email_list:
            if current_email.to == email.to:
                self.assert_email_equal(current_email, email)
                return True

        self.fail('{} not contains in {}'.format(email, email_list))


class MessagesTestAssertsMixin(object):

    def assert_message_count(self, response, expect_num):
        """
        Asserts that exactly the given number of messages have been sent.
        """

        actual_num = len(response.context['messages'])
        if actual_num != expect_num:
            self.fail('Message count was %d, expected %d' %
                      (actual_num, expect_num))

    def assert_message_contains(self, response, text, level=None):
        """
        Asserts that there is exactly one message containing the given text.
        """

        messages = response.context['messages']

        matches = [m for m in messages if text in m.message]

        if len(matches) == 1:
            msg = matches[0]
            if level is not None and msg.level != level:
                self.fail('There was one matching message but with different'
                          'level: %s != %s' % (msg.level, level))

            return

        elif len(matches) == 0:
            messages_str = ", ".join('"%s"' % m for m in messages)
            self.fail('No message contained text "%s", messages were: %s' %
                      (text, messages_str))
        else:
            self.fail('Multiple messages contained text "%s": %s' %
                      (text, ", ".join(('"%s"' % m) for m in matches)))

    def assert_message_not_contains(self, response, text):
        """ Assert that no message contains the given text. """

        messages = response.context['messages']

        matches = [m for m in messages if text in m.message]

        if len(matches) > 0:
            self.fail('Message(s) contained text "%s": %s' %
                      (text, ", ".join(('"%s"' % m) for m in matches)))


class TestAssertsMixin(object):

    def assert404(self, client_request_function):
        self.assertEqual(client_request_function.status_code, 404)

    def assert405(self, client_request_function):
        self.assertEqual(client_request_function.status_code, 405)


class BaseViewTestMixin(MessagesTestAssertsMixin, ObjectManagementMixin,
                        EmailTestAssertsMixin, TestAssertsMixin):
    factory = RequestFactory()

    def test_url_resolves_correctly(self):
        found = resolve(self.view_url)
        self.assertEqual(found.func.__name__, self.view.__name__)


class TemplatedViewTestMixin(BaseViewTestMixin):

    def test_view_uses_correct_template(self):
        response = self.client.get(self.view_url)
        self.assertTemplateUsed(response, self.template_name)


class BaseFormTestMixin(EmailTestAssertsMixin):
    form_class = None
    form_fields = ()
    form_args = {}

    def test_form_contains_all_fields(self):
        form = self.form_class(**self.form_args)
        for field_name in self.form_fields:
            name = field_name[0]
            is_required = field_name[1]

            # check field present
            self.assertNotEqual(form.fields[name], False)
            # check field is required flag
            self.assertEqual(form.fields[name].required, is_required)

        self.assertEqual(len(form.fields), len(self.form_fields))


class LoginRequiredTestMixin(object):

    def test_not_available_for_not_logged_in_user(self):
        self.client.logout()

        response = self.client.get(self.view_url)
        uri = reverse('login') + '?next=' + response.request['PATH_INFO']
        if response.request['QUERY_STRING']:
            uri = '{}%3F{}'.format(uri, urllib.quote(
                response.request['QUERY_STRING']))

        self.assertRedirects(response, uri)


class StaffIsRedirectedToAdminMixin(object):

    def test_redirect_to_admin_if_user_is_staff(self):
        self.client.logout()

        user = self.create_account_manager()
        self.user_login(user)

        response = self.client.get(self.view_url, follow=True)
        self.assertRedirects(response, reverse('admin:index'))


class OrdinaryUsersOnlyTestMixin(StaffIsRedirectedToAdminMixin):
    pass


class BaseModelTestMixin(EmailTestAssertsMixin):

    def test_required_fields_presents(self):
        for field in self.model_fields:
            self.assertIn(field, self.model._meta.get_all_field_names())


def decorate_all_methods(decorator, prefix='test_'):
    """
    decorates all methods in class which begin with prefix test_ to prevent
    accidental external HTTP requests.
    """
    def dectheclass(cls):
        for name, m in getmembers(cls, predicate=lambda x: isfunction(x)
                                  or ismethod(x)):

            if name.startswith(prefix):
                setattr(cls, name, decorator(m))

        return cls

    return dectheclass


class UnitTestCase(ObjectManagementMixin, TestCase):
    pass
