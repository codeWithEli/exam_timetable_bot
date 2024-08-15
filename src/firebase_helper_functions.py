import logging
import re
import os
from typing import Optional
from firebase_init import db, storage




class FirebaseHelperFunctions(): 
    def __init__(self, user_id: str ):

        self.user_id = user_id

        # log config
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

        try:
            # cred = credentials.Certificate("./serviceAccount.json")

            # # Initialize Firebase app
            # firebase_admin.initialize_app(
            #     cred, {"storageBucket": "ug-exams-bot.appspot.com"})

            self.db = db
            self.doc_ref = self.db.collection(self.user_id)
            self.bucket = storage.bucket()

        except FileNotFoundError as e:
            self.logger.error(f"🔥Error loading service account credentials: {e}")
            raise

        except Exception as e:
            self.logger.exception(f"🔥Unexpected error initializing Firebase app: {e}")
            raise



    def save_exact_venue_details(self,  course: str, course_info: dict) -> None:
        """Save all exams details to firebase"""
        try:
            sanitized_course = re.sub(r'\W+', '_', course.strip())
            doc = self.doc_ref.document('ExactVenuesDetails')
            
            if doc.get().exists:
                doc.update({
                    sanitized_course: course_info
                })
            else:
                doc.create(document_data={
                    sanitized_course: course_info
                })
        except Exception as e:
            self.logger.exception(
                f"🔥Error saving exams details: {e}"
            )

    def save_exact_venue_not_found_details(self,  course: str, course_info: dict) -> None:
        """Save exact venue not found details to firebase"""
        try:
            sanitized_course = re.sub(r'\W+', '_', course.strip())
            doc = self.doc_ref.document('NotExactVenuesDetails')
            
            if doc.get().exists:
                doc.update({
                    sanitized_course: course_info
                })
            else:
                doc.create(document_data={
                    sanitized_course: course_info
                })

        
        except Exception as e:
            self.logger.exception(
                f"🔥Error saving exact venue not found details {e}"
            )
            raise

   

    def get_exact_venue_info(self, course: str) -> dict | None:
        """
        Get exams info in exact venue details
        """
        try:
            doc = self.doc_ref.document('ExactVenuesDetails')

            if doc.get().exists:
                exams_info = doc.get([f'{course}']).to_dict()
                info = exams_info.get(course, {})
                # self.logger.info(f'exams_info: {exams_info}')
                return info
            
            else:
                return None
        except KeyError as e:
            self.logger.exception(
                f"🔥Error getting exams info : {e}")
            return None
        

    def get_not_exact_venue_info(self, course: str) -> dict | None:
        """
        Get exams info from NotExactVenuesDetails
        """
        try:
            doc = self.doc_ref.document('NotExactVenuesDetails')

            if doc.get().exists:
                exams_info = doc.get([f'{course}']).to_dict()
                info = exams_info.get(course, {})
                # self.logger.info(f'exams_info: {exams_info}')
                return info
            else:
                return None
        except KeyError as e:
            self.logger.exception(
                f"🔥Error getting exams info - {e}")
            return None
        
    def get_exact_venue_keys(self) -> list | None:
        """
        Get exams info in exact venue details
        """
        try:
            doc = self.doc_ref.document('ExactVenuesDetails')

            if doc.get().exists:
                exams_info = list(doc.get().to_dict().keys())
                # self.logger.info(f'exams_info: {exams_info}')
                return exams_info
            
            else:
                return None
        except KeyError as e:
            self.logger.exception(
                f"🔥Error getting exams info : {e}")
            return None
        

    def get_not_exact_venue_keys(self) -> list | None:
        """
        Get exams info from NotExactVenuesDetails
        """
        try:
            doc = self.doc_ref.document('NotExactVenuesDetails')

            if doc.get().exists:
                exams_info = list(doc.get().to_dict().keys())
                # self.logger.info(f'exams_info: {exams_info}')
                return exams_info
            else:
                return None
        except KeyError as e:
            self.logger.exception(
                f"🔥Error getting exams info - {e}")
            return None
        
    def delete_exams_details(self) -> None:
        """
        Delete saved exams details from user document
        """

        try:
            self.doc_ref.document('ExactVenuesDetails').delete()
            self.doc_ref.document('NotExactVenuesDetails').delete()
            return None

        except Exception as e:
            self.logger.error(f"🔥An error occurred while deleting exams details: {e}")
            raise

    def upload_to_firebase(self, local_file_path: str, remote_file_name: str) -> str:
        """
        Upload calender.ics file to firebase 
        delete local copy and
        return a public url of the screenshot
        """

        try:
            # Upload to firebase storage
            bucket = storage.bucket()
            blob = bucket.blob(f"calendars/{user_id}/{remote_file_name}")
            blob.upload_from_filename(local_file_path)

            # return public url
            blob.make_public()
            public_url = blob.public_url

            # delete local copy
            os.remove(local_file_path)

            return public_url

        except Exception as e:
           self.logger.exception(f'🔥Upload calendar failed : {str(e)}')
           raise
        


    def delete_from_firebase_storage(self, remote_file_name: str):
        """
        Delete screenshot from firebase
        """

        try:
            bucket = storage.bucket()
            blob = bucket.blob(f"screenshots/{user_id}/{remote_file_name}")
            blob.delete()

        except Exception as e:
           self.logger.error(f"🔥Error deleting screenshot - {str(e)}")
           raise



if __name__ == "__main__":
    user_id = "123456789"
    if user_id:
        firebase_helper = FirebaseHelperFunctions(user_id)
        
        firebase_helper.save_exact_venue_details("Math", {"venue": "Room 1013", "time": "9:00 AM"}) 
        firebase_helper.save_exact_venue_not_found_details("Physics", {"venue": "Not found", "time": "2:00 PM"}) 
        firebase_helper.get_exact_venue_info("Math")
        firebase_helper.get_not_exact_venue_info("Physics") 
        firebase_helper.get_exact_venue_keys()
        firebase_helper.get_not_exact_venue_keys() 
        firebase_helper.delete_exams_details() 
        # firebase_helper.upload_to_firebase(user_id,"local_file_path", "remote_file_name") 
        # firebase_helper.delete_from_firebase_storage(user_id,"remote_file_name")
        print("Done")
