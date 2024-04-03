from bs4 import BeautifulSoup
from bisect import bisect_left
import re
import logging
import aiohttp
import asyncio
import firebase_functions as FB

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def get_single_exam_details(user_id: str, id: int, links: list) -> bool | None:
    """
    Get the all exams details of a single course.

    This funtion takes the links of all exams 
    schedule returned from the results of a seach
    in the "seach schedule tab" in sts.timetable 
    website and saves the exams details to firebase
    """
    try:
        no_id_venue = []
        exact_venues_details = {}
        venue_not_found = {}

        found_exact_venue = False

        def binary_search(venues, id):
            index = bisect_left(venues, id)
            if index != len(venues) and venues[index] == id:
                return True
            else:
                return False

        async with aiohttp.ClientSession() as session:
            for link in links:
                async with session.get(link) as response:
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
                            all_venues = [venue.text for venue in venues]

                            if id_range == "":
                                no_id_venue.append(venue_name)

                            venue_id_range = re.findall(r"\d+", id_range)

                            if len(venue_id_range) == 2 and binary_search(list(range(int(venue_id_range[0]), int(venue_id_range[1]) + 1)), id):

                                exact_venues_details[course_name] = {'Full_Course_Name': course_name, 'Course_Level': course_level, 'Campus': campus,
                                                                     'Exams_Status': exams_status, 'Exams_Date': exam_date, 'Exams_Time': exam_time,
                                                                     'Exact_Venue': venue_name, 'All_Exams_Venues': all_venues, 'No_ID_Venue': no_id_venue, 'Link': link, }
                            else:
                                venue_not_found[course_name] = {'Full_Course_Name': course_name, 'Course_Level': course_level, 'Campus': campus,
                                                                'Exams_Status': exams_status, 'Exams_Date': exam_date, 'Exams_Time': exam_time,
                                                                'Exact_Venue': None, 'All_Exams_Venues': all_venues, 'No_ID_Venue': no_id_venue, 'Link': link, }

            if exact_venues_details:
                for course, course_details in exact_venues_details.items():
                    FB.save_exams_details(user_id, course, course_details)
                found_exact_venue = True
                logger.info(
                    f"Exact venue found ✅...saved details to firebase for user id {user_id} 🔥")
            else:
                for course_, course_details_ in venue_not_found.items():
                    FB.save_exams_details(user_id, course_, course_details_)
                logger.info(
                    f"Exact venue NOT found ❌...saved details to firebase for user id {user_id} 🔥")

            return found_exact_venue

    except Exception as e:
        logger.error(f'ERROR GETTING SINGLE_EXAMS_DETAIL: {str(e)}')
        return None


if __name__ == "__main__":
    exams_links = ['https://sts.ug.edu.gh/timetable/details/UGRC150/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 1/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 2/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 3/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 4/2024-04-03',
                   'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 5/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 6/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 7/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 1/2024-04-04', 'https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 2/2024-04-04']

    user_id = "123456789"
    ID = 10953871
    asyncio.run(get_single_exam_details(user_id, ID, exams_links))
