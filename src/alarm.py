import logging
import firebase_functions as FB
from ics import Calendar, Event, DisplayAlarm
from datetime import datetime, timedelta
import warnings


warnings.simplefilter("ignore", FutureWarning)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def create_alarm_file(user_id: str, alarm_offset_minutes: int) -> str:

    try:
        all_exams_details = FB.get_saved_exams_details(user_id)

        cal = Calendar()

        for course_name, course_info in all_exams_details.items():
            # Create event
            event = Event()
            event.name = course_info.get("Full_Course_Name")
            event.description = f"ALL EXAMS VENUES: {course_info.get('All_Exams_Venue')}"
            event.begin = datetime.strptime(
                f"{course_info.get('Exams_Date')} {course_info.get('Exams_Time')}", "%B %d, %Y %I:%M %p")

            # Construct display text and venue

            display_text = f"{course_info['Full_Course_Name']}"
            Venue = ""
            if course_info.get("Exact_Exams_Venue"):
                Venue = f"{course_info.get('Exact_Exams_Venue')}"
            else:
                Venue = f"{', '.join(course_info.get('All_Exams_Venue'))}"

            event.location = Venue

            # Add alarm
            alarm = DisplayAlarm()
            alarm.trigger = timedelta(minutes=-alarm_offset_minutes)
            alarm.description = f"{display_text} \nVenue: {Venue}"
            event.alarms.append(alarm)

            # Add event to calendar
            cal.events.add(event)

        # Create a single ICS file with all events
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Exam_Reminder-{user_id}-{now}.ics"
        filename_path = f"./{filename}"

        with open(filename_path, "w") as f:
            f.writelines(cal.serialize())

        calendar_url = FB.upload_calendar_to_firebase(filename_path, filename)

        logger.info(f"Exam alarm information saved to: {filename}")

        return calendar_url

    except Exception as e:
        logger.info(
            f"An error occurred while creating ALARM file for {course_name}: {e}")
        return None


if __name__ == "__main__":
    create_alarm_file("123456789", 60)
