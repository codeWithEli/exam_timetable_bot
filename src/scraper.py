
import os
import time
import re
import logging
import dotenv

from datetime import datetime
from bs4 import BeautifulSoup

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

    def click_schedule_gen(self) -> None:
        try:
            schedule_gen_xpath = "/html/body/header/nav/div/div[2]/ul/li[4]/a"
            schedule_gen = self.wait.until(
                EC.presence_of_element_located((By.XPATH, schedule_gen_xpath)))
            schedule_gen.click()
            logger.info("Ready to generate schedule....🌍")

        except Exception as e:
            logger.info(str(e))

    def course_search_in_schedule_gen(self, course_code: str) -> None:
        try:
            search_box_xpath = '//*[@id="3"]/div/div[2]/div/form/div[1]/div/div/span/span[1]/span/ul/li/input'

            self.search_box = self.driver.find_element(
                By.XPATH, search_box_xpath)
            self.search_box.click()
            self.search_box.send_keys(course_code)

        except Exception as e:
            logger.error(str(e))

    def is_course_available(self, course_code) -> bool:
        try:

            self.course_search_in_schedule_gen(course_code)
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

    def course_search_in_search_schedule(self, course_code: str) -> None:
        try:
            search_box_xpath = '//*[@id="2"]/div/div[2]/form/div[1]/div[1]/input'

            self.search_box = self.driver.find_element(
                By.XPATH, search_box_xpath)
            self.search_box.click()
            self.search_box.send_keys(course_code)

        except Exception as e:
            logger.error(str(e))

    def get_batch(self, course_code: str) -> list:
        try:

            self.course_search_in_schedule_gen(course_code)
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

            if len(self.batch_list) > 0:
                logger.info(f"Searching for {self.batch_list} 🔎")
                for course_found in self.batch_list:
                    self.course_search_in_schedule_gen(course_found)
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

    def click_find_exams_schedules(self) -> None:
        try:
            generate_button_xpath = '//*[@id="2"]/div/div[2]/form/button[1]'
            generate_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, generate_button_xpath)))
            self.driver.execute_script(
                'arguments[0].click();', generate_button)

        except (NoSuchElementException):
            logger.error('click_generater element Not Found')

        except Exception as e:
            logger.error(str(e))

    def click_search_schedules(self) -> None:
        try:
            button_xpath = '/html/body/header/nav/div/div[2]/ul/li[3]/a'
            button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
            self.driver.execute_script(
                'arguments[0].click();', button)

        except (NoSuchElementException):
            logger.error('click_generater element Not Found')

        except Exception as e:
            logger.error(str(e))

    def exact_exam_venue(self, user_id, course, e_venues, ID: int):
        try:
            no_id_venues = []
            exam_venue = None
            venue_list = []

            for venue in e_venues:
                # Clear previous highlighs
                # self.driver.execute_script(
                #     "arguments[0].setAttribute('style', '');", venue)
                venue_object = venue
                name = venue.text
                id_range_text = venue.find_element(
                    By.TAG_NAME, "span").text
                id_range = list(
                    map(int, re.findall(r'\d+', id_range_text)))
                if id_range:
                    venue_list.append(
                        (venue_object, name, id_range[0], id_range[1]))
                else:
                    no_id_venues.append(name)

            low = 0
            high = len(venue_list) - 1

            while low <= high:
                mid = (low + high)//2

                if venue_list[mid][2] <= ID <= venue_list[mid][3]:
                    logger.info(f'Found ID - {ID} in range - {id_range} ✅')
                    exam_venue = venue_list[mid][1]
                    self.driver.execute_script(
                        "arguments[0].setAttribute('style', 'background: yellow; border: 2px solid red;');", venue_list[mid][0])
                    logger.info(
                        f'Found exact exams venue {exam_venue} 📍')
                    return exam_venue, no_id_venues
                elif venue_list[mid][3] > ID:
                    high = mid - 1
                else:
                    low = mid + 1

            return exam_venue, no_id_venues

        except Exception as e:
            logger.error(f'Getting exact exams venue error - {str(e)}')
            return None

    def exams_detail(self, user_id: str, course_code: str, ID=None) -> None:
        try:

            rows = self.wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))

            exams_info = {}
            no_id_venues = None
            exact_venue = None

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

                    if ID != None:
                        exact_venue, no_id_venues = self.exact_exam_venue(
                            user_id, e_course, e_venues, ID)

                        

                    exams_info[e_course] = {'Full_Course_Name': e_course,
                                            'Exams_Date': e_date,
                                            'Exams_Time': e_time,
                                            'Exact_Venue': exact_venue,
                                            'All_Exams_Venue': all_venues,
                                            'No_ID_venues': no_id_venues,
                                            'Course_Code': course_code
                                            }
                    logger.info(
                            f"Exact venue and no id venues saved to firebase 🔥")
                    else:
                        logger.info("ID not given, cant find venue")

            for course_name, course_info in exams_info.items():
                FB.save_exams_details(user_id, course_name, course_info)

            logger.info(f"Saved exams details to firebase 🔥")
            return

        except (NoSuchElementException):
            logger.error("No such element")
            return None
        except Exception as e:
            logger.error(str(e))
            return None

    def take_screenshot(self, user_id: str, name: str) -> str | None:
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

    def single_exams_schedule(self, course_code: str) -> list | None:
        try:
            self.click_search_schedules()
            self.course_search_in_search_schedule(course_code)
            self.click_find_exams_schedules()

            html = self.driver.page_source
            soup = BeautifulSoup(html, "lxml")
            exams_links = []

            for a in soup.select('div.header a[href]'):
                exams_links.append(a['href'])

            logger.info(f"Got links for {exams_links}")
            return exams_links

        except (NoSuchElementException):
            logger.error("Single Exams Schedule element not found")
            return None
        except Exception as e:
            logger.error(f'SINGLE_EXAMS_SCHEDULE_ERROR: {str(e)}')
            return None

    def all_courses_schedule(self, all_courses, user_id, ID=None):
        try:
            self.click_schedule_gen()
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
    scraper.single_exams_schedule("ugbs303")
    # scraper.all_courses_schedule("ugbs303, dcit303, ugrc210", user_id, ID)

    scraper.close()
