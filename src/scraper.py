import os
import logging
import dotenv

from bs4 import BeautifulSoup
import requests
import re

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.common.exceptions import NoSuchElementException

# constants
dotenv.load_dotenv()
URL = os.getenv("UG_TIMETABLE_URL")

# configuring logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


class Scraper:
    """Scraper class"""

    def __init__(self):
        self.found_links = []
       
    
    def find_course_links(self, soup_card_details, course_code: str) -> list:
            
            try:
                pattern = re.compile(rf'{course_code}', re.IGNORECASE)
                
                for card in soup_card_details:
                    links = card.select("div.header a[href]")
                    for link in links:
                        if pattern.search(link.text):
                            self.found_links.append(link['href'])
                
                return self.found_links
                
            except Exception as e:
                logger.error(f'FIND_COURSE_LINKS_ERROR: {str(e)}')
                return None


    def single_exams_schedule(self, course_code: str) -> list | None:
        try:
            
            
            page_links = set()
            html = requests.get(URL).content
            soup = BeautifulSoup(html, "lxml")
            
            first_exams_card = soup.select("body > div.container.resize > div:nth-child(2) > div")
            self.find_course_links(first_exams_card, course_code)
            

            pagination = soup.select("body > div.container.resize > div:nth-child(3) > div > div > ul a[href]")
            for page in pagination:
                page_links.add(page['href'])

            for link in page_links:
                html = requests.get(link).content
                soup = BeautifulSoup(html, "lxml")
                remaining_exams_card = soup.select("body > div.container.resize > div:nth-child(2) > div")
                self.find_course_links(remaining_exams_card, course_code)
            return self.found_links
        
        except Exception as e:
            logger.error(f'SINGLE_EXAMS_SCHEDULE_ERROR: {str(e)}')
            return None




if __name__ == '__main__':
    scraper = Scraper()
    user_id = "123456789"
    course_code = "DCIT102"
    # scraper.get_exams_page_links()
    scraper.single_exams_schedule(course_code)
    # scraper.close()
