#!/usr/bin/python
# -*- coding: utf-8 -*-

from functional_tests.base import *


class InstallationTest(FunctionalTest):

    def test_django_default_page(self):
        b = self.browser
        self.get(self.server_url)

        b.wait_for_element_with_xpath('//h1[text()="It worked!"]')
# Done!
