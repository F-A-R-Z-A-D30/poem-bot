from flask import Flask
from threading import Thread
import requests
import time
import random
import data  # فایل شعرهای محلی تو
import sqlite3
import os
import logging

# ==========================================
TOKEN = "1613886570:03yF4qFiCCT3p8AhkplRwCIKeXCZi_BY9aM"
# ==========================================

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# --- کاهش لاگ‌های Flask ---
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- سرور Flask با تنظیمات بهینه‌تر ---
app = Flask(__name__)

# غیرفعال کردن پیغام‌های دیباگ
app.debug = False


@app.route('/')
def home():
    return "🤖 Poetry Bot is Running!"


@app.route('/health')
def health_check():
    return {"status": "healthy", "service": "poetry-bot"}


@app.route('/ping')
def ping():
    return "pong"


def run_http():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)


def keep_alive():
    t = Thread(target=run_http, daemon=True)
    t.start()
    print(f"🌐 سرور Flask روی پورت {os.environ.get('PORT', 8080)} راه‌اندازی شد")


# --- مدیر API و داده‌های محلی ---
class SmartPoemManager:
    def __init__(self):
        print("📖 در حال بارگذاری داده‌های شعر...")
        # داده‌های محلی اصلی
        self.local_poems = {
            "hafez": data.POEMS.get("hafez", []),
            "saadi": data.POEMS.get("saadi", []),
            "molana": data.POEMS.get("molana", [])
        }

        print(
            f"✅ داده‌های محلی بارگذاری شد: حافظ({len(self.local_poems['hafez'])}), سعدی({len(self.local_poems['saadi'])}), مولانا({len(self.local_poems['molana'])})")

        # API گنجگاه (بهترین API فارسی)
        self.api_url = "https://api.ganjgah.ir/api/v1/poem/random"
        self.poets_map = {"hafez": "حافظ", "saadi": "سعدی", "molana": "مولانا"}

        # تنظیمات
        self.use_api = True
        self.cache_enabled = True
        self._init_cache()

    def _init_cache(self):
        """ایجاد کش برای اشعار API"""
        try:
            conn = sqlite3.connect('api_poems_cache.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_poems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poet TEXT,
                    verse1 TEXT,
                    verse2 TEXT,
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_poet ON api_poems(poet)')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ خطا در راه‌اندازی کش: {e}")

    def _get_from_api(self, poet):
        """دریافت شعر از API گنجگاه"""
        if poet not in self.poets_map:
            return None

        try:
            response = requests.get(
                self.api_url,
                params={"poet": self.poets_map[poet]},
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    poem_data = data[0]
                    poem_text = poem_data.get('poem', '')

                    # پردازش متن شعر
                    lines = []
                    for line in poem_text.split('\n'):
                        line = line.strip()
                        if line and len(line) > 5:  # خطوط خیلی کوتاه رو حذف کن
                            lines.append(line)

                    # انتخاب بهترین خطوط
                    if len(lines) >= 2:
                        # برای حافظ و سعدی، سعی کن بیت کامل پیدا کنی
                        if poet in ["hafez", "saadi"]:
                            # دنبال خطوطی بگرد که نشانه بیت هستند
                            for i in range(len(lines) - 1):
                                line1 = lines[i]
                                line2 = lines[i + 1]
                                # اگر هر دو خط معنی دار باشند
                                if len(line1) > 10 and len(line2) > 10:
                                    return f"{line1}\n{line2}"

                        # اگر بیت کامل پیدا نکردی، دو خط اول رو بگیر
                        return f"{lines[0]}\n{lines[1]}"
                    elif len(lines) == 1:
                        return lines[0]
                    else:
                        return poem_text[:300]  # محدود کردن طول
        except Exception as e:
            print(f"⚠️ خطا در دریافت از API: {e}")

        return None

    def _save_to_cache(self, poet, verse1, verse2, source):
        """ذخیره شعر در کش"""
        if not self.cache_enabled or not verse1:
            return

        try:
            conn = sqlite3.connect('api_poems_cache.db')
            cursor = conn.cursor()
            # حذف رکوردهای قدیمی (نگهداری فقط 50 شعر برای هر شاعر)
            cursor.execute('''
                DELETE FROM api_poems 
                WHERE id IN (
                    SELECT id FROM api_poems 
                    WHERE poet = ? 
                    ORDER BY created_at DESC 
                    LIMIT -1 OFFSET 50
                )
            ''', (poet,))

            # اضافه کردن شعر جدید
            cursor.execute(
                "INSERT INTO api_poems (poet, verse1, verse2, source) VALUES (?, ?, ?, ?)",
                (poet, verse1, verse2 or "", source)
            )
            conn.commit()
            conn.close()
        except:
            pass

    def _get_from_cache(self, poet):
        """دریافت شعر از کش"""
        try:
            conn = sqlite3.connect('api_poems_cache.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT verse1, verse2 FROM api_poems WHERE poet = ? ORDER BY RANDOM() LIMIT 1",
                (poet,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                verse1, verse2 = result
                if verse2:
                    return f"{verse1}\n{verse2}"
                return verse1
        except:
            pass
        return None

    def get_poem(self, poet, use_api=True):
        """دریافت شعر با ترتیب هوشمند"""
        # 1. استفاده از API (اگر فعال باشد)
        if use_api and self.use_api:
            api_poem = self._get_from_api(poet)
            if api_poem:
                # ذخیره در کش
                lines = api_poem.split('\n')
                verse1 = lines[0] if len(lines) > 0 else ""
                verse2 = lines[1] if len(lines) > 1 else ""
                self._save_to_cache(poet, verse1, verse2, "api")
                return api_poem

            # 2. از کش بگیر
            cached_poem = self._get_from_cache(poet)
            if cached_poem:
                return cached_poem

        # 3. از داده‌های محلی (همیشه قابل اعتماد)
        if poet in self.local_poems and self.local_poems[poet]:
            poem = random.choice(self.local_poems[poet])
            # تبدیل فرمت --- به خط جدید
            if " --- " in poem:
                poem = poem.replace(" --- ", "\n")
            return poem

        # 4. پیام پیش‌فرض
        default_poems = {
            "hafez": "الا یا ایها الساقی ادر کأسا و ناولها\nکه عشق آسان نمود اول ولی افتاد مشکل‌ها",
            "saadi": "بنی آدم اعضای یک پیکرند\nکه در آفرینش ز یک گوهرند",
            "molana": "بی‌همگان به سر شود بی‌تو به سر نمی‌شود\nداغ تو دارد این دلم جای دگر نمی‌شود"
        }
        return default_poems.get(poet, "شعری یافت نشد.")


# --- مقداردهی اولیه ---
print("🤖 در حال راه‌اندازی ربات شعر...")
poem_manager = SmartPoemManager()

# --- دیکشنری برای حالت کاربران ---
user_modes = {}
user_stats = {}


# --- کیبوردهای مختلف ---
def get_main_keyboard():
    """کیبورد اصلی"""
    return {
        "keyboard": [
            [{"text": "📖 فال حافظ"}, {"text": "🌿 پند سعدی"}],
            [{"text": "🔥 اشعار مولانا"}, {"text": "🎲 شعر تصادفی"}],
            [{"text": "⚙️ تنظیمات"}, {"text": "📊 آمار ربات"}],
            [{"text": "📞 درباره ما"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def get_settings_keyboard(current_mode):
    """کیبورد تنظیمات"""
    online_btn = "✅ آنلاین" if current_mode == "online" else "آنلاین"
    offline_btn = "✅ آفلاین" if current_mode == "offline" else "آفلاین"

    return {
        "keyboard": [
            [{"text": online_btn}, {"text": offline_btn}],
            [{"text": "🔙 برگشت به منوی اصلی"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def get_stats_keyboard():
    """کیبورد آمار"""
    return {
        "keyboard": [
            [{"text": "📈 آمار من"}, {"text": "📊 آمار کلی"}],
            [{"text": "🔙 برگشت به منوی اصلی"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


# --- توابع کمکی ---
def send_message(chat_id, text, keyboard=None, parse_mode="HTML"):
    """ارسال پیام"""
    url = f"{BASE_URL}/sendMessage"

    if keyboard is None:
        keyboard = get_main_keyboard()

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard,
        "parse_mode": parse_mode
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False


def send_poem_message(chat_id, poet_name, poem_text):
    """ارسال شعر با فرمت زیبا"""
    # ایموجی برای هر شاعر
    emojis = {
        "hafez": "📖",
        "saadi": "🌿",
        "molana": "🔥"
    }

    emoji = emojis.get(poet_name, "🎲")

    # متن نهایی
    message = f"{emoji} <b>شعر زیبا</b>\n\n"
    message += f"{poem_text}\n\n"
    message += f"<i>دیوان {poet_name.capitalize()}</i>"

    send_message(chat_id, message)


def get_updates(offset=0):
    """دریافت آپدیت‌ها"""
    try:
        url = f"{BASE_URL}/getUpdates"
        params = {"offset": offset, "timeout": 10, "limit": 100}
        response = requests.get(url, params=params, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None


def update_user_stats(chat_id, poet):
    """به‌روزرسانی آمار کاربر"""
    if chat_id not in user_stats:
        user_stats[chat_id] = {"total": 0, "hafez": 0, "saadi": 0, "molana": 0, "random": 0}

    user_stats[chat_id]["total"] += 1
    if poet in user_stats[chat_id]:
        user_stats[chat_id][poet] += 1


# --- تابع اصلی ربات ---
def main():
    print("✅ ربات شعر آماده است!")
    print(f"📞 آدرس وب: http://0.0.0.0:{os.environ.get('PORT', 8080)}")

    last_update_id = 0

    while True:
        try:
            updates = get_updates(last_update_id + 1)

            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    last_update_id = update["update_id"]

                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_text = update["message"]["text"].strip()

                        # تنظیم حالت پیش‌فرض
                        if chat_id not in user_modes:
                            user_modes[chat_id] = "online"

                        current_mode = user_modes[chat_id]

                        # پردازش دستورات
                        if user_text == "/start":
                            welcome = """<b>🌹 سلام! به ربات شعر فارسی خوش آمدید</b>

من می‌توانم زیباترین شعرهای فارسی را برای شما بخوانم:

<b>📚 دسترسی سریع:</b>
📖 فال حافظ - غزلیات زیبای حافظ
🌿 پند سعدی - حکمت‌های ناب سعدی  
🔥 اشعار مولانا - اشعار عرفانی مولانا
🎲 شعر تصادفی - یک شعر زیبا از هر شاعر

<b>⚙️ حالت فعلی:</b> """ + ("آنلاین 🌐" if current_mode == "online" else "آفلاین 💾")

                            send_message(chat_id, welcome)

                        elif user_text == "📖 فال حافظ":
                            use_api = (current_mode == "online")
                            poem = poem_manager.get_poem("hafez", use_api)
                            update_user_stats(chat_id, "hafez")

                            # اضافه کردن یک پیام فال
                            fal_message = "<b>📖 فال حافظ</b>\n\n"
                            fal_message += "«به نیت دل، فال زیبای حافظ را باز کردیم...»\n\n"
                            fal_message += poem
                            fal_message += "\n\n<b>تفسیر:</b> این شعر نشان از عشق، صبر و امید دارد."

                            send_message(chat_id, fal_message)

                        elif user_text == "🌿 پند سعدی":
                            use_api = (current_mode == "online")
                            poem = poem_manager.get_poem("saadi", use_api)
                            update_user_stats(chat_id, "saadi")

                            # برای سعدی، اگر شعر کوتاه بود یکی دیگه اضافه کن
                            lines = poem.split('\n')
                            if len(lines) == 1 or len(poem) < 30:
                                poem2 = poem_manager.get_poem("saadi", use_api)
                                if poem2 != poem:
                                    poem = f"{poem}\n\n{poem2}"

                            pand_message = "<b>🌿 پند سعدی</b>\n\n"
                            pand_message += "«حکمت زیبای سعدی شیرازی»\n\n"
                            pand_message += poem
                            pand_message += "\n\n<i>گلستان و بوستان سعدی</i>"

                            send_message(chat_id, pand_message)

                        elif user_text == "🔥 اشعار مولانا":
                            use_api = (current_mode == "online")
                            poem = poem_manager.get_poem("molana", use_api)
                            update_user_stats(chat_id, "molana")

                            molana_message = "<b>🔥 مولانا جلال‌الدین رومی</b>\n\n"
                            molana_message += "«اشعار عاشقانه و عرفانی»\n\n"
                            molana_message += poem
                            molana_message += "\n\n<i>مثنوی معنوی</i>"

                            send_message(chat_id, molana_message)

                        elif user_text == "🎲 شعر تصادفی":
                            poets = ["hafez", "saadi", "molana"]
                            poet = random.choice(poets)
                            poet_names = {"hafez": "حافظ", "saadi": "سعدی", "molana": "مولانا"}

                            use_api = (current_mode == "online")
                            poem = poem_manager.get_poem(poet, use_api)
                            update_user_stats(chat_id, "random")

                            random_message = f"<b>🎲 شعر تصادفی از {poet_names[poet]}</b>\n\n"
                            random_message += poem

                            send_message(chat_id, random_message)

                        elif user_text == "⚙️ تنظیمات":
                            settings_msg = f"""<b>⚙️ تنظیمات ربات</b>

<b>حالت فعلی:</b>
{'✅ آنلاین - دریافت شعرهای جدید از اینترنت' if current_mode == 'online' else '✅ آفلاین - استفاده از داده‌های داخلی'}

<b>گزینه‌ها:</b>
• آنلاین: شعرهای تازه‌تر اما ممکن است کمی کندتر باشد
• آفلاین: شعرهای داخلی با سرعت بالا

لطفاً حالت مورد نظر را انتخاب کنید:"""

                            send_message(chat_id, settings_msg, get_settings_keyboard(current_mode))

                        elif user_text == "✅ آنلاین" or user_text == "آنلاین":
                            user_modes[chat_id] = "online"
                            send_message(chat_id,
                                         "✅ <b>حالت آنلاین فعال شد!</b>\n\nاکنون از اینترنت برای دریافت شعرهای جدید استفاده می‌شود.",
                                         get_main_keyboard())

                        elif user_text == "✅ آفلاین" or user_text == "آفلاین":
                            user_modes[chat_id] = "offline"
                            send_message(chat_id,
                                         "📂 <b>حالت آفلاین فعال شد!</b>\n\nاکنون فقط از داده‌های داخلی استفاده می‌شود.",
                                         get_main_keyboard())

                        elif user_text == "🔙 برگشت به منوی اصلی":
                            send_message(chat_id, "منوی اصلی:", get_main_keyboard())

                        elif user_text == "📊 آمار ربات":
                            send_message(chat_id, "📊 <b>بخش آمار ربات</b>\n\nلطفاً نوع آمار را انتخاب کنید:",
                                         get_stats_keyboard())

                        elif user_text == "📈 آمار من":
                            if chat_id in user_stats:
                                stats = user_stats[chat_id]
                                personal_stats = f"""<b>📈 آمار استفاده شما</b>

<b>تعداد کل درخواست‌ها:</b> {stats['total']}

<b>تعداد به تفکیک:</b>
📖 فال حافظ: {stats.get('hafez', 0)} بار
🌿 پند سعدی: {stats.get('saadi', 0)} بار
🔥 مولانا: {stats.get('molana', 0)} بار
🎲 تصادفی: {stats.get('random', 0)} بار

<b>حالت فعلی:</b> {'آنلاین 🌐' if user_modes.get(chat_id, 'online') == 'online' else 'آفلاین 💾'}"""
                            else:
                                personal_stats = "هنوز هیچ آماری برای شما ثبت نشده است. شروع به استفاده از ربات کنید!"

                            send_message(chat_id, personal_stats, get_stats_keyboard())

                        elif user_text == "📊 آمار کلی":
                            try:
                                conn = sqlite3.connect('api_poems_cache.db')
                                cursor = conn.cursor()
                                cursor.execute("SELECT COUNT(*) FROM api_poems")
                                cache_count = cursor.fetchone()[0]

                                cursor.execute("SELECT poet, COUNT(*) FROM api_poems GROUP BY poet")
                                poet_counts = cursor.fetchall()
                                conn.close()
                            except:
                                cache_count = 0
                                poet_counts = []

                            total_users = len(user_modes)
                            online_users = sum(1 for mode in user_modes.values() if mode == "online")

                            stats_msg = f"""<b>📊 آمار کلی ربات</b>

<b>👥 کاربران:</b>
• کاربران فعال: {total_users}
• حالت آنلاین: {online_users}
• حالت آفلاین: {total_users - online_users}

<b>💾 ذخیره:</b>
• کل اشعار کش شده: {cache_count}"""

                            if poet_counts:
                                stats_msg += "\n\n<b>اشعار کش شده:</b>"
                                for poet, count in poet_counts:
                                    name = {"hafez": "حافظ", "saadi": "سعدی", "molana": "مولانا"}.get(poet, poet)
                                    stats_msg += f"\n• {name}: {count}"

                            stats_msg += f"\n\n<b>🔄 وضعیت:</b> ✅ فعال"
                            stats_msg += f"\n<b>🆔 شناسه شما:</b> <code>{chat_id}</code>"

                            send_message(chat_id, stats_msg, get_stats_keyboard())

                        elif user_text == "📞 درباره ما":
                            about_us = """<b>📞 درباره ما</b>

<b>👨‍💻 توسعه‌دهنده:</b>
فرزاد قجری

<b>📱 تماس:</b>
09302446141

<b>📧 ایمیل:</b>
farzadghajari707@gmail.com

<b>🎯 خدمات:</b>
• ساخت انواع ربات تلگرام
• طراحی وب‌سایت
• برنامه‌نویسی سفارشی
• پشتیبانی مادام‌العمر

<b>✨ ربات شعر فارسی:</b>
• دارای هزاران شعر از شاعران بزرگ
• دو حالت آنلاین/آفلاین
• رابط کاربری ساده و زیبا
• پاسخگویی سریع

<b>💌 برای سفارش پروژه:</b>
لطفاً از طریق شماره یا ایمیل بالا تماس بگیرید.

<i>با ❤️ برای علاقه‌مندان شعر فارسی</i>"""

                            send_message(chat_id, about_us)

                        else:
                            send_message(chat_id, "🤔 دستور نامعتبر!\n\nلطفاً از دکمه‌های پایین استفاده کنید.")

            else:
                time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ خطا: {e}")
            time.sleep(1)


# --- اجرای برنامه ---
if __name__ == "__main__":
    # شروع سرور وب
    keep_alive()

    # کمی صبر برای راه‌اندازی
    time.sleep(2)

    # شروع ربات
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 ربات متوقف شد")
    except Exception as e:
        print(f"❌ خطا: {e}")