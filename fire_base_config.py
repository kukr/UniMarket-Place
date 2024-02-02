from pyrebase import initialize_app
from firebase_admin import auth as fba_auth, credentials
import firebase_admin
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

# Update firebaseConfig dictionary to use environment variables
firebaseConfig = {
  "apiKey": os.getenv('FIREBASE_API_KEY'),
  "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
  "databaseURL": os.getenv('FIREBASE_DATABASE_URL'),
  "projectId": os.getenv('FIREBASE_PROJECT_ID'),
  "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
  "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
  "appId": os.getenv('FIREBASE_APP_ID')
}

firebase=initialize_app(firebaseConfig)
auth=firebase.auth()
db = firebase.databaṣse()
users_ref = db.child("users")
products_ref = db.child("products")
offers_ref = db.child("offers")

# Initialize Firebase Admin SDK
cred = credentials.Certificate("cs409-95e5e-fcb8ed9d33f0.json")
firebase_admin.initialize_app(cred)

print(products_ref.get().val())