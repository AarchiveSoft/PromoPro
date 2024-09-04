"""
this script is intended to make the overview of currently running promotions easier.

TODO:
Filter by Product
Filter by Date
Show all - with sorting option
"""
import datetime
import os
import sqlite3
import sys
import time

from PyQt6.QtWidgets import QWidget

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# create (if necessary) and fill DB
conn = sqlite3.connect('promoProData.db')
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT,
            promo_details TEXT,
            start_date DATE,
            end_date DATE,
            scraped_date DATE
    )
""")
conn.commit()


class App(QWidget):
    """
    Initializes the user interface by creating the GUI and setting up the mode selection.
    """

    def __init__(self):
        super().__init__()
        self.title = "PromoPro"
        self.left = 100
        self.top = 100
        self.width = 250
        self.height = 600

        self.initUI()

    def initUI(self):
        """
        Initializes the user interface by creating the GUI and setting up the mode selection.

        :return: None
        """
        # create GUI
        # mode selection
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        return


class GetPromos():
    """Class for scraping promotion data from a website and storing it in a SQLite database.

    Args:
        None

    Attributes:
        chromedriver_path (str): Path to the Chrome driver executable.
        chrome_options (str): Options for running Chrome browser.
        service (webdriver.chrome.Service): Service for running Chrome driver.
        driver (webdriver.chrome.WebDriver): Chrome driver instance.
        links (List[str]): List of URLs for each brand's promotion page.
        conn (sqlite3.Connection): Connection to the SQLite database.
        cursor (sqlite3.Cursor): Cursor used for executing SQL queries.

    Methods:
        None

    Usage:
        get_promos = GetPromos()
    """

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

    # set webdriverwait
    wait = WebDriverWait(driver, 10)

    # go through pages and gather information
    # list of all brands
    category_links = []

    brand_list = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,
                                                              ".subcategories-listing-container")))
    brands = brand_list.find_elements(By.TAG_NAME, "li")

    for brand in brands:
        link_element = brand.find_element(By.TAG_NAME, "a")
        # DEBUG
        category_title = link_element.get_attribute("title")
        category_link = link_element.get_attribute("href")
        category_links.append(category_link)
        print(f"category_link for <{category_title}> added")

    # scrape data for each category_link
    for i in category_links:
        # get category
        driver.get(i)

        # get products in list of promo included stuff
        product_list = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".row.product-filter-target.productlist.productlist-viewmode.productlist-viewmode-list")))
        products = product_list.find_elements(By.CSS_SELECTOR, "div.content-container")

        # go through products and get various info on each product
        first_link_flag = False
        first_link = ""
        for product in products:
            link_title_element = product.find_element(By.TAG_NAME, "a")
            product_title = link_title_element.get_attribute("title")
            product_link = link_title_element.get_attribute("href")

            if not first_link_flag:
                first_link = product_link
                first_link_flag = True

            price_tax_element = product.find_element(By.CLASS_NAME, "price-tax")

            art_nr_element = price_tax_element.find_element(By.CLASS_NAME, "tax-shipping-hint")
            art_nr_text = art_nr_element.text

            if "Art.Nr.:" in art_nr_text:
                art_nr = art_nr_text.split("Art.Nr.:")[1].split("\n")[0].strip()

            # debug for now
            # print(f"scraped info for {product}: \nTitle: {product_title} \nProduct Link: {product_link} \nArt.-Nr.:
            # {art_nr}")

        # get additional information from the first product (these infos should remain the same over all articles in
        # the category
        driver.get(first_link)
        promo_until = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".specialprice")))
        promo_until_text = promo_until.text
        promo_until_text_date = promo_until_text.split("bis:")[1].strip()
        promo_until_date = time.strptime(promo_until_text_date, "%d.%m.%Y")
        promo_until_datetime = datetime.datetime(*promo_until_date[:6])
        promo_until_date_string = promo_until_datetime.strftime('%Y-%m-%d')

        current_time = datetime.datetime.now()
        current_time_string = current_time.strftime('%Y-%m-%d')

        # print(f"promo until date extracted: {promo_until_date}")

        first_link_flag = False
        first_link = ""

        # fill db with scraped data:
        cursor.execute("""
            INSERT INTO promotions (brand, model, promo_details, start_date, end_date, scraped_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category_title, product_title, '', '1900-01-01', promo_until_date_string, current_time_string))
        conn.commit()

        # print table for now for testing
        cursor.execute('SELECT * FROM promotions')
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    driver.quit()
