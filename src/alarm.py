import random
import logging
import firebase_functions as FB
from ics import Calendar, Event, DisplayAlarm
from datetime import datetime, timedelta


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def create_alarm_file(user_id: str, alarm_offset_minutes: int) -> str:

    try:
        all_exams_details = FB.get_saved_exams_details(user_id)
        
        cal = Calendar()

        for course_name, course_info in all_exams_details.items():all_exams_details = FB.get_saved_exams_details(user_id)
        
        cal = Calendar()

        for course_name, course_info in all_exams_details.items():
            # Create event
            event = Event()
            event.name = course_info["Full_Course_Name"]
            event.description = f"ALL EXAMS VENUES: {course_info['All_Exams_Venue']}"
            event.begin = datetime.strptime(
                f"{course_info['Exams_Date']} {course_info['Exams_Time']}", "%B %d, %Y %I:%M %p")

            # Construct display text and venue
            display_text = f"{course_info['Full_Course_Name']}"
            Venue = ""
            if course_info["Exact_Exams_Venue"] is not None:
                Venue = f"{course_info['Exact_Exams_Venue']}"
            else:
                Venue = f"{', '.join(course_info['All_Exams_Venue'])}"

            event.location = Venue

            # Add alarm
            alarm = DisplayAlarm()
            alarm.trigger = timedelta(minutes=-alarm_offset_minutes)
            alarm.description = f"{display_text} \nVenue: {Venue}"
            event.alarms.append(alarm)

            # Add event to calendar
            cal.events.add(event)

        # Create a single ICS file with all events
        ran_num = random.randint(0, 1000)
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{ran_num}-Exam_Reminder-{user_id}-{now}.ics"
        filename_path = f"./{filename}"

        with open(filename_path, "w") as f:
            f.writelines(cal.serialize())
            # f.writelines(alarm.serialize())

        calendar_url = FB.upload_calendar_to_firebase(filename_path, filename)

        logger.info(f"All exam alarm information saved to: {filename}")

        return calendar_url

    except Exception as e:
        logger.info(
            f"An error occurred while creating ALARM file for {course_name}: {e}")
        return None


if __name__ == "__main__":
    create_alarm_file("123456789", 60)
