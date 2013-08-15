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
import json
import time
import unittest

import pyes

from selenium import webdriver
from paste.deploy.loadwsgi import appconfig
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

from h.models import Base, User
from annotator.annotation import Annotation
from annotator.document import Document

settings = appconfig('config:test.ini', relative_to='.')

class SeleniumTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = engine_from_config(settings)
        cls.Session = sessionmaker(autoflush=False, autocommit=True)

    def setUp(self):
        self.base_url = "http://localhost:4000"
        env = os.environ

        if env.has_key('SAUCE_USERNAME') and env.has_key('SAUCE_ACCESS_KEY'):
            username = env['SAUCE_USERNAME']
            key = env['SAUCE_ACCESS_KEY']
            caps = webdriver.DesiredCapabilities.FIREFOX
            caps['name'] = str(self)
            caps['platform'] = "Linux"
            caps['build'] = env['TRAVIS_BUILD_NUMBER']
            caps['tags'] = [env['TRAVIS_PYTHON_VERSION'], 'CI']
            caps['tunnel-identifier'] = env['TRAVIS_JOB_NUMBER']

            hub_url = 'http://%s:%s@localhost:4445/wd/hub' % (username, key)
            self.driver = webdriver.Remote(desired_capabilities=caps, command_executor=hub_url)
            self.sauce_url = "https://saucelabs.com/jobs/%s" % self.driver.session_id
        else:
            self.driver = webdriver.Firefox()
            self.driver.implicitly_wait(30)

        self.driver.maximize_window()

        self.verificationErrors = []
        self.accept_next_alert = True

        # set up a database connection
        self.connection = self.engine.connect()
        self.session = self.Session(bind=self.connection)
        Base.metadata.bind = self.connection
        Base.metadata.create_all(self.engine)

        self._wipe()

    def tearDown(self):
        self.driver.quit()
        self._wipe()

    def _wipe(self):
        self._wipe_users()
        self._wipe_elasticsearch()

    def _wipe_elasticsearch(self):
        # TODO: ideally we should be able to use annotator.elasticsearch here
        es_index = settings['es.index']
        es_host = settings['es.host']
        # XXX: delete annotations and documents
        import requests
        url = "%s/%s/annotation/_query?q=*:*" % (es_host, es_index)
        requests.delete(url)

    def _wipe_users(self):
        for user in self.session.query(User).all():
            self.session.delete(user)
        self.session.flush()

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


    def highlight(self, css_selector):
        """A hack to select some text on the page, and trigger the
        annotator. Ideally this should be achievable with an action chain
        """
        script = """
            var p = $("p")[0];
            var range = document.createRange();
            range.selectNodeContents(p);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            var offset = $(p).offset();
            $(".annotator-adder").css({top: offset.top, left: offset.left});
            window.annotator.checkForEndSelection("foobar");
            """
        self.driver.execute_script(script)

class Annotator():
    """
    a ContextManager for easily focusing the Selenium driver on the
    Annotator iframe.
    """

    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        frame = self.driver.find_element_by_class_name('annotator-frame')
        collapsed = 'annotator-collapsed' in frame.get_attribute('class')
        self.driver.switch_to_frame(frame)
        if collapsed:
            self.driver.find_element_by_css_selector("div.tri").click()
            time.sleep(0.5)

    def __exit__(self, typ, value, traceback):
        self.driver.switch_to_default_content()
