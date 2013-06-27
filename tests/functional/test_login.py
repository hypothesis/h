from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re

from . import SeleniumTestCase, Annotator

class Login(SeleniumTestCase):
   
    def test_login(self):
        driver = self.driver
        driver.get("https://localhost:5000/")

        with Annotator(driver):
            driver.find_element_by_css_selector("div.tri").click()
            driver.find_element_by_link_text("Sign in").click()
            driver.find_element_by_name("username").clear()
            driver.find_element_by_name("username").send_keys("test")
            driver.find_element_by_name("password").clear()
            driver.find_element_by_name("password").send_keys("test")
            driver.find_element_by_css_selector("input[name=\"login\"]").click()
            driver.find_element_by_css_selector("div.annotator-notice.annotator-notice-error").click()

        try: self.assertRegexpMatches(driver.find_element_by_css_selector("BODY").text, r"^[\s\S]*create[\s\S]*$")
        except AssertionError as e: self.verificationErrors.append(str(e))
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
if __name__ == "__main__":
    unittest.main()
