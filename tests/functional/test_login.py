from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re

from . import SeleniumTestCase, Annotator

class Login(SeleniumTestCase):
   
    def test_login(self):
        driver = self.driver
        driver.get("https://localhost:4000/")

        with Annotator(driver):
            driver.find_element_by_css_selector("div.tri").click()
            driver.find_element_by_link_text("Sign in").click()
            driver.find_element_by_name("username").clear()
            driver.find_element_by_name("username").send_keys("test")
            driver.find_element_by_name("password").clear()
            driver.find_element_by_name("password").send_keys("test")
            driver.find_element_by_css_selector("input[name=\"login\"]").click()
            time.sleep(2)
            self.assertEqual(driver.find_element_by_css_selector("span.dropdown-toggle").text, "test")
    
if __name__ == "__main__":
    unittest.main()
