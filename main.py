import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

import database as db_logic

# ========== إعداد التسجيل ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ========== تحميل التوكن ==========
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ لم يتم العثور على BOT_TOKEN في ملف .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== بيانات المتجر ==========
SHOP_ITEMS = {
    "private_point_x2": {"name": "مضاعف نقاط (مرة واحدة)", "cost": 3000, "emoji": "⚡"},
    "class_transfer": {"name": "تذكرة نقل فصل", "cost": 15000, "emoji": "🎫"},
    "reputation_boost": {"name": "تعزيز السمعة +10%", "cost": 2000, "emoji": "📈"}
}

# ========== لوحة المفاتيح الرئيسية ==========
def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="⌬ الملف الشخصي"),
        types.KeyboardButton(text="⌬ ترتيب الفصول")
    )
    builder.row(
        types.KeyboardButton(text="⌬ المتجر (S-System)"),
        types.KeyboardButton(text="⌬ لوحة القوانين")
    )
    builder.row(
        types.KeyboardButton(text="⌬ المهام اليومية"),
        types.KeyboardButton(text="⌬ الدعم التقني")
    )
    return builder.as_markup(resize_keyboard=True)

# ========== بداية التشغيل ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        name = message.from_user.full_name
        if not name:
            name = message.from_user.first_name or f"Student_{message.from_user.id}"

        db_logic.create_user(message.from_user.id, name)
        logger.info(f"تم تسجيل/تحديث المستخدم {message.from_user.id}")

        welcome = (
            "⌬ **نظام Arise OS: تم تفعيل البروتوكول**\n\n"
            f"مرحباً بك، {name}.\n"
            "تم تخصيص معرف رقمي لك في قاعدة البيانات.\n\n"
            "*استخدم لوحة التحكم أدناه لاستعراض النظام.*"
        )
        await message.answer(welcome, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"خطأ في /start: {e}")
        await message.answer("⚠️ حدث خلل في التهيئة. تواصل مع الدعم الفني.")

# ========== الملف الشخصي (بدون صورة) ==========
@dp.message(F.text == "⌬ الملف الشخصي")
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    try:
        user = db_logic.get_user(user_id)
        if not user:
            await message.answer("❌ لم يتم العثور على ملفك. اضغط /start أولاً.")
            return

        profile_text = (
            f"⌬ **بطاقة تعريف الطالب** ⌬\n\n"
            f"• الاسم: {user.get('name', 'غير معروف')}\n"
            f"• الفصل: {user.get('class', 'D')}\n"
            f"• الرصيد: {user.get('points', 0):,} PP\n"
            f"• السمعة: {user.get('reputation', 100)}%\n"
            f"• العناصر المملوكة: {len(user.get('inventory', []))}\n\n"
            "*النتائج هي كل ما يهم.*"
        )
        await message.answer(profile_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"خطأ في الملف الشخصي: {e}")
        await message.answer("⚠️ تعذر جلب الملف الشخصي حالياً.")

# ========== ترتيب الفصول (نصي) ==========
@dp.message(F.text == "⌬ ترتيب الفصول")
async def show_leaderboard(message: types.Message):
    try:
        users = db_logic.get_all_users()
        class_points = {"A": 0, "B": 0, "C": 0, "D": 0}

        for uid, data in users.items():
            cls = data.get("class", "D")
            class_points[cls] += data.get("points", 0)

        sorted_classes = sorted(class_points.items(), key=lambda x: x[1], reverse=True)

        text = "⌬ **ترتيب كفاءة الفصول المركزية** ⌬\n\n"
        for i, (cls, pts) in enumerate(sorted_classes, 1):
            text += f"{i}. **Class {cls}** | {pts:,} PP\n"
        text += "\n*(يتم تحديث البيانات لحظياً من الذاكرة المركزية)*"

        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"خطأ في ترتيب الفصول: {e}")
        await message.answer("⚠️ تعذر عرض الترتيب حالياً.")

# ========== المتجر ==========
@dp.message(F.text == "⌬ المتجر (S-System)")
async def show_shop(message: types.Message):
    text = "⌬ **السوق المظلم (S-System)** ⌬\n\n"
    for item_id, item in SHOP_ITEMS.items():
        text += f"{item['emoji']} /buy_{item_id} : {item['name']} - {item['cost']:,} PP\n"
    text += "\n*استخدم الأمر /buy_... لشراء العنصر.*"
    await message.answer(text, parse_mode="Markdown")

