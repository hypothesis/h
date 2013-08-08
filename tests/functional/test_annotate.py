from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re

from . import SeleniumTestCase, Annotator

class TestAnnotation(SeleniumTestCase):

    def test_annotation(self):
        driver = self.driver
        driver.get(self.base_url + "/")

        # wait a few seconds for the server to warm up & login
        time.sleep(3)
        self.login()

        # highlight the first paragraph and click the pen to annotate it
        self.highlight("p")
        driver.find_element_by_css_selector(".annotator-adder button").click()

        # switch over to the annotator pane and click to save
        with Annotator(driver):
            note = driver.find_element_by_css_selector("textarea")
            note.send_keys("test annotation")
            driver.find_element_by_css_selector("button").click()

        # go away and come back
        driver.get("http://google.com")
        driver.get(self.base_url + "/")

        # make sure the heatmap shows our annotation
        with Annotator(driver):
            # the middle heatmap label should have a "1" in it
            labels = driver.find_elements_by_css_selector(".heatmap-pointer")
            assert len(labels) == 3
            assert labels[1].text == "1"

            # if we click the heatmap we should see our annotation appear
            # make sure the username and text of the annotation are stored
            labels[1].click()
            a = driver.find_elements_by_css_selector(".annotation")
            assert len(a) == 1
            assert a[0].find_element_by_css_selector(".user").text == "test"
            assert a[0].find_element_by_css_selector("markdown div p").text == "test annotation"

if __name__ == "__main__":
    unittest.main()
