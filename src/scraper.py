
import os
import time
import re
import logging
import dotenv

from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from selenium.common.exceptions import NoSuchElementException, TimeoutException

import firebase_functions as FB

# constants
dotenv.load_dotenv()
URL = os.getenv("UG_URL")

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
        self.driver.get(URL)  # "https://sts.ug.edu.gh/timetable/"

        self.wait = WebDriverWait(self.driver, 10)

        self.click_schedule_gen()

    def click_schedule_gen(self) -> None:
        try:
            schedule_gen_xpath = "/html/body/header/nav/div/div[2]/ul/li[4]/a"
            schedule_gen = self.wait.until(
                EC.presence_of_element_located((By.XPATH, schedule_gen_xpath)))
            schedule_gen.click()
            logger.info("Ready to generate schedule....🌍")

        except Exception as e:
            logger.info(str(e))

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

    def search_course(self, course_code: str) -> None:
        try:
            search_box_xpath = '//*[@id="3"]/div/div[2]/div/form/div[1]/div/div/span/span[1]/span/ul/li/input'

            self.search_box = self.driver.find_element(
                By.XPATH, search_box_xpath)
            self.search_box.click()
            self.search_box.send_keys(course_code)

        except Exception as e:
            logger.error(str(e))

    def get_batch(self, course_code: str) -> list:
        try:

            self.search_course(course_code)
            course_list_xpath = '//*[@class="select2-results__options"]'

            course_lists = self.wait.until(
                EC.presence_of_element_located((By.XPATH, course_list_xpath)))
            course_batch = course_lists.find_elements(By.TAG_NAME, 'li')

            batch_list = []
            for batch in course_batch:
                if batch.text != "No results found":
                    batch_list.append(batch.text)

            logger.info(f'Found batch list: {batch_list}✅')

            self.search_box.clear()

            if len(batch_list) > 0:
                logger.info(f"Searching for {batch_list} 🔎")
                for course_found in batch_list:
                    self.search_course(course_found)
                    self.search_box.send_keys(Keys.RETURN)

            return batch_list

        except (NoSuchElementException):
            logger.error("get_batch element not found")

        except (ConnectionError):
            logger.error(
                "get_batch connection error..check internet connection")

        except Exception as e:
            logger.error(f'GET_BATCH ERROR: {str(e)}')

    def click_generate(self) -> None:
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

    def exact_exam_venue(self, user_id, course, e_venues, ID: None | int):
        try:
            no_id_venues = []
            exam_venue = ""

            for venue in e_venues:
                id_range_text = venue.find_element(
                    By.TAG_NAME, "span").text

                id_range = list(
                    map(int, re.findall(r'\d+', id_range_text)))

                # Clear previous highlighs
                self.driver.execute_script(
                    "arguments[0].setAttribute('style', '');", venue)

                if id_range_text != "" and ID is not None:
                    if id_range[0] <= int(ID) <= id_range[1]:
                        logger.info(f'Found ID - {ID} in range - {id_range} ✅')
                        exam_venue = venue.text.split("|")[0]
                        self.driver.execute_script(
                            "arguments[0].setAttribute('style', 'background: yellow; border: 2px solid red;');", venue)

                        logger.info(
                            f'Found exact exams venue {exam_venue} 📍')
                        return exam_venue
                    else:
                        logger.info(f"ID {ID} not in range {id_range}")

                elif id_range_text == "" and ID is not None:
                    no_id_venue = venue.text.split("|")[0]
                    no_id_venues.append(no_id_venue)
                    FB.set_no_id_venues(user_id, course, no_id_venues)
                    logger.info(
                        f"Found venue without ID attached -- {no_id_venues} 🗺")

                else:
                    return None

        except Exception as e:
            logger.error(f'Getting exact exams venue error - {str(e)}')
            return None

    def exams_detail(self, user_id: str, course_code: str, ID=None) -> None:
        try:

            rows = self.wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))

            for row in rows[1:]:
                cols = row.find_elements(By.TAG_NAME, "td")

                if len(cols) > 0:
                    e_course = cols[0].text
                    e_date = cols[1].text
                    e_time = cols[2].text
                    e_venues = cols[3].find_elements(By.TAG_NAME, "li")

                    all_venues = []

                    for venue in e_venues:
                        # Get all venues
                        all_venues.append(venue.text)

                    FB.save_exams_details(user_id, e_course,
                                          e_date, e_time, all_venues)
                    FB.set_course_code(user_id, e_course, course_code)
                    logger.info(f"Saved exams details to firebase 🔥")

                    if ID != None:
                        exact_venue = self.exact_exam_venue(user_id, e_course,
                                                            e_venues, ID)
                        FB.set_exact_venue(user_id, e_course, exact_venue)
                        logger.info(
                            f"Exact venue and no id venues saved to firebase 🔥")
                    else:
                        logger.info("ID not given, cant find venue")

            return

        except (NoSuchElementException):
            logger.error("No such element")
            return None
        except Exception as e:
            logger.error(str(e))
            return None

    def take_screenshot(self, user_id: str, name: str) -> str:
        try:
            # get date and time
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # scoll to end fo page
            self.driver.find_element(
                By.XPATH, "/html/body").send_keys(Keys.END)
            time.sleep(1)

            # take screenshot
            exams_card_xpath = '//*[@id="allcontent"]'
            element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, exams_card_xpath)))

            screenshot_path = f"./{name}-{user_id}-{now}.png"
            remote_name = f"{name}-{user_id}-{now}"

            element.screenshot(screenshot_path)

            image_url = FB.upload_screenshot_to_firebase(
                screenshot_path, remote_name)
            logger.info('Schedule saved to firebase 🔥')

            return image_url

        except (TimeoutException):
            logger.error("take_screenshot timeout")
            return None
        except Exception as e:
            logger.error(str(e))
            return None

    def single_exams_schedule(self, course_code, user_id: str):
        try:

            batch_list = self.get_batch(course_code)
            if len(batch_list) > 0:
                self.click_generate()
                self.exams_detail(user_id, course_code, ID=None)
                return self.take_screenshot(user_id, course_code)
            else:
                logger.info(f"{course_code} Not found !! 👾")
                return None

        except (NoSuchElementException):
            logger.error("Single exams schedule element not found")
            return None

        except Exception as e:
            logger.error(f'SINGLE_EXAMS_SCHEDULE_ERROR: {str(e)}')
            return None

    def all_courses_schedule(self, all_courses, user_id, ID=None):
        try:
            unavailable_courses = []
            available_courses = []
            cleaned_courses = all_courses.upper().replace(" ", "").split(',')

            logger.info(f'User requested for {cleaned_courses} 🔎')

            for course in cleaned_courses:
                if self.is_course_available(course):
                    available_courses.append(course)
                else:
                    unavailable_courses.append(course)

            logger.info(
                f'Available course on UG timetable website : {available_courses} ✅')
            for found_course in available_courses:
                self.get_batch(found_course)

            self.click_generate()

            self.exams_detail(user_id, found_course, ID)
            logger.info(
                f'Not available on UG timetable website Yet: {unavailable_courses} 👾')

            return self.take_screenshot(user_id, "Exams_Schedule"), unavailable_courses

        except (NoSuchElementException):
            logger.error("all_course_schedule element NOT FOUND")
            return None, None
        except (TimeoutException):
            logger.error("Connection Timeout")
            return None, None
        except Exception as e:
            logger.error(str(e))
            return None, None

    def close(self):
        self.driver.quit()


if __name__ == '__main__':
    scraper = Scraper()
    user_id = "123456789"
    ID = 10963881
    # scraper.single_exams_schedule("dcit303", user_id)
    # scraper.find_exact_exams_venue("ugbs303", user_id, ID)
    # scraper.find_exact_exams_venue("ugrc210", user_id, ID)
    scraper.all_courses_schedule("ugbs303, dcit303, ugrc210", user_id, ID)
    scraper.cleanup()
