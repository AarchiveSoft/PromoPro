"""
this script is intended to make the overview of currently running promotions easier.

TODO:
Filter by Product
Filter by Date
Show all - with sorting option
"""

import sys
import os
import time

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QWidget, QMainWindow

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = "PromoPro"
        self.left = 100
        self.top = 100
        self.width = 250
        self.height = 600

        self.initUI()

    def initUI(self):
        # create GUI
        # mode selection
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        return

class GetPromos():
    # selenium driver setup - CHROME
    if getattr(sys, "frozen", False):
        # Running as packaged executable, driver is in same directory
        base_path = sys._MEIPASS
    else:
        # Running as normal script, driver is in parent directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        # base_path = os.path.dirname(base_path)
    chromedriver_path = os.path.join(base_path, 'dev', 'chromedriver.exe')
    print(f"chromedriver located at: {chromedriver_path}")
    chrome_options = webdriver.ChromeOptions()
    # dev/chrome-win64/chrome.exe
    chrome_options.binary_location = os.path.join(base_path, 'dev', 'chrome-win64', 'chrome.exe')
    print(f"chrome binary located and constructed path: {chrome_options.binary_location}")

    service = Service(chromedriver_path)

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.graphicart.ch/shop/de/alle-sonderangebote/")
    except Exception as e:
        print(f"there was an issue with the driver: {e}")

    # go through pages and gather information
    # list of all brands
    links = []

    brand_list = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                                                  ".subcategories-listing-container")))
    brands = brand_list.find_elements(By.TAG_NAME, "li")

    for brand in brands:
        link_element = brand.find_element(By.TAG_NAME, "a")
        # DEBUG
        title = link_element.get_attribute("title")
        link = link_element.get_attribute("href")
        links.append(link)
        print(f"link for <{title}> added")

    for i in links:
        driver.get(i)
        time.sleep(0.5)

    driver.quit()