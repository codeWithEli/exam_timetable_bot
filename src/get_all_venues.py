from bs4 import BeautifulSoup
import re
import logging
import aiohttp
import asyncio
from firebase_helper_functions import FirebaseHelperFunctions


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

found_course_links = []


def find_course_links(soup_card_details) -> list:
    try:
        for card in soup_card_details:
            links = card.select("div.header a[href]")
            for link in links:
                found_course_links.append(link["href"])

        return found_course_links

    except Exception as e:
        logger.error(f"FIND_COURSE_LINKS_ERROR: {str(e)}")
        return None


async def get_course_links(daily_exams_link) -> list | None:
    try:
        page_links = set()
        async with aiohttp.ClientSession() as session:
            async with session.get(daily_exams_link) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "lxml")

                first_exams_card = soup.select(
                    "body > div.container.resize > div:nth-child(2) > div"
                )
                find_course_links(first_exams_card)

                pagination = soup.select(
                    "body > div.container.resize > div:nth-child(3) > div > div > ul a[href]"
                )
                for page in pagination:
                    page_links.add(page["href"])

                for link in page_links:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link) as response:
                            html = await response.text()
                            soup = BeautifulSoup(html, "lxml")
                            remaining_exams_card = soup.select(
                                "body > div.container.resize > div:nth-child(2) > div"
                            )
                            find_course_links(remaining_exams_card)
                    return found_course_links

    except Exception as e:
        logger.error(f"SINGLE_EXAMS_SCHEDULE_ERROR: {str(e)}")
        return None


async def get_all_exams_venues(link: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                text = await response.text()
                soup = BeautifulSoup(text, "lxml")
                table = soup.find("table", class_="table table-striped")

                if table:
                    venues = (
                        table.find("td", string="Venue(s) / Index Range")
                        .find_next_sibling("td")
                        .find_all("li")
                    )

                    for venue in venues:
                        venue_text = venue.text.strip().split("|")
                        venue_name = venue_text[0]

                        with open("venue.txt", "a") as file:
                            file.write(venue_name + "\n")

    except Exception as e:
        logger.error(f"ERROR GETTING SINGLE_EXAMS_DETAIL: {str(e)}")
        return


def remove_duplicates(file_path):
    try:
        lines = set()
        with open(file_path, "r") as file:
            for line in file:
                lines.add(line.strip())

        with open("clean_venues.txt", "a") as file:
            for line in lines:
                file.write(line + "\n")

    except Exception as e:
        logger.error(f"ERROR REMOVING DUPLICATES: {str(e)}")


async def main():
    try:
        exams_links = []
        for i in range(1, 10):
            exams_links.append(
                f"https://sts.ug.edu.gh/timetable/thedate/2024-08-0{int(i)}"
            )

        for i in range(10, 16):
            exams_links.append(
                f"https://sts.ug.edu.gh/timetable/thedate/2024-08-{int(i)}"
            )

        for link in exams_links:
            await get_course_links(daily_exams_link=link)

        logger.info(f"total course found ========== {len(found_course_links)}")

        for link in found_course_links:
            await get_all_exams_venues(link=link)
        return

    except Exception as e:
        logger.error(f"Error proccesing exams details: {str(e)}")
        return


if __name__ == "__main__":
    # exams_links = ['https://sts.ug.edu.gh/timetable/details/DCIT102-Batch -1/2024-08-13', 'https://sts.ug.edu.gh/timetable/details/DCIT102-Batch -2/2024-08-13']
    # user_id = "123456789"
    # ID =  22048836

    # # UID = "271330483"
    # UID = "123456789"
    # asyncio.run(main())

    remove_duplicates("venue.txt")
