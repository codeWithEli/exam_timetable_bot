import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage

# Read service account credentials securely using a context manager
cred = credentials.Certificate("./serviceAccount.json")

# Initialize Firebase app
firebase_admin.initialize_app(
    cred, {"storageBucket": "ug-exams-bot.appspot.com"})
db = firestore.client()
storage = storage