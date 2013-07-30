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
        self.login()
        script = """
            var p = $("p")[0];
            var range = document.createRange();
            range.selectNodeContents(p);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            $(document).mouseup(p);
            """
        driver.execute_script(script)
        # TODO: persist the annotation and check that it is there

if __name__ == "__main__":
    unittest.main()
