import time
import json
import requests
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_credentials():
    try:
        with open('credentials.json', 'r') as file:
            data = json.load(file)
        return data['username'], data['password']
    except (FileNotFoundError, KeyError) as e:
        logger.error(f"Error loading credentials: {e}")
        sys.exit(1)

def init_driver(headless=False, driver_path=None):
    try:
        options = Options()
        options.headless = headless  
        if driver_path:
            driver = webdriver.Chrome(executable_path=driver_path, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        
        driver.maximize_window()
        return driver
    except Exception as e:
        logger.error(f"Error initializing WebDriver: {e}")
        sys.exit(1)

def login_to_sauce_demo(driver, username, password):
    try:
        driver.get('https://www.saucedemo.com/')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'user-name'))
        ).send_keys(username)

        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.ID, 'login-button').click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'inventory_list'))
        )
        logger.info("Logged in successfully!")
    except (NoSuchElementException, TimeoutException) as e:
        logger.error(f"Error logging in: {e}")
        driver.quit()
        sys.exit(1)

def fetch_product_details(driver):
    products = {}
    try:
        product_elements = driver.find_elements(By.CLASS_NAME, 'inventory_item')

        for product in product_elements:
            title = product.find_element(By.CLASS_NAME, 'inventory_item_name').text
            description = product.find_element(By.CLASS_NAME, 'inventory_item_desc').text
            price = product.find_element(By.CLASS_NAME, 'inventory_item_price').text
            products[title] = {"description": description, "price": price}
        
        with open('products.json', 'w') as f:
            json.dump(products, f, indent=4)
        
        logger.info("Product details fetched and saved successfully.")
    except (NoSuchElementException, Exception) as e:
        logger.error(f"Error fetching product details: {e}")
        driver.quit()
        sys.exit(1)

def update_product_price():
    try:
        with open('products.json', 'r') as f:
            products = json.load(f)
        
        product_keys = list(products.keys())
        if len(product_keys) >= 3:
            third_product = product_keys[2]
            products[third_product]["price"] = "$100"
            with open('updated_products.json', 'w') as f:
                json.dump(products, f, indent=4)
            logger.info(f"Price of third product '{third_product}' updated to $100.")
        else:
            logger.warning("Less than three products found.")
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error updating product price: {e}")
        sys.exit(1)

def fetch_title_from_api():
    try:
        response = requests.get('https://jsonplaceholder.typicode.com/posts/1')
        if response.status_code == 200:
            data = response.json()
            title = data['title']

            with open('fetch_title.json', 'w') as f:
                json.dump({"title": title}, f, indent=4)
            logger.info("Title fetched from API and saved.")
        else:
            logger.error(f"Error fetching title from API: {response.status_code}")
            raise Exception("API call failed.")
    except requests.RequestException as e:
        logger.error(f"Error during API call: {e}")
        sys.exit(1)

def main():
    headless = '--headless' in sys.argv
    driver_path = None
    if '--driver-path' in sys.argv:
        driver_path = sys.argv[sys.argv.index('--driver-path') + 1]
    
    try:
        username, password = load_credentials()

        driver = init_driver(headless=headless, driver_path=driver_path)
        login_to_sauce_demo(driver, username, password)

        fetch_product_details(driver)

       
        update_product_price()

       
        fetch_title_from_api()

        
        with open('updated_products.json', 'r') as f:
            updated_products = json.load(f)
        
        product_keys = list(updated_products.keys())
        third_product = product_keys[2]
        assert updated_products[third_product]["price"] == "$100", "Price update failed."
        logger.info("Assertion passed: Third product price is $100.")

       
        driver.quit()

    except Exception as e:
        logger.error(f"An error occurred during the execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
