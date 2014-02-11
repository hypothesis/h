from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from . import SeleniumTestCase, Annotator

class TestLogin(SeleniumTestCase):

    def test_login(self):
        driver = self.driver
        driver.get(self.base_url + "/")

        # Assert logged in with the right username
        with Annotator(driver):
            self.register()
            self.logout()
            self.login()

            picker = (By.CLASS_NAME, 'user-picker')
            ec = expected_conditions.visibility_of_element_located(picker)
            WebDriverWait(self.driver, 10).until(ec)

            picker = driver.find_element_by_class_name('user-picker')
            dropdown = picker.find_element_by_class_name('dropdown-toggle')
            # Some bugs were fixed in selenium 2.35 + FF23 combo
            # Unfortunately, that means we need test both options
            try:
                self.assertEqual(dropdown.text, "test")
            except AssertionError:
                self.assertEqual(dropdown.text, "test/localhost")


if __name__ == "__main__":
    unittest.main()
