import sys
import requests
import time
import os
import poplib
import email
import server_tools
from django.test.utils import override_settings
from django.test import LiveServerTestCase
from django.utils import timezone
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from main.models import *
from functional_tests.initial_data import *

DEFAULT_EMAIL_WAIT = 1800
SOCKET_DEFAULT_TIMEOUT = 150
ELEMENT_LOOKUP_TIMEOUT = 30
DEFAULT_WAIT = 5
SCREEN_DUMP_LOCATION = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'screendumps')
)

# Monkeypatch python not to print "Broken Pipe" errors to stdout.
import SocketServer
from wsgiref import handlers
SocketServer.BaseServer.handle_error = lambda *args, **kwargs: None
handlers.BaseHandler.log_exception = lambda *args, **kwargs: None


class FunctionalTestObjectsMixin(object):

    def create_object(self, name=OBJECT_TEST_DATA['name']):
        if self.against_staging:
            print '\n{}: going to create object'.format(
                timezone.now().strftime('%H:%M:%S'))
            self.login_admin()

            b = self.browser
            self.get(self.server_url + '/admin/')
            # optimized to work with django suit
            self.click(By.XPATH,
                       '//tr[contains(.,"Jet operator companies")]'
                       '//a[contains(.,"Add")]')

            b.find_element_by_id('id_name').send_keys(name)

            self.click(By.XPATH, '//button[@name="_save"]')
            self.assertIn('was added successfully.',
                          self.wait_for_element_with_xpath('//div[contains(@class, "alert")]').text)

            print '{}: done'.format(
                timezone.now().strftime('%H:%M:%S'))
        else:
            """
            Object.objects.get_or_create(name=name)[0]
            """

        return name

    def create_superuser(self, email=ADMIN_TEST_DATA['email'],
                         password=ADMIN_TEST_DATA['password'],
                         first_name=ADMIN_TEST_DATA['first_name'],
                         last_name=ADMIN_TEST_DATA['last_name'],
                         phone=ADMIN_TEST_DATA['phone']):
        if self.against_staging:
            print '\n{}: going to create admin'.format(
                timezone.now().strftime('%H:%M:%S'))
            server_tools.create_superuser(self.server_host, email, password,
                                          first_name, last_name)
            print '{}: done'.format(
                timezone.now().strftime('%H:%M:%S'))
        else:
            user = User(email=email, first_name=first_name,
                        last_name=last_name, is_staff=True,
                        is_superuser=True, is_active=True)
            user.save()
            user.set_password(password)
            user.save()

        return email


class WaitForObjectMixin(object):

    def wait_for_element(self, lookup_type, locator,
                         timeout=ELEMENT_LOOKUP_TIMEOUT,
                         expected_condition=EC.visibility_of_element_located):
        return WebDriverWait(self.browser, timeout).until(
            expected_condition((lookup_type, locator)),
            u'Could not find element by {}: {}.'.format(lookup_type, locator)
        )

    def wait_for_element_with_id(self, element_id, *args, **kwargs):
        return self.wait_for_element(By.ID, element_id, *args, **kwargs)

    def wait_for_link(self, link_name, *args, **kwargs):
        return self.wait_for_element(By.LINK_TEXT, link_name, *args, **kwargs)

    def wait_for_link_contains_text(self, link_name, *args, **kwargs):
        return self.wait_for_element(By.PARTIAL_LINK_TEXT, link_name, *args, **kwargs)

    def wait_for_element_with_xpath(self, xpath, *args, **kwargs):
        return self.wait_for_element(By.XPATH, xpath, *args, **kwargs)

    def wait_for_element_with_name(self, name, *args, **kwargs):
        return self.wait_for_element(By.NAME, name, *args, **kwargs)

    def wait_for_element_with_css(self, name, *args, **kwargs):
        return self.wait_for_element(By.CSS_SELECTOR, name, *args, **kwargs)

    def wait_for_element_with_xpath_to_hide(self, xpath, *args, **kwargs):
        return self.wait_for_element(
            By.XPATH, xpath,
            expected_condition=EC.invisibility_of_element_located, *args, **kwargs)

    def wait_for_element_with_id_to_hide(self, element_id, *args, **kwargs):
        return self.wait_for_element(
            By.ID, element_id,
            expected_condition=EC.invisibility_of_element_located, *args, **kwargs)

    def wait_for_element_count_to_be(
            self, lookup_type, locator, count, timeout=ELEMENT_LOOKUP_TIMEOUT):
        elements = WebDriverWait(self.browser, timeout).until(
            lambda b: len(b.find_elements(lookup_type, locator)) == count,
            u'Element count was {} (expected {})'.format(
                len(self.browser.find_elements(lookup_type, locator)), count)
        )

    def wait_for_element_with_xpath_count_to_be(self, xpath, count, **kwargs):
        self.wait_for_element_count_to_be(By.XPATH, xpath, count, **kwargs)

    def wait_for_element_with_name_count_to_be(self, name, count, **kwargs):
        self.wait_for_element_count_to_be(By.NAME, name, count, **kwargs)

    def wait_for_element_with_css_count_to_be(self, name, count, **kwargs):
        self.wait_for_element_count_to_be(
            By.CSS_SELECTOR, name, count, **kwargs)

    def wait_for_element_with_xpath_to_be_selected(self, xpath, *args, **kwargs):
        return self.wait_for_element(By.XPATH, xpath,
                                     expected_condition=EC.element_located_to_be_selected, *args, **kwargs)

    def assertPageHasTitle(self, header_xpath):
        start_time = time.time()
        while time.time() - start_time < ELEMENT_LOOKUP_TIMEOUT * 3:
            try:
                element = self.wait_for_element_with_xpath(header_xpath)
            except TimeoutException:
                print ('{}: got timeout while trying to find header "{}", '
                       'retrying'.format(timezone.now().strftime('%H:%M:%S'),
                                         header_xpath))
                interval = +ELEMENT_LOOKUP_TIMEOUT
                continue
            else:
                return


