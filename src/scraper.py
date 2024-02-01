
import os
import time
import logging

import dotenv 
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome  import ChromeDriverManager

from selenium.common.exceptions import NoSuchElementException, TimeoutException



#logger config
# logging.basicConfig(filemode='scraper.log',filemode='w')



#constants
dotenv.load_dotenv()
URL = os.getenv("URL")

class Scraper:
    """Scrapper class"""
    def __init__(self):
        """Initialize and config chrome browser"""

        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions() 

        #persistent browser
        options.add_experimental_option("detach", True)

        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-pdf-viewer')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-dev-shm-usage')
        

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(3000,1500)
        self.driver.get(URL)   

        
    def course_search(self):
        try:
            
        

            #Display all courses
            show_all_course_xpath = "//label//select//option[@value='-1']"
            get_all_course = self.driver.find_element(By.XPATH, show_all_course_xpath)
            time.sleep(1)
            get_all_course.click()

            #Seach for course
            search_box_xpath = "//label//input[@class='form-control input-sm']"
            search_box = self.driver.find_element(By.XPATH, search_box_xpath)
            time.sleep(1)
            search_box.click()

            self.course_code = input("Please enter course code (eg dcit301): ")

            search_box.send_keys(f"{self.course_code}")

            print("Searching for course....")



        except (NoSuchElementException):
            print("Element not found")
        
        except (TimeoutException):
           print("No internet conection")

        except Exception as e:
            print(str(e))


    def get_exams_schedule(self):
        try:

            course_xpath = "//table//td//a"
            exams_details = self.driver.find_element(By.XPATH, course_xpath)
            exams_details.click()
            print(f"Got {self.course_code} scedule taking screenshot....")

        except (NoSuchElementException):
            print("Element not found")

        except Exception as e:
            print(str(e))

    def take_screenshot(self):

        try:
            #scoll to end fo page
            self.driver.find_element(By.XPATH, "/html/body").send_keys(Keys.END)
            time.sleep(1)

            #take screenshot
            exams_card_xpath = "/html/body/div[1]/div[2]/div"
            element = self.driver.find_element(By.XPATH, exams_card_xpath)
            element.screenshot(f"./screenshots/{self.course_code}"+".png")
            print('file saved')

        except (TimeoutException):
            print("No internet conection")
        except Exception as e:
            print(str(e))
        
        

    def cleanup(self):
        
        self.driver.quit()

    

if __name__ == '__main__':
    scraper = Scraper()
    scraper.course_search()
    scraper.get_exams_schedule()
    scraper.take_screenshot()
    scraper.cleanup()
    