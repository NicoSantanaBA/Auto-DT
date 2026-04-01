import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

@pytest.fixture
def driver():

    download_path = os.path.abspath("downloads")

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    options = webdriver.ChromeOptions()

    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }

    options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.maximize_window()

    yield driver

    driver.quit()