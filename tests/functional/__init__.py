from os import environ as env
from unittest import TestCase
from selenium import webdriver

class SeleniumTestCase(TestCase):

    def setUp(self):
        if env.has_key('SAUCE_USERNAME') and env.has_key('SAUCE_ACCESS_KEY'):
            username = env['SAUCE_USERNAME']
            key = env['SAUCE_ACCESS_KEY']
            caps = webdriver.DesiredCapabilities.FIREFOX
            caps['platform'] = "Linux"
            caps['build'] = env['TRAVIS_BUILD_NUMBER']
            caps['tags'] = [env['TRAVIS_PYTHON_VERSION'], 'CI']
            hub_url = 'http://%s:%s@localhost:4445' % (username, key)
            self.driver = webdriver.Remote(desired_capabilities=caps, command_executor=hub_url)
            self.sauce_url = "https://saucelabs.com/jobs/%s" % self.driver.session_id
        else:
            self.driver = webdriver.Firefox()
            self.driver.implicitly_wait(30)

        self.verificationErrors = []
        self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

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


