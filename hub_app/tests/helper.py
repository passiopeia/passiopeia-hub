"""
Test Helper Collection
"""
from django.conf import settings
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver


def firefox_webdriver_factory(accept_language: str = 'en-us, en') -> FirefoxWebDriver:
    """
    Create a firefox webdriver, in headless mode or not, depending on the setting HEADLESS_TEST_MODE
    """
    options = FirefoxOptions()
    options.headless = settings.HEADLESS_TEST_MODE

    profile = FirefoxProfile()
    profile.set_preference('intl.accept_languages', accept_language)
    profile.update_preferences()

    selenium = FirefoxWebDriver(options=options, firefox_profile=profile)
    selenium.implicitly_wait(15)

    return selenium
