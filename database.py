import os
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from dotenv import load_dotenv

# تحميل الإعدادات
load_dotenv()

# تهيئة الاتصال
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_URL")
    })
except Exception as e:
    print(f"❌ خطأ في تهيئة Firebase: {e}")
    raise e

def get_user(user_id):
    """
    جلب بيانات المستخدم مع تحويل last_daily من نص ISO إلى كائن datetime.
    هذا التعديل ضروري جداً لكي تعمل دالة show_missions في main.py دون أخطاء.
    """
    data = db.reference(f'Users/{user_id}').get()
    if data:
        if data.get("last_daily"):
            try:
                # تحويل النص المحفوظ (مثال: '2026-04-10T12:00:00+00:00') إلى كائن وقت
                data["last_daily"] = datetime.fromisoformat(data["last_daily"])
            except (ValueError, TypeError):
                # في حال كان التنسيق قديم أو تالف، نعيده لـ None لتجنب تعطيل البوت
                data["last_daily"] = None
        return data
    else:
        return {}

def create_user(user_id, name):
    """إنشاء مستخدم جديد بنظام النقاط الافتراضي"""
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
    """جلب قائمة جميع الطلاب"""
    return db.reference('Users').get() or {}

def update_points(user_id, amount):
    """
    زيادة أو نقص النقاط مع آلية حماية من القيم السالبة.
    (تعديل ذكي يحافظ على اقتصاد النظام)
    """
    ref = db.reference(f'Users/{user_id}/points')
    current_points = ref.get() or 0
    # المعادلة: إذا كان الخصم سيؤدي لرصيد سالب، نثبته على 0
    new_points = max(0, current_points + amount)
    ref.set(new_points)

def set_last_daily(user_id, timestamp):
    """
    تسجيل تاريخ آخر مكافأة يومية.
    نستقبل كائن datetime ونحوله لنص ISO لتخزينه في Firebase.
    """
    db.reference(f'Users/{user_id}/last_daily').set(timestamp.isoformat())

def add_to_inventory(user_id, item_id):
    """إضافة المشتريات إلى حقيبة المستخدم"""
    ref = db.reference(f'Users/{user_id}/inventory')
    current_inv = ref.get() or []
    if item_id not in current_inv:
        current_inv.append(item_id)
        ref.set(current_inv)
