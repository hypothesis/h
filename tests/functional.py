import time
from selenium import webdriver, selenium

username = os.environ['SAUCE_USERNAME']
key = os.environ['SAUCE_ACCESS_KEY']

caps = webdriver.DesiredCapabilities.CHROME
caps['platform'] = "Linux"

hub_url = '%s:%s@localhost:4445' % (username, key)
hub_url = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (username, key)
driver = webdriver.Remote(desired_capabilities=caps, command_executor=hub_url)
print "sauce job: https://saucelabs.com/jobs/%s" % driver.session_id

def test_login():
    driver.get("http://test.hypothes.is")
    assert "Hypothesis" in driver.title

    frame = driver.find_elements_by_tag_name('iframe')[0]
    driver.switch_to_frame(frame)

    driver.find_element_by_css_selector(".tri").click()
    driver.find_element_by_link_text('Sign in').click()
    driver.find_element_by_css_selector('input[name="username"]').send_keys("edsu")
    driver.find_element_by_css_selector('input[name="password"]').send_keys("|y(!U#W{s<H})5r{lqX4vb{Te")
    driver.find_element_by_css_selector('input[name="login"]').click()
    time.sleep(10)
    assert driver.find_element_by_css_selector('div[ng-show="persona"] span').text, "edsu"