@override_settings(CELERY_ALWAYS_EAGER=True)
class FunctionalTest(FunctionalTestObjectsMixin, WaitForObjectMixin,
                     LiveServerTestCase):
    errors_count = 0

    @classmethod
    def setUpClass(cls):
        cls.against_staging = False
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_host = arg.split('=')[1]
                cls.server_url = 'https://' + cls.server_host
                cls.against_staging = True

        phantomjs_args = ['--ignore-ssl-errors=yes',
                          '--web-security=false',
                          ]
        if cls.against_staging:
            phantomjs_args.append('--ssl-protocol=tlsv1')

        cls.browser = webdriver.PhantomJS(service_args=phantomjs_args)
        cls.browser.set_window_size(1368, 768)

        if not cls.against_staging:
            cls.fixtures = ['sites.json', ]
            super(FunctionalTest, cls).setUpClass()
            cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if not cls.against_staging:
            super(FunctionalTest, cls).tearDownClass()
        cls.browser.quit()

    @staticmethod
    def _test_has_failed(instance):
        errors_and_fails_count = len(instance._resultForDoCleanups.errors) \
            + len(instance._resultForDoCleanups.failures)
        if errors_and_fails_count > FunctionalTest.errors_count:
            FunctionalTest.errors_count = errors_and_fails_count
            return True
        return False

    def setUp(self):
        print '{}: {} started'.format(
            timezone.now().strftime('%H:%M:%S'), self.id())

        if self.against_staging:
            server_tools.reset_database(self.server_host)
        else:
            self.create_superuser()
        self.logged_in = False
        self.admin_logged_in = False
        return super(FunctionalTest, self).setUp()

    def tearDown(self):
        if FunctionalTest._test_has_failed(self):
            if not os.path.exists(SCREEN_DUMP_LOCATION):
                os.makedirs(SCREEN_DUMP_LOCATION)
            for ix, handle in enumerate(self.browser.window_handles):
                self._windowid = ix
                self.browser.switch_to.window(handle)
                self.take_screenshot()
                self.dump_html()
        self.logout()
        super(FunctionalTest, self).tearDown()
        print '{}: {} stopped'.format(
            timezone.now().strftime('%H:%M:%S'), self.id())
        print '--------------------------------------------------'

    def _wait_for_get(self, url):
        print '{}: trying to open url {}'.format(
            timezone.now().strftime('%H:%M:%S'), url)
        try:
            self.browser.get(url)
            print '{}: opened url {}'.format(
                timezone.now().strftime('%H:%M:%S'), url)
            return True
        except TimeoutException:
            print '{}: got timeout for url {} '.format(
                timezone.now().strftime('%H:%M:%S'), url)
            return False

    def click(self, lookup_type, lookup_string):
        start_time = time.time()
        element = self.wait_for_element(lookup_type, lookup_string)
        while time.time() - start_time < ELEMENT_LOOKUP_TIMEOUT * 3:
            try:
                element.find_elements_by_id('doesnt-matter')
            except StaleElementReferenceException:
                return

            if len(element.text):
                print '{}: clicking link with text "{}"'.format(
                    timezone.now().strftime('%H:%M:%S'),
                    element.text.encode('utf-8').replace('\n', ' '))
            else:
                try:
                    if len(element.get_attribute('value')):
                        print '{}: clicking button with value "{}"'.format(
                            timezone.now().strftime('%H:%M:%S'),
                            element.get_attribute('value'))
                except:
                    print '{}: clicking element without text or value'.format(
                        timezone.now().strftime('%H:%M:%S'))

            try:
                element.click()
                return
            except TimeoutException:
                print '{}: got timeout for click event'.format(
                    timezone.now().strftime('%H:%M:%S'))

            element = self.wait_for_element(lookup_type, lookup_string)

    def get(self, url):
        self.browser.set_page_load_timeout(30)

        while not self._wait_for_get(url):
            pass

    def _get_filename(self):
        timestamp = timezone.now().isoformat().replace(':', '.')[:19]
        site_name = self.server_url.replace(
            "http://", "").replace("https://", "")
        return ('{folder}/{timestamp}-{site}-{classname}.{method}-'
                'window{windowid}'.format(
                    folder=SCREEN_DUMP_LOCATION,
                    timestamp=timestamp,
                    site=site_name[0],
                    classname=self.__class__.__name__,
                    method=self._testMethodName,
                    windowid=self._windowid,
                ))

    def take_screenshot(self):
        filename = self._get_filename() + '.png'
        self.browser.get_screenshot_as_file(filename)

    def dump_html(self):
        filename = self._get_filename() + '.html'
        with open(filename, 'w') as f:
            f.write(self.browser.page_source.encode('utf8'))

    def logout(self):
        if self.logged_in:
            self.get(self.server_url + '/user/logout')
            self.logged_in = False
            self.admin_logged_in = False
            print '{}: user logged out'.format(
                timezone.now().strftime('%H:%M:%S'))

    def login(self, email, password):
        if self.logged_in:
            self.logout()

