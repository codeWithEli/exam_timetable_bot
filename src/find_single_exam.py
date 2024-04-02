from bs4 import BeautifulSoup
import requests
from bisect import bisect_left
import re
import logging


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)




def get_single_exam_details(id: int, links: list) -> dict | None:

    try:
        no_id_venue = []
        exact_venues_details = []

        def binary_search(venues, id):
            index = bisect_left(venues, id)
            if index != len(venues) and venues[index] == id:
                return True
            else:
                return False

        for link in links:
            response = requests.get(link)
            soup = BeautifulSoup(response.text, 'lxml')
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

                    if id_range == "":
                        no_id_venue.append(venue_name)

                    venue_id_range = re.findall(r"\d+", id_range)

                    if len(venue_id_range) == 2 and binary_search(list(range(int(venue_id_range[0]), int(venue_id_range[1]) + 1)), id):

                        exact_venues_details.append({'course_name': course_name, 'course_level': course_level, 'campus': campus, 'exams_status': exams_status,
                                                    'exam_date': exam_date, 'exam_time': exam_time, 'venue': venue_name, 'no id venue': no_id_venue, 'link': link, })
        logger.info(exact_venues_details)
        return exact_venues_details

    except Exception as e:
        logger.error(f'ERROR GETTING SINGLE_EXAMS_DETAIL: {str(e)}')
        return None


if __name__ == "__main__":
    exams_links = ['https://sts.ug.edu.gh/timetable/details/UGRC150/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 1/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 2/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 3/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 4/2024-04-03',
               'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 5/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 6/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-Main Campus-Batch 7/2024-04-03', 'https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 1/2024-04-04', 'https://sts.ug.edu.gh/timetable/details/UGRC150-CHS-Batch - 2/2024-04-04']

    ID = 10953871
    get_single_exam_details(ID, exams_links)
