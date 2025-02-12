import random
from ics import Calendar, Event, DisplayAlarm
from datetime import datetime, timedelta
from firebase_functions import get_saved_exams_details
from utils import logger


def create_alarm_file(user_id: str, alarm_offset_minutes: int) -> str:
    all_exams_details = get_saved_exams_details(user_id)

    cal = Calendar()

    try:
        for course_name, course_info in all_exams_details.items():
            # Create event
            event = Event()
            event.name = course_info["Full_Course_Name"]
            event.description = f"ALL EXAMS VENUES: {course_info['All_Exams_Venue']}"
            event.begin = datetime.strptime(
                f"{course_info['Exams_Date']} {course_info['Exams_Time']}",
                "%B %d, %Y %I:%M %p",
            )

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
        filename = f"{ran_num}-Exam_Reminder-{user_id}.ics"
        with open(filename, "w") as f:
            f.writelines(cal.serialize())
            # f.writelines(alarm.serialize())

        logger.info(f"All exam alarm information saved to: {filename}")
        return filename

    except Exception as e:
        logger.info(f"An error occurred while processing {course_name}: {e}")
        return None


if __name__ == "__main__":
    create_alarm_file("123456789", 60)
