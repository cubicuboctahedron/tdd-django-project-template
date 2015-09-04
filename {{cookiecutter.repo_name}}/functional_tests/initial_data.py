#!/usr/bin/python
# -*- coding: utf-8 -*-

EMAIL_PREFIX = settings.TEST_EMAILS_PREFIX
EMAIL_DOMAIN = settings.TEST_EMAILS_DOMAIN

OBJECT_TEST_DATA = {
    'name': 'test name'
}

ADMIN_TEST_DATA = {
    'email': EMAIL_PREFIX+'admin'+EMAIL_DOMAIN,
    'first_name': 'Jody',
    'last_name': 'Thornton',
    'password': 'changeme',
}