# Open main page
        b = self.browser
        self.get(self.server_url + '/user/login')
        self.wait_for_element_with_xpath('//h3[text()="Sign In"]')
# Fill the form
        b.find_element_by_id('login-username').send_keys(email)
        b.find_element_by_id('login-password').send_keys(password)
# Click submit
        self.click(By.XPATH, '//input[@value="Login"]')
# Assert redirected to the Dashboard page
        self.wait_for_element_with_xpath('//h2[text()="Dashboard"]')
        print '{}: user {} logged in'.format(
            timezone.now().strftime('%H:%M:%S'), email)
        self.logged_in = True

    def check_is_in_django_suit(self):
        self.browser.find_element_by_xpath(
            '//h2[text()="Site administration"]')

    def login_to_admin_view(self, email, password):
        if self.logged_in:
            self.logout()

        b = self.browser
        self.get(self.server_url + '/admin/')

        b.find_element_by_id('id_username').send_keys(email)
        b.find_element_by_id('id_password').send_keys(password)
        self.click(By.CSS_SELECTOR, 'input[type="submit"]')

        self.check_is_in_django_suit()
        self.logged_in = True
        print '{}: staff member {} logged in'.format(
            timezone.now().strftime('%H:%M:%S'), email)

    def login_admin(self):
        if not self.admin_logged_in:
            self.login_to_admin_view(ADMIN_TEST_DATA['email'],
                                     ADMIN_TEST_DATA['password'])
            self.admin_logged_in = True

    def copy_current_cookies(self):
        cookies = dict()
        for cookie in self.browser.get_cookies():
            cookies[cookie["name"]] = cookie["value"]

        return cookies

    def POST_with_requests(self, data={}, files={}):
        data['csrfmiddlewaretoken'] = self.browser.find_element_by_xpath(
            "//input[@name='csrfmiddlewaretoken']").get_attribute('value')

        return requests.post(self.browser.current_url,
                             cookies=self.copy_current_cookies(),
                             files=files, data=data, verify=False,
                             headers=dict(Referer=self.browser.current_url))

    def GET_with_requests(self, url):
        return requests.get(url, cookies=self.copy_current_cookies(),
                            verify=False,
                            headers=dict(Referer=self.browser.current_url))