async def process_purchase(message: types.Message, item_id: str):
    user_id = message.from_user.id
    user = db_logic.get_user(user_id)
    if not user:
        await message.answer("❌ لم يتم العثور على ملفك. اضغط /start أولاً.")
        return

    item = SHOP_ITEMS.get(item_id)
    if not item:
        await message.answer("❌ عنصر غير معروف.")
        return

    if user["points"] < item["cost"]:
        await message.answer(f"❌ رصيدك غير كافٍ. تحتاج {item['cost']:,} PP.")
        return

    db_logic.update_points(user_id, -item["cost"])
    db_logic.add_to_inventory(user_id, item_id)

    await message.answer(
        f"✅ تم شراء **{item['name']}** بنجاح!\n"
        f"تم خصم {item['cost']:,} PP من رصيدك.",
        parse_mode="Markdown"
    )
    logger.info(f"المستخدم {user_id} اشترى {item_id}")

@dp.message(Command("buy_private_point_x2"))
async def buy_double_points(message: types.Message):
    await process_purchase(message, "private_point_x2")

@dp.message(Command("buy_class_transfer"))
async def buy_class_transfer(message: types.Message):
    await process_purchase(message, "class_transfer")

@dp.message(Command("buy_reputation_boost"))
async def buy_reputation_boost(message: types.Message):
    await process_purchase(message, "reputation_boost")

# ========== لوحة القوانين ==========
@dp.message(F.text == "⌬ لوحة القوانين")
async def show_rules(message: types.Message):
    text = (
        "⌬ **دستور نظام Arise** ⌬\n\n"
        "1. الغباء ليس عذراً.\n"
        "2. يُسمح باستخدام كافة الاستراتيجيات للفوز.\n"
        "3. الطالب الذي يفقد رصيده بالكامل، يُطرد من النظام.\n"
        "4. المهام اليومية تُمنح مرة كل 24 ساعة."
    )
    await message.answer(text, parse_mode="Markdown")

# ========== المهام اليومية ==========
@dp.message(F.text == "⌬ المهام اليومية")
async def show_missions(message: types.Message):
    user_id = message.from_user.id
    user = db_logic.get_user(user_id)
    if not user:
        await message.answer("❌ الرجاء الضغط على /start أولاً.")
        return

    now = datetime.now(timezone.utc)
    last_daily = user.get("last_daily")

    if last_daily:
        if hasattr(last_daily, "astimezone"):
            last_daily = last_daily.astimezone(timezone.utc)
        if now - last_daily < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_daily)
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes = remainder // 60
            await message.answer(
                f"⏳ لقد استلمت مكافأتك اليومية بالفعل.\n"
                f"الوقت المتبقي: {hours} ساعة و {minutes} دقيقة."
            )
            return

    reward = 5000
    db_logic.update_points(user_id, reward)
    db_logic.set_last_daily(user_id, now)
    await message.answer(
        f"⌬ **تم إكمال المهمة اليومية!** ⌬\n\n"
        f"✅ تمت إضافة {reward:,} PP إلى رصيدك.\n"
        f"عد غداً لمهمة جديدة.",
        parse_mode="Markdown"
    )
    logger.info(f"مستخدم {user_id} استلم مكافأة يومية {reward}")

# ========== الدعم التقني ==========
@dp.message(F.text == "⌬ الدعم التقني")
async def show_support(message: types.Message):
    text = (
        "⌬ **وحدة الدعم التقني**\n\n"
        "للإبلاغ عن ثغرات أو مشاكل، تواصل مع: @YourUsername\n"
        "أو استخدم أمر /report متبوعاً برسالتك."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("report"))
async def report_bug(message: types.Message):
    await message.answer("📨 تم استلام بلاغك. شكراً لمساهمتك في تحسين النظام.")

# ========== حماية من الرسائل العشوائية ==========
@dp.message()
async def unknown_message(message: types.Message):
    if not message.text.startswith("/"):
        await message.answer(
            "⌬ أمر غير معترف به.\nيرجى استخدام الأزرار المتاحة في لوحة التحكم.",
            reply_markup=main_menu_keyboard()
        )

# ========== معالجة الأخطاء العامة ==========
@dp.errors()
async def errors_handler(update: types.Update, exception: Exception):
    logger.exception(f"حدث خطأ غير معالج: {exception}")
    return True

# ========== تشغيل البوت ==========
async def main():
    logger.info(">>> Arise OS Engine: ONLINE")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"فشل تشغيل البوت: {e}")

if __name__ == "__main__":
    asyncio.run(main())
