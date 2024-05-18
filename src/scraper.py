import os
import logging
import dotenv

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

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
        self.driver.get(URL)
        self.wait = WebDriverWait(self.driver, 10)

    def course_search_in_search_schedule(self, course_code: str) -> None:
        try:
            search_box_xpath = '//*[@id="2"]/div/div[2]/form/div[1]/div[1]/input'

            self.search_box = self.driver.find_element(
                By.XPATH, search_box_xpath)
            self.search_box.click()
            self.search_box.send_keys(course_code)

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

            # logger.info(f"Exams links--{exams_links}")
            return exams_links

        except (NoSuchElementException):
            logger.error("Single Exams Schedule element not found")
            return None
        except Exception as e:
            logger.error(f'SINGLE_EXAMS_SCHEDULE_ERROR: {str(e)}')
            return None

    def close(self):
        self.driver.quit()


if __name__ == '__main__':
    scraper = Scraper()
    user_id = "123456789"
    scraper.single_exams_schedule("ugbs303")
    scraper.close()