class EmailCheckMixin(object):

    def _connect(self, username, password):
        host = "example.com"
        self.fail('You need to set POP3 email server host')

        self.mail = poplib.POP3_SSL(host)
        self.mail.getwelcome()
        self.mail.user(username)
        self.mail.pass_(password)
        return self.mail

    def _disconnect(self):
        self.mail.quit()

    def _clean_postbox(self, username, password):
        try:
            mail = self._connect(username, password)
        except:
            time.sleep(5)
            mail = self._connect(username, password)
        for email_id in range(1, mail.stat()[0] + 1):
            mail.dele(email_id)
        mail = self._disconnect()

    def clean_admin_postbox(self):
        self._clean_postbox(ADMIN_TEST_DATA['email'],
                            ADMIN_TEST_DATA['password'])

    def _check_for_mail(self, username, password, subject):
        try:
            mail = self._connect(username, password)
        except:
            time.sleep(5)
            mail = self._connect(username, password)

        message_count = mail.stat()[0]
        print "{}: Message count: {}".format(timezone.now().strftime('%H:%M:%S'),
                                             message_count)
        message = u''
        for current_message_id in range(1, message_count + 1):
            for j in mail.retr(current_message_id)[1]:
                message += u"{}\r\n".format(j)

            message = email.message_from_string(message)

            if subject in message['subject']:
                print('Found email with subject: \"{}\"'.format(
                    message['subject']))
                message = message.get_payload(1).get_payload(
                    decode=True).decode('utf-8')
                break
            else:
                print('Skipping email with subject: \"{}\"'.format(
                    message['subject']))
            message = u''

        mail = self._disconnect()
        return message

    def _wait_for_email(self, username, password, subject='',
                        timeout=DEFAULT_EMAIL_WAIT):
        print "\n{}: {}: Checking for mail with subject \"{}\"".format(
            timezone.now().strftime('%H:%M:%S'), username, subject)
        interval = 2
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                message = self._check_for_mail(username, password, subject)
            except:
                time.sleep(5)
                message = self._check_for_mail(username, password, subject)
            if message:
                return message
            time.sleep(interval)
            interval = +5

        self.fail('Email not received')

    def get_admin_email(self, *args, **kwargs):
        return self._wait_for_email(ADMIN_TEST_DATA['email'],
                                    ADMIN_TEST_DATA['password'],
                                    *args, **kwargs)


class Select2(WaitForObjectMixin):

    def __init__(self, browser, field_id):
        self.browser = browser
        element = self.wait_for_element_with_id(
            field_id, expected_condition=EC.presence_of_element_located)
        self.replaced_element = element
        self.element = self.browser.find_element_by_id(
            's2id_{0}'.format(element.get_attribute('id')))

    def click(self):
        click_element = ActionChains(self.browser)\
            .click_and_hold(self.element)\
            .release(self.element)
        click_element.perform()

    def open(self):
        if not self.is_open:
            # PhantomJS workaround
            self.browser.execute_script(
                '$("#{}").data("select2").open()'.format(
                    self.element.get_attribute('id')))

    def close(self):
        if self.is_open:
            self.click(self)

    def select_first(self, entry):
        self.open()
        inputs = self.browser.find_elements_by_xpath(
            '//input[@class="select2-input select2-focused"]')
        for input_field in inputs:
            if input_field.is_displayed():
                input_field.send_keys(entry)
                break
        self.wait_for_element_with_xpath(
            '//li[contains(@class, "select2-results-dept-0")]').click()
        try:
            self.browser.find_element_by_xpath(
                '//input[@class="select2-input select2-focused"]').clear()
        except:
            pass

    @property
    def is_open(self):
        if 'select2-dropdown-open' in self.element.get_attribute("class"):
            return True

        return False

    @property
    def dropdown(self):
        return browser.find_element_by_id('select2-drop')

    @property
    def items(self):
        self.open()
        item_divs = self.dropdown.find_elements_by_css_selector(
            'ul.select2-results li div.select2-result-label')
        return [div.text for div in item_divs]
