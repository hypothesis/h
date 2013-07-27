"""
Support for doing Selenium functional tests locally and remotely using 
SauceLabs. You should be able to write tests with Selenium IDE, export
them as Python WebDriver scripts, and then modify them to extend 
SeleniumTestCase (included below) so that a test user is created. 

If your test involves clicking around in the Annotator iframe you will
need to use the Annotator context manager to switch to the iframe, since
Selenium IDE doesn't currently handle this. See tests/functional/test_login.py
for an example.
"""

import os
import json
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

        self.verificationErrors = []
        self.accept_next_alert = True

        # set up a database connection
        self.connection = self.engine.connect()
        self.session = self.Session(bind=self.connection)
        Base.metadata.bind = self.connection
        Base.metadata.create_all(self.engine)

        self._wipe_elastic_search()

    def tearDown(self):
        self.driver.quit()

        # clean out users so subsequent tests can register without collisions
        for user in self.session.query(User).all():
            self.session.delete(user)

    def _wipe_elastic_search(self):
        # TODO: ideally we should be able to use annotator.elasticsearch here
        es_index = settings['es.index'] 
        es_host = settings['es.host']
        # XXX: delete annotations and documents

class Annotator():
    """
    a ContextManager for easily focusing the Selenium driver on the 
    Annotator iframe.
    """

    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        frame = self.driver.find_elements_by_tag_name('iframe')[0]
        self.driver.switch_to_frame(frame)

    def __exit__(self, type, value, traceback):
        self.driver.switch_to_default_content()
