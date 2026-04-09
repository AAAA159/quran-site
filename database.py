import os
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

load_dotenv()

# إعداد Firebase باستخدام ملف الـ JSON
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_URL")
})

def get_user(user_id):
    return db.reference(f'Users/{user_id}').get()

def create_user(user_id, name):
    if not get_user(user_id):
        db.reference(f'Users/{user_id}').set({
            "name": name,
            "class": "D",
            "points": 20000,
            "reputation": 100
        })

def get_all_users():
    return db.reference('Users').get() or {}

def update_user_points(user_id, amount):
    ref = db.reference(f'Users/{user_id}/points')
    current = ref.get() or 0
    ref.set(current + amount)
