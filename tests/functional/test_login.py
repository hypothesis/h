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

        with Annotator(driver):
            driver.find_element_by_css_selector("div.tri").click()
            driver.find_element_by_link_text("Sign in").click()
            driver.find_element_by_link_text("Create an account").click()
            driver.find_element_by_css_selector("form[name=\"register\"] > input[name=\"username\"]").clear()
            driver.find_element_by_css_selector("form[name=\"register\"] > input[name=\"username\"]").send_keys("test")
            driver.find_element_by_css_selector("form[name=\"register\"] > input[name=\"email\"]").clear()
            driver.find_element_by_css_selector("form[name=\"register\"] > input[name=\"email\"]").send_keys("test@example.org")
            driver.find_element_by_css_selector("form[name=\"register\"] > input[name=\"password\"]").clear()
            driver.find_element_by_css_selector("form[name=\"register\"] > input[name=\"password\"]").send_keys("test")
            driver.find_element_by_name("sign_up").click()

            time.sleep(2)

            driver.find_element_by_css_selector("span.dropdown-toggle").click()
            driver.find_element_by_xpath("//li[2]").click()
            driver.find_element_by_link_text("Sign in").click()
            driver.find_element_by_name("username").clear()
            driver.find_element_by_name("username").send_keys("test")
            driver.find_element_by_name("password").clear()
            driver.find_element_by_name("password").send_keys("test")
            driver.find_element_by_css_selector("input[name=\"login\"]").click()

            # wait for the login to take effect via ajax
            time.sleep(5)
            self.assertEqual(driver.find_element_by_css_selector("span.dropdown-toggle").text, "test")

if __name__ == "__main__":
    unittest.main()
