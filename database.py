import firebase_admin
from firebase_admin import credentials, db

# إعداد الربط
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'رابط_قاعدة_بياناتك_هنا'
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

def update_points(user_id, amount):
    ref = db.reference(f'Users/{user_id}/points')
    current = ref.get() or 0
    ref.set(current + amount)

def get_class_points():
    # لجلب مجموع نقاط كل فصل للتقارير
    users = db.reference('Users').get()
    classes = {"A": 0, "B": 0, "C": 0, "D": 0}
    if users:
        for uid in users:
            cls = users[uid].get("class", "D")
            classes[cls] += users[uid].get("points", 0)
    return classes
  
