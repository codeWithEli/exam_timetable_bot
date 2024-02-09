
import os
import time
import re
import logging
import dotenv

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

# configuring logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


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

        self.unavailable_courses = []
        self.available_courses = []

    def click_schedule_gen(self):
        try:
            schedule_gen_xpath = "/html/body/header/nav/div/div[2]/ul/li[4]/a"
            schedule_gen = self.wait.until(
                EC.presence_of_element_located((By.XPATH, schedule_gen_xpath)))
            schedule_gen.click()
            logger.info("Ready to generate schedule....")

        except Exception as e:
            logger.info(str(e))

    def search_course(self, course_code: str):
        try:
            search_box_xpath = '//*[@id="3"]/div/div[2]/div/form/div[1]/div/div/span/span[1]/span/ul/li/input'

            self.search_box = self.driver.find_element(
                By.XPATH, search_box_xpath)
            self.search_box.click()
            self.search_box.send_keys(course_code)

        except Exception as e:
            logger.error(str(e))

    def validate_course_code(self, course_code):

        pattern = r'^[A-Za-z]{4}\d{3}$'

        if not re.match(pattern, course_code):
            raise ValueError(
                f"Invalid course code: {course_code}. Expected format is 4 alphabets followed by 3 numbers")

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
            logger.error("Is_ourse_available Element Not Found")

        except (ConnectionError):
            logger.error("Connection error check internet connection")

        except Exception as e:
            logger.error(str(e))

    def get_batch(self, course_code: str):
        try:

            self.search_course(course_code)
            course_list_xpath = '//*[@class="select2-results__options"]'

            course_lists = self.wait.until(
                EC.presence_of_element_located((By.XPATH, course_list_xpath)))
            course_batch = course_lists.find_elements(By.TAG_NAME, 'li')

            self.batch_list = []

            for batch in course_batch:
                self.batch_list.append(batch.text)

            logger.info(f'Found : {self.batch_list}')

            self.search_box.clear()

            for course_found in self.batch_list:
                self.search_course(course_found)
                self.search_box.send_keys(Keys.RETURN)

        except (NoSuchElementException):
            logger.error("get_batch element not found")

        except (ConnectionError):
            logger.error("get_batch connection..check internet connection")

        except Exception as e:
            logger.error(str(e))

    def click_generate(self):
        try:
            generate_button_xpath = '//*[@id="sendButton"]'
            generate_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, generate_button_xpath)))
            self.driver.execute_script(
                'arguments[0].click();', generate_button)

        except (NoSuchElementException):
            logger.error('click_generater element Not Found')

        except Exception as e:
            logger.error(str(e))

    def single_exams_schedule(self):
        try:

            self.click_schedule_gen()
            self.course_code = input(
                "Please enter course code (eg ugrc110): ").upper().replace(" ", "")
            self.get_batch(self.course_code)
            self.click_generate()
            self.take_screenshot(self.course_code)

        except (NoSuchElementException):
            logger.error("single exams schedulelement not found")

        except Exception as e:
            logger.error(str(e))

    def find_exact_exams_venue(self, ID: int):

        try:
            self.click_schedule_gen()
            self.course_code = input(
                "Please enter course code (eg ugrc110): ").upper().replace(" ", "")
            self.get_batch(self.course_code)
            self.click_generate()
            self.find_id(ID)
            self.take_screenshot(self.course_code)

        except (NoSuchElementException):
            logger.error("exact_exams_venue element not found")

        except Exception as e:
            logger.error(str(e))

    def all_courses_schedule(self):
        try:
            all_courses = input(
                "Please enter all your course: ").upper().replace(" ", "").split(',')
            for course in all_courses:
                self.validate_course_code(course)
            try:

                self.click_schedule_gen()

                logger.info(f'User requested for {all_courses}')

                for course in all_courses:
                    if self.is_course_available(course):
                        self.available_courses.append(course)
                    else:
                        self.unavailable_courses.append(course)

                logger.info(
                    f'Available course on UG timetable website : {self.available_courses}')
                for found_courses in self.available_courses:
                    self.get_batch(found_courses)

                self.click_generate()
                self.take_screenshot("Exams_Schedule")

                logger.info(
                    f'Not available on UG timetable website Yet: {self.unavailable_courses}')

            except (NoSuchElementException):
                logger.error("all_course_schedule element NOT FOUND")
            except (TimeoutException):
                logger.error("Connection Timeout")
            except Exception as e:
                logger.error(str(e))
        except ValueError as e:
            logger.error(str(e))

    def find_id(self, ID: int):

        try:
            no_id_venues = []
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
                        logger.info(
                            f"""
                                    Course Batch : {e_course.text}
                                    Date : {e_date.text}
                                    Time : {e_time.text}    
                                    Venue : {exam_venue} 

                                    """)

                        return {e_course.text}, {e_date.text}, {e_time.text}, {exam_venue}

                    else:
                        for venue in e_venues:
                            id_range_text = venue.find_element(
                                By.TAG_NAME, "span").text
                            id_range = list(
                                map(int, re.findall(r'\d+', id_range_text)))

                            if id_range_text == "":
                                no_id_venues.append(
                                    e_venues[0].text.split("|")[0])
                            elif id_range_text != "":
                                if id_range[0] <= ID <= id_range[1]:
                                    logger.info(id_range)
                                    exam_venue = venue.text.split("|")[0]
                                    logger.info(
                                        f"""
                                        Course Batch : {e_course.text}
                                        Date : {e_date.text}
                                        Time : {e_time.text}    
                                        Venue : {exam_venue} 

                                        """)
                                    return {e_course.text}, {e_date.text}, {e_time.text}, {exam_venue}

            if len(no_id_venues) > 0:
                logger.info(
                    f"Exact venue NOT FOUND. Posible venue ==> {no_id_venues}")
                return "ID NOT FOUND", no_id_venues
            else:
                logger.info(
                    f"Exact venue NOT FOUND")
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
            logger.info('Schedule saved')
            return image_url

        except (TimeoutException):
            logger.error("take_screenshot timeout")
        except Exception as e:
            logger.error(str(e))

    def cleanup(self):
        self.driver.quit()


if __name__ == '__main__':
    scraper = Scraper()
    # scraper.single_exams_schedule()
    # scraper.find_exact_exams_venue(11358985)
    scraper.all_courses_schedule()
    scraper.cleanup()
