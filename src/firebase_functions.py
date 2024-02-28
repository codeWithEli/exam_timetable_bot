""" firebase helper functions"""
import logging
import os

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
    """
    Retrieves the course code for the given user ID from Firestore.

    Args:
        user_id: The user ID to retrieve the course code for.

    Returns:
        The course code if found, otherwise None.
    """

    try:
        doc_ref = db.collection('users').document(str(user_id))
        doc = doc_ref.get()

        if doc.exists:
            return doc.get('course_name')
        else:
            logger.info(f"No course code found for user ID: {user_id}")
            return None

    except Exception as e:
        logger.exception(
            f"Error retrieving course code for user ID {user_id}: {e}")
        return None  # Indicate failure by returning None


def set_course_code(user_id: str, course_code: str) -> None:
    """
    Sets the course code for the given user ID in Firestore.

    Args:
        user_id: The user ID to set the course code for.
        course_code: The course code to set.
    """

    try:
        db.collection('users').document(str(user_id)).set(
            {'course_name': course_code})

    except Exception as e:
        logger.exception(
            f"Error setting course code for user ID {user_id}: {e}")
