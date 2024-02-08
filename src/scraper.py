
import os
import time
import re

import dotenv
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from selenium.common.exceptions import NoSuchElementException, TimeoutException


from firebase_functions import upload_to_firebase_storage


# constants
dotenv.load_dotenv()
URL = os.getenv("URL")


class Scraper:
    """Scraper class"""

    def __init__(self):
        """Initialize and config chrome browser"""

        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()

        # persistent browser
        options.add_experimental_option("detach", True)

        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-pdf-viewer')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--blink-settings=imagesEnabled=false')

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(3000, 1500)
        self.driver.get(URL)

        self.wait = WebDriverWait(self.driver, 10)

        self.unavialable_courses = []

    def click_schedule_gen(self):
        try:
            schedule_gen_xpath = "/html/body/header/nav/div/div[2]/ul/li[4]/a"
            schedule_gen = self.wait.until(
                EC.presence_of_element_located((By.XPATH, schedule_gen_xpath)))
            schedule_gen.click()
            print("Ready to generate schedule....")

        except Exception as e:
            print(str(e))

    def search_course(self, course_code: str):
        try:
            search_box_xpath = '//*[@id="3"]/div/div[2]/div/form/div[1]/div/div/span/span[1]/span/ul/li/input'

            self.search_box = self.driver.find_element(
                By.XPATH, search_box_xpath)
            self.search_box.click()
            self.search_box.send_keys(course_code)

        except Exception as e:
            print(str(e))

    def is_course_available(self, course_code) -> bool:
        try:
            self.search_course(course_code)
            course_list_xpath = '//*[@class="select2-results__options"]'

            course_lists = self.wait.until(
                EC.presence_of_element_located((By.XPATH, course_list_xpath)))
            courses = course_lists.find_elements(By.TAG_NAME, 'li')

            for course in courses:
                if course.text == "No results found":
                    return False
                else:
                    return True

        except (NoSuchElementException):
            print("No such Element")

        except (ConnectionError):
            print("Connection Timeout")

        except Exception as e:
            print(str(e))

    def get_batch(self, course_code: str):
        try:
            if self.is_course_available(course_code) is True:
                self.search_course(course_code)
                course_list_xpath = '//*[@class="select2-results__options"]'

                course_lists = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, course_list_xpath)))
                course_batch = course_lists.find_elements(By.TAG_NAME, 'li')

                self.batch_list = []

                for batch in course_batch:
                    if batch.text != "No results found":
                        self.batch_list.append(batch.text)

                print(f'Found : {self.batch_list}')

                self.search_box.clear()

                for i in self.batch_list:
                    self.search_course(i)
                    self.search_box.send_keys(Keys.RETURN)
            else:
                self.unavialable_courses.append(course_code)

        except (NoSuchElementException):
            print("No such Element")

        except (ConnectionError):
            print("Connection Timeout")

        except Exception as e:
            print(str(e))

    def click_generate(self):
        try:
            generate_button_xpath = '//*[@id="sendButton"]'
            generate_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, generate_button_xpath)))
            self.driver.execute_script(
                'arguments[0].click();', generate_button)

        except (NoSuchElementException):
            print('Element Not Found')

        except Exception as e:
            print(str(e))

    def single_exams_schedule(self):
        try:
            self.click_schedule_gen()
            self.course_code = input(
                "Please enter course code (eg ugrc110): ").upper().replace(" ", "")
            self.get_batch(self.course_code)
            self.click_generate()
            # self.find_id(10985154)
            self.find_id(10985154)
            self.take_screenshot(self.course_code)

        except (NoSuchElementException):
            print("Element not found")

        except Exception as e:
            print(str(e))

    def all_courses_schedule(self):
        try:
            self.click_schedule_gen()
            self.all_courses = input(
                "Please enter all your course: ").upper().replace(" ", "").split(',')

            print(f'You said {self.all_courses}')

            for course in self.all_courses:
                self.get_batch(course)

            self.click_generate()
            self.take_screenshot("Exams_Schedule")

            if len(self.unavialable_courses) > 0:
                print(
                    f'These are not available on UG Website Yet: {self.unavialable_courses}')

        except (TimeoutException):
            print("Connection Timeout")
        except Exception as e:
            print(str(e))

    def find_id(self, id: int):

        try:
            rows = self.wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")

                if len(cols) > 0:
                    e_course = cols[0]
                    e_date = cols[1]
                    e_time = cols[2]
                    e_venues = cols[3].find_elements(By.TAG_NAME, "li")

                    if len(e_venues) == 1:
                        exam_venue = e_venues[0].text.split("|")[0]
                        print(
                            f"""
                            Course Batch : {e_course.text}
                            Date : {e_date.text}
                            Time : {e_time.text}    
                            Venue : {exam_venue} 

                            """)
                    else:
                        for venue in e_venues:
                            id_range_text = venue.find_element(
                                By.TAG_NAME, "span").text
                            id_range = list(
                                map(int, re.findall(r'\d+', id_range_text)))

                            if id_range[0] <= id <= id_range[1]:
                                print(id_range)
                                exam_venue = venue.text.split("|")[0]
                                print(
                                    f"""
                                    Course Batch : {e_course.text}
                                    Date : {e_date.text}
                                    Time : {e_time.text}    
                                    Venue : {exam_venue} 

                                    """)

            return "ID NOT FOUND"

        except (NoSuchElementException):
            print("No such element")
        except Exception as e:
            print(str(e))

    def take_screenshot(self, name: str):

        try:
            # scoll to end fo page
            self.driver.find_element(
                By.XPATH, "/html/body").send_keys(Keys.END)
            time.sleep(1)

            # take screenshot
            exams_card_xpath = '//*[@id="allcontent"]'
            element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, exams_card_xpath)))

            screenshot_path = f"./{name}"+".png"
            element.screenshot(f"./{name}"+".png")

            image_url = upload_to_firebase_storage(screenshot_path, name)
            print('Schedule saved')

            return image_url

        except (TimeoutException):
            print("TimeOut!!")
        except Exception as e:
            print(str(e))

    def cleanup(self):
        self.driver.quit()


if __name__ == '__main__':
    scraper = Scraper()
    # scraper.single_exams_schedule()
    scraper.all_courses_schedule()
    scraper.cleanup()
