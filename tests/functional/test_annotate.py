# -*- coding: utf-8 -*-
import unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from . import SeleniumTestCase, Annotator


class TestAnnotation(SeleniumTestCase):

    def test_annotation(self):
        driver = self.driver
        driver.get(self.base_url + "/")

        self.register()

        # highlight the first paragraph and click the pen to annotate it
        self.highlight("p")
        driver.find_element_by_css_selector(".annotator-adder button").click()

        # switch over to the annotator pane and click to save
        with Annotator(driver):
            annotation = driver.find_element_by_class_name('annotation')
            body = driver.switch_to_active_element()
            body.send_keys("test annotation")
            annotation.find_element_by_css_selector("button").click()

            # Wait for save
            ts = (By.TAG_NAME, "fuzzytime")
            saved = expected_conditions.visibility_of_element_located(ts)
            WebDriverWait(driver, 10).until(saved)

        def get_labels(d):
            return d.find_elements_by_css_selector(".heatmap-pointer")

        # go away and come back
        driver.get(self.base_url + "/")

        # the middle heatmap label should have a "1" in it
        WebDriverWait(driver, 10).until(lambda d: len(get_labels(d)) == 3)
        a_label = get_labels(driver)[1]
        assert a_label.text == "1"

        # if we click the heatmap we should see our annotation appear
        # make sure the username and text of the annotation are stored
        a_label.click()
        with Annotator(driver):
            annotation = (By.CLASS_NAME, 'annotation')
            ec = expected_conditions.visibility_of_element_located(annotation)
            WebDriverWait(driver, 10).until(ec)
            annotation = driver.find_element_by_class_name('annotation')
            user = annotation.find_element_by_class_name('user')
            body = annotation.find_element_by_css_selector('markdown div p')
            assert user.text == 'test'
            assert body.text == 'test annotation'


if __name__ == "__main__":
    unittest.main()
