from bs4 import BeautifulSoup
from bisect import bisect_left
import re
from dataclasses import dataclass
import logging
import aiohttp
import asyncio
from firebase_functions import (
    save_exams_details, delete_exams_details, set_exact_venue_bool)
import time
# from memory_profiler import LineProfiler, profile

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


@dataclass
class FindExamsVenue():
    """
    Get the all exams details of a single course.

    This funtion takes the links of all exams 
    schedule returned from the results of a seach
    in the "seach schedule tab" in sts.timetable 
    website and saves the exams details to firebase
    """

    user_id: str
    std_id: int
    links: list

    # Delete previous data from firebase

    def binary_search(self, venues):

        index = bisect_left(venues, self.std_id)
        if index != len(venues) and venues[index] == self.std_id:
            return True
        else:
            return False

    async def process_links(self):
        for link in self.links:
            yield link


    async def fetch_and_process(self, session, link: str, retries: int = 2):
        for i in range(retries):
            try:

                async with session.get(link) as response:

                    no_id_venue: list = []
                    # found_exact_venue: bool = False

                    text = await response.text()
                    soup = BeautifulSoup(text, 'lxml')
                    course_name = soup.select(
                        'div.header span.text-primary')[0].text
                    table = soup.find('table', class_='table table-striped')

                    if table:
                        course_level = table.find(
                            'td', string='Course Level').find_next_sibling('td').text

                        exams_status = table.find(
                            'td', string='Exams Status').find_next_sibling('td').text

                        exam_date = table.find(
                            'td', string='Exam Date').find_next_sibling('td').text

                        exam_time = table.find(
                            'td', string='Exams Time').find_next_sibling('td').text

                        campus = table.find(
                            'td', string='Campus').find_next_sibling('td').text

                        venues = table.find(
                            'td', string='Venue(s) / Index Range').find_next_sibling('td').find_all('li')

                        for venue in venues:
                            venue_text = venue.text.strip().split("|")
                            id_range = venue_text[1]
                            venue_name = venue_text[0]
                            all_venues = [venue.text.strip(
                                "[]").replace("[", "") for venue in venues]

                            if id_range == "":
                                no_id_venue.append(venue_name)

                            venue_id_range = re.findall(r"\d+", id_range)

                            if len(venue_id_range) == 2 and self.binary_search(list(range(int(venue_id_range[0]), int(venue_id_range[1]) + 1))):

                                course_details = {'Full_Course_Name': course_name, 'Course_Level': course_level, 'Campus': campus,
                                                  'Exams_Status': exams_status, 'Exams_Date': exam_date, 'Exams_Time': exam_time,
                                                  'Exact_Venue': f"{venue_name} | {id_range}", 'No_ID_Venue': no_id_venue, 'Link': link, }
                                save_exams_details(
                                    self.user_id, course_name, course_details)
                                set_exact_venue_bool(self.user_id, status=True)

                            else:
                                course_details = {'Full_Course_Name': course_name, 'Course_Level': course_level, 'Campus': campus,
                                                  'Exams_Status': exams_status, 'Exams_Date': exam_date, 'Exams_Time': exam_time,
                                                  'Exact_Venue': None, 'All_Exams_Venues': all_venues,  'Link': link, }
                                save_exams_details(
                                    self.user_id, course_name, course_details)
                                set_exact_venue_bool(
                                    self.user_id, status=False)

                            if soup.decomposed is False:
                                soup.decompose()
            except (aiohttp.ServerDisconnectedError, aiohttp.ClientConnectionError, aiohttp.ClientConnectorCertificateError):
                if i < retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    raise
            break

    async def main(self):
        async with aiohttp.ClientSession() as session:
            async for link in self.process_links():
                await self.fetch_and_process(session, link)


if __name__ == "__main__":
    exams_links = ['https://sts.ug.edu.gh/timetable/details/UGRC150/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 1/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 2/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 3/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 4/2024-04-03',
                   'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 5/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 6/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 7/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 1/2024-04-04', 'https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 2/2024-04-04']

    user_id = "123456789"
    ID = 10953871
    venue_finder = FindExamsVenue(user_id, std_id=ID, links=exams_links)

    asyncio.run(venue_finder.main())
