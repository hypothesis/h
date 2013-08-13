from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re

from . import SeleniumTestCase, Annotator

class TestLogin(SeleniumTestCase):

    def test_login(self):
        driver = self.driver
        driver.get(self.base_url + "/")

        self.register()

        with Annotator(driver):
            # Log out
            picker = driver.find_element_by_class_name('user-picker')
            dropdown = picker.find_element_by_class_name('dropdown-toggle')
            dropdown.click()
            dropdown.find_element_by_xpath("//li[2]").click()

        self.login()

        with Annotator(driver):
            picker = driver.find_element_by_class_name('user-picker')
            dropdown = picker.find_element_by_class_name('dropdown-toggle')
            self.assertEqual(dropdown.text, "test")

if __name__ == "__main__":
    unittest.main()
