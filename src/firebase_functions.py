""" firebase helper functions"""
import logging
import re

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# log config
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

try:
    # Read service account credentials securely using a context manager
    cred = credentials.Certificate("src/.credentials/serviceAccount.json")

    # Initialize Firebase app
    firebase_admin.initialize_app(cred)

    db = firestore.client()

except FileNotFoundError as e:
    logger.error(f"Error loading service account credentials: {e}")
    raise  # Re-raise the exception to signal failure

except Exception as e:
    logger.exception(f"Unexpected error initializing Firebase app: {e}")
    raise  # Re-raise the exception to report the issue


def get_course_code(user_id: str) -> str:

    try:
        doc_ref = db.collection('users').document(str(user_id))
        doc = doc_ref.get()

        if doc.exists:
            course_code = doc.get('user_entered_course_code')
            return course_code
        else:
            logger.info(
                f"No course code found in firebase for user ID: {user_id}")
            return None

    except Exception as e:
        logger.exception(
            f"Error retrieving course code for user ID {user_id}: {e}")
        return None


def set_course_code(user_id: str, course_code: str) -> None:

    try:
        db.collection('users').document(str(user_id)).update(
            {'user_entered_course_code': course_code})

    except Exception as e:
        logger.exception(
            f"Error setting course code for user ID {user_id}: {e}")


def get_saved_exams_details(user_id: str) -> dict:

    doc_ref = db.collection('users').document(user_id)
    try:
        doc = doc_ref.get()
        if doc.exists:
            exams_details = doc.to_dict()
            logger.info(f"GOT all exams details")
            return exams_details
        else:
            logger.info('No such document!')
    except Exception as e:
        logger.error(f'Error getting exams details: {e}')


def save_exams_details(user_id: str, course: str, date: str, time: str, venue) -> None:
    sanitized_course = re.sub(r'\W+', '_', course)

    try:
        db.collection('users').document(user_id).update({
            sanitized_course: {'Full_Course_Name': course,
                               'Exams_Date': date,
                               'Exams_Time': time,
                               'All_Exams_Venue': venue
                               }
        })
        logger.info(f"Exams details for {sanitized_course} saved to firebase")
    except Exception as e:
        logger.exception(
            f"Error setting exams details for {'users'}: {e}")


def get_exams_venue(user_id: str) -> str:

    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            all_exams_venue = doc.get('All_Exams_Venue')
            logger.info(
                f"Retrived venue from firebase -- {all_exams_venue}")
            return all_exams_venue
        else:
            logger.info(f"No exams venue found for user ID: {user_id}")
            return None
    except Exception as e:
        logger.exception(
            f"Error retrieving exams venue for user ID {user_id}: {e}")
        return None


def set_exact_venue(user_id: str, course, exact_venue: str) -> None:
    sanitized_course = re.sub(r'\W+', '_', course)
    try:
        db.collection('users').document(str(user_id)).update(
            {f'{sanitized_course}.Exact_Exams_Venue': exact_venue})

    except Exception as e:
        logger.exception(
            f"Error setting exact exams venue for user ID {user_id}: {e}")


def get_exact_venue(user_id: str, course):
    sanitized_course = re.sub(r'\W+', '_', course)
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            exact_exams_venue = doc.get(
                f'{sanitized_course}.Exact_Exams_Venue')
            return exact_exams_venue
        else:
            logger.info(
                f"Exact venue Not found in firebase for course: {course}")
            return None
    except Exception as e:
        logger.exception(
            f"Error getting exact exams venue for user ID {user_id}: {e}")
        return None


def set_no_id_venues(user_id: str, course: str, no_id_venue: list):
    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        # doc_ref = db.collection('users').document(user_id)
        # doc = doc_ref.get()
        if len(no_id_venue) > 0:

            db.collection('users').document(user_id).update({
                f'{sanitized_course}.No_ID_Venues': no_id_venue
            })
        else:
            db.collection('users').document(user_id).update({
                f'{sanitized_course}.No_ID_Venues': None
            })

    except Exception as e:
        logger.error(str(e))


def get_no_id_venues(user_id: str, course: str) -> list | None:
    try:
        sanitized_course = re.sub(r'\W+', '_', course)
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            no_id_venue = doc.get(f'{sanitized_course}.No_ID_Venues')
            logger.info("Got no_id_venues ✅")
            return no_id_venue
        else:
            return None

    except Exception as e:
        logger.error(f"Error getting no_id_venues \n {e}")


def delete_exams_details(user_id: str) -> None:

    try:
        courses = get_saved_exams_details(user_id).keys()
        for course in courses:
            db.collection('users').document(user_id).update({
                f"{course}": firestore.DELETE_FIELD
            })
        logger.info(f"All exams details DELETED!!")
    except Exception as e:
        print(f"An error occurred when deleting: {e}")


if __name__ == "__main__":
    user_id = "123456789"
    # set_course_code(user_id, "UGBS303")
    # save_exams_details(user_id, "UGBS303 - COMPUTER APPLICATIONS IN MANAGEMENT", "01 March 2024",
    #                  "02:32 pm", "UGCS LAB 3 MAIN")
    # set_exact_venue(
    #     user_id, "UGBS303_COMPUTER_APPLICATIONS_IN_MANAGEMENT", "UGCS LAB 3 MAIN")
    # get_exact_venue(user_id, "UGBS303 - COMPUTER APPLICATIONS IN MANAGEMENT")
    # get_saved_exams_details(user_id)
    # get_exams_venue(user_id)
    # get_course_code(user_id)
    delete_exams_details(
        user_id)
