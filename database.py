import os
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_URL")
    })
except Exception as e:
    print(f"❌ خطأ في تهيئة Firebase: {e}")
    raise e

def get_user(user_id):
    """جلب بيانات المستخدم مع ضمان عدم إرجاع None"""
    data = db.reference(f'Users/{user_id}').get()
    return data if data else {}

def create_user(user_id, name):
    ref = db.reference(f'Users/{user_id}')
    if not ref.get():
        ref.set({
            "name": name,
            "class": "D",
            "points": 20000,
            "reputation": 100,
            "inventory": [],
            "last_daily": None
        })

def get_all_users():
    return db.reference('Users').get() or {}

def update_points(user_id, amount):
    ref = db.reference(f'Users/{user_id}/points')
    current = ref.get() or 0
    new_points = max(0, current + amount)  # لا يقل عن صفر
    ref.set(new_points)

def set_last_daily(user_id, timestamp):
    # timestamp هو كائن datetime، نخزنه كنص ISO
    db.reference(f'Users/{user_id}/last_daily').set(timestamp.isoformat())

def add_to_inventory(user_id, item_id):
    ref = db.reference(f'Users/{user_id}/inventory')
    current_inv = ref.get() or []
    if item_id not in current_inv:
        current_inv.append(item_id)
        ref.set(current_inv)
