# -*- coding: utf-8 -*-
"""
Support for doing Selenium functional tests locally and remotely using
SauceLabs. You should be able to write tests with Selenium IDE, export
them as Python WebDriver scripts, and then modify them to extend
SeleniumTestCase (included below) so that you can easily login as
a test user.

If your test involves clicking around in the Annotator iframe you will
need to use the Annotator context manager to switch to the iframe, since
Selenium IDE doesn't currently handle this. See tests/functional/test_login.py
for an example.

SeleniumTestCase also provides a method to select some text in the page for
annotation, since it seemed impossible to achieve with the Selenium webdriver
API.
"""

import os
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumTestCase(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:4000"
        env = os.environ
        self.driver = webdriver.PhantomJS('./node_modules/.bin/phantomjs')
        self.driver.maximize_window()
        self.verificationErrors = []
        self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()

    def login(self):
        "signs in as test/test@example.org/test"
        driver = self.driver
        with Annotator(driver):
            # Find the signin link and click it
            signin = driver.find_element_by_link_text("Sign in")
            signin.click()

            # Find the authentication form sheet
            auth = driver.find_element_by_class_name('sheet')

            # Find the login pane
            form = auth.find_element_by_name('login')

            username = form.find_element_by_name('username')
            username.clear()
            username.send_keys("test")

            password = form.find_element_by_name('password')
            password.clear()
            password.send_keys("test")

            form.submit()

    def logout(self):
        driver = self.driver
        with Annotator(driver):
            picker = (By.CLASS_NAME, 'user-picker')
            ec = expected_conditions.visibility_of_element_located(picker)
            WebDriverWait(self.driver, 30).until(ec)

            picker = driver.find_element_by_class_name('user-picker')
            dropdown = picker.find_element_by_class_name('dropdown-toggle')
            dropdown.click()
            dropdown.find_element_by_xpath("//li[position()=last()]").click()

    def register(self):
        "registers as test/test@example.org/test"
        driver = self.driver
        with Annotator(driver):
            # Find the signin link and click it
            signin = driver.find_element_by_link_text("Sign in")
            signin.click()

            # Find the authentication form sheet
            auth = driver.find_element_by_class_name('sheet')

            # Switch to the registration tab
            auth.find_element_by_link_text("Create an account").click()

            # Get the registration pane
            form = auth.find_element_by_name('register')

            username = form.find_element_by_name('username')
            username.clear()
            username.send_keys("test")

            email = form.find_element_by_name('email')
            email.clear()
            email.send_keys("test@example.org")

            password = form.find_element_by_name('password')
            password.clear()
            password.send_keys("test")

            form.submit()

            picker = (By.CLASS_NAME, 'user-picker')
            ec = expected_conditions.visibility_of_element_located(picker)
            WebDriverWait(self.driver, 30).until(ec)

    def highlight(self, css_selector):
        """A hack to select some text on the page, and trigger the
        annotator. Ideally this should be achievable with an action chain
        """
        script = """
            var p = $("%s")[0];
            var range = document.createRange();
            range.selectNodeContents(p);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            var offset = $(p).offset();
            window.annotator.plugins.TextAnchors.checkForEndSelection();
            """ % (css_selector,)
        self.driver.execute_script(script)


class Annotator():
    """
    a ContextManager for easily focusing the Selenium driver on the
    Annotator iframe.
    """

    g_state = dict()

    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        # Do nothing if nested
        count = self.g_state.setdefault(self.driver, 0)
        self.g_state[self.driver] = count + 1
        if count > 0:
            return

        driver = self.driver
        container = (By.CLASS_NAME, 'annotator-frame')
        ec = expected_conditions.visibility_of_element_located(container)
        WebDriverWait(driver, 30).until(ec)
        container = driver.find_element_by_class_name('annotator-frame')
        collapsed = 'annotator-collapsed' in container.get_attribute('class')
        if collapsed:
            tb = driver.find_element_by_class_name("annotator-toolbar")
            tb.find_element_by_css_selector('li > a').click()

        ec = expected_conditions.frame_to_be_available_and_switch_to_it(
            'hyp_sidebar_frame')
        WebDriverWait(driver, 30).until(ec)

    def __exit__(self, typ, value, traceback):
        count = self.g_state[self.driver]
        if count == 1:
            del self.g_state[self.driver]
            self.driver.switch_to_default_content()
            self.driver.find_element_by_tag_name('body').click()
