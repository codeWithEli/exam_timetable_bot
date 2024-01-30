
import os
import time

import dotenv 
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome  import ChromeDriverManager



dotenv.load_dotenv()
URL = os.getenv("URL")

class Scraper:
    """Scrapper class"""
    def __init__(self):
        """Initialize chrome browser"""

        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions() 

        #browser options
        options.add_experimental_option("detach", True)
        

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(2024,1020)
        self.driver.implicitly_wait(7)

       
    


    def get_page(self):
        try:
            self.driver.get(URL)    

            #click on schedule generator
            element =  self.driver.find_element(By.XPATH, "//li//a[contains(text(),'Schedule Generator')]")

            print(element.text)
            
            
            
            #search for the course



        except Exception as e:
            print(str(e))

    def parse_html(self):
        pass

    def extract_timetable(self):
        pass

    def get_requested_timetable(self):
        pass
    

if __name__ == '__main__':
    scraper = Scraper()
    scraper.get_page()
