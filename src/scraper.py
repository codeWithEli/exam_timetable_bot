
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
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
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

        #options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-pdf-viewer')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--blink-settings=imagesEnabled=false')

        

        self.driver = webdriver.Chrome(service=service, options=options)
        # self.driver.set_window_size(3000,1500)
        self.driver.get(URL)

        self.wait = WebDriverWait(self.driver, 10)

        self.course_code = input("Please enter course code (eg dcit301): ").replace(" ","")
    
    def click_schedule_gen(self):
        try:
            schedule_gen_xpath = "/html/body/header/nav/div/div[2]/ul/li[4]/a"
            schedule_gen = self.wait.until(EC.presence_of_element_located((By.XPATH, schedule_gen_xpath)))
            schedule_gen.click()
            print("Clicked on schedule generator....")

        except Exception as e:
            print(str(e))
  
    def search_course(self, course_code: str):
        try:
            search_box_xpath = '//*[@id="3"]/div/div[2]/div/form/div[1]/div/div/span/span[1]/span/ul/li/input' 

            self.search_box = self.driver.find_element(By.XPATH, search_box_xpath)
            self.search_box.click()
            self.search_box.send_keys(course_code)
            


        except Exception as e:
            print(str(e))


    def get_batch(self):
        try:
            self.search_course(self.course_code)
            course_list_xpath = '//*[@class="select2-results__options"]'
            
            course_lists = self.wait.until(EC.presence_of_element_located((By.XPATH, course_list_xpath)))
            course_batch = course_lists.find_elements(By.TAG_NAME, 'li')
            self.batch_list = []
            for batch in course_batch:
                self.batch_list.append(batch.text)
            
            print(self.batch_list)

            self.search_box.clear()

            for i in self.batch_list:
                self.search_course(i)
                self.search_box.send_keys(Keys.RETURN)


        except (NoSuchElementException):
            print("No such Element")
            
        except (ConnectionError):
            print("No internet connection")
           
        except Exception as e:
            print(str(e))

    def get_exams_schedule(self):
        try:
            self.get_batch()
            



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
            element = self.wait.until(EC.presence_of_element_located((By.XPATH, exams_card_xpath)))
            
            #self.driver.find_element(By.XPATH, exams_card_xpath)
            element.screenshot(f"./screenshots/{self.course_code}"+".png")
            print('file saved')

        except (TimeoutException):
            print("No internet conection")
        except Exception as e:
            print(str(e))
        
        

    def cleanup(self):
        time.sleep(60)
        self.driver.quit()

    

if __name__ == '__main__':
    scraper = Scraper()
    scraper.click_schedule_gen()
    scraper.get_batch()
    # scraper.get_exams_schedule()
    # scraper.take_screenshot()
    scraper.cleanup()
    