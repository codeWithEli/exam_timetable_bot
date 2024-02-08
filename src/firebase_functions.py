""" firebase helper functions"""
import os


import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage


cred = credentials.Certificate('src/serviceAccount.json')
firebase_admin.initialize_app(
    cred, {"storageBucket": "ug-exams-bot.appspot.com"})


def upload_to_firebase_storage(local_file_path: str, remote_file_name: str) -> str:
    """
    Upload screenschot to firebase 
    delete local copy and
    return a public url of the screenshot
    """

    try:
        # Upload to firebase storage
        bucket = storage.bucket()
        blob = bucket.blob(f"screenshots/{remote_file_name}")
        blob.upload_from_filename(local_file_path)

        print("Screenshot uploaded to firebase!")

        # delete local copy
        os.remove(local_file_path)

        # return public url
        blob.make_public()
        public_url = blob.public_url

        return public_url

    except Exception as e:
        print(str(e))
