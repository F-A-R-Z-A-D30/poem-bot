from flask import Flask
from threading import Thread
import requests
import time
import random
import data  # فایل شعرهای محلی تو
import sqlite3
from datetime import datetime

# ==========================================
TOKEN = "1613886570:03yF4qFiCCT3p8AhkplRwCIKeXCZi_BY9aM"
# ==========================================

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# --- بخش ۱: سرور برای بیدار ماندن (Flask) ---
app = Flask('')


@app.route('/')
def home():
    return "Poetry Bot is Alive! 📖"


def run_http():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run_http)
    t.start()


# --- بخش ۲: مدیر API و داده‌های محلی ---
class SmartPoemManager:
    def __init__(self):
        # داده‌های محلی اصلی (همون data.POEMS)
        self.local_poems = {
            "hafez": data.POEMS["hafez"] if hasattr(data, 'POEMS') and "hafez" in data.POEMS else [],
            "saadi": data.POEMS["saadi"] if hasattr(data, 'POEMS') and "saadi" in data.POEMS else [],
            "molana": data.POEMS["molana"] if hasattr(data, 'POEMS') and "molana" in data.POEMS else []
        }

        # APIها
        self.apis = [
            self._try_api_ganjgah,  # اولویت اول
            self._try_api_ganjoor,  # اولویت دوم
        ]

        # تنظیمات
        self.use_api = True  # می‌تونی غیرفعال کنی
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
                    verse TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            print("✅ کش API راه‌اندازی شد")
        except:
            print("⚠️ خطا در راه‌اندازی کش")

    def _try_api_ganjgah(self, poet):
        """API گنجگاه"""
        try:
            poets_map = {
                "hafez": "حافظ",
                "saadi": "سعدی",
                "molana": "مولانا"
            }

            if poet not in poets_map:
                return None

            response = requests.get(
                "https://api.ganjgah.ir/api/v1/poem/random",
                params={"poet": poets_map[poet]},
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    poem_data = data[0]
                    poem_text = poem_data.get('poem', '')
                    lines = poem_text.strip().split('\n')

                    if len(lines) >= 2:
                        poem = f"{lines[0]} --- {lines[1]}"
                    elif len(lines) == 1:
                        poem = lines[0]
                    else:
                        poem = poem_text

                    # ذخیره در کش
                    self._save_to_cache(poet, poem, "ganjgah")
                    return poem
        except Exception as e:
            print(f"خطا در API گنجگاه: {e}")
        return None

    def _try_api_ganjoor(self, poet):
        """API گنجور"""
        try:
            poets_id = {
                "hafez": 1,
                "saadi": 2,
                "molana": 3
            }

            if poet not in poets_id:
                return None

            response = requests.get(
                f"https://api.ganjoor.net/api/ganjoor/poem/random?poetId={poets_id[poet]}",
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                if data:
                    # استخراج متن شعر
                    verses = data.get('verses', [])
                    if len(verses) >= 2:
                        v1 = verses[0].get('text', '').strip()
                        v2 = verses[1].get('text', '').strip()
                        poem = f"{v1} --- {v2}"
                    elif len(verses) == 1:
                        poem = verses[0].get('text', '').strip()
                    else:
                        poem = data.get('fullTitle', '') or data.get('plainText', '')

                    if poem:
                        self._save_to_cache(poet, poem, "ganjoor")
                        return poem
        except Exception as e:
            print(f"خطا در API گنجور: {e}")
        return None

    def _save_to_cache(self, poet, poem, source):
        """ذخیره شعر API در کش"""
        if not self.cache_enabled or not poem:
            return

        try:
            conn = sqlite3.connect('api_poems_cache.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO api_poems (poet, verse, source) VALUES (?, ?, ?)",
                (poet, poem, source)
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
                "SELECT verse FROM api_poems WHERE poet = ? ORDER BY RANDOM() LIMIT 1",
                (poet,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except:
            return None

    def get_poem(self, poet, use_api=True):
        """
        دریافت شعر با ترتیب هوشمند:
        1. اگر API فعال بود، سعی کن از API بگیر
        2. اگر API موفق نبود، از کش بگیر
        3. اگر کش هم خالی بود، از داده‌های محلی بگیر
        """
        poem = None

        # 1. استفاده از API
        if use_api and self.use_api:
            for api_func in self.apis:
                poem = api_func(poet)
                if poem:
                    return {"source": "api", "poem": poem}

            # 2. اگر API جواب نداد، از کش بگیر
            cached_poem = self._get_from_cache(poet)
            if cached_poem:
                return {"source": "cache", "poem": cached_poem}

        # 3. در نهایت از داده‌های محلی
        if poet in self.local_poems and self.local_poems[poet]:
            poem = random.choice(self.local_poems[poet])
            return {"source": "local", "poem": poem}

        # 4. اگر هیچ کدام نبود
        return {"source": "error", "poem": "شعری یافت نشد."}


# --- بخش ۳: منطق ربات (بدون تغییر زیاد) ---
poem_manager = SmartPoemManager()


def send_message_with_keyboard(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    keyboard = {
        "keyboard": [
            [{"text": "📖 فال حافظ"}, {"text": "🌿 پند سعدی"}],
            [{"text": "🔥 شور مولانا"}, {"text": "🎲 یک بیت شانسی"}],
            [{"text": "🔄 حالت آنلاین"}, {"text": "💾 حالت آفلاین"}],
            [{"text": "📊 آمار"}, {"text": "📞 درباره ما"}]
        ],
        "resize_keyboard": True
    }
    payload = {"chat_id": chat_id, "text": text, "reply_markup": keyboard}
    try:
        requests.post(url, json=payload)
    except:
        pass


def get_updates(offset=0):
    try:
        url = f"{BASE_URL}/getUpdates"
        params = {"offset": offset, "timeout": 5}
        return requests.get(url, params=params).json()
    except:
        return None


# متغیرهای حالت کاربران
user_modes = {}  # {chat_id: "online" or "offline"}


def main():
    print("✅ ربات شاعر ترکیبی (API + محلی) روشن شد!")
    last_update_id = 0

    while True:
        updates = get_updates(last_update_id + 1)
        if updates and updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                last_update_id = update["update_id"]

                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_text = update["message"]["text"]

                    # حالت پیش‌فرض کاربر
                    if chat_id not in user_modes:
                        user_modes[chat_id] = "online"  # پیش‌فرض آنلاین

                    current_mode = user_modes[chat_id]

                    if user_text == "/start":
                        welcome_msg = """سلام! به ربات شعر فارسی خوش آمدید 🌹

من می‌توانم شعرهای زیبای فارسی را برای شما بخوانم:
• 📖 فال حافظ (با تفسیر)
• 🌿 پند سعدی (حکمت آموز)
• 🔥 شور مولانا (عرفانی)
• 🎲 یک بیت شانسی (تصادفی)

💡 **حالت فعلی:** آنلاین (استفاده از API)
می‌توانید با دکمه‌های پایین حالت را تغییر دهید."""
                        send_message_with_keyboard(chat_id, welcome_msg)

                    elif user_text == "📖 فال حافظ":
                        use_api = (current_mode == "online")
                        result = poem_manager.get_poem("hafez", use_api)

                        source_emoji = "🌐" if result["source"] == "api" else "💾" if result[
                                                                                        "source"] == "local" else "🗄️"
                        mode_emoji = "🟢" if current_mode == "online" else "🔴"

                        message = f"{source_emoji} **فال حافظ** {mode_emoji}\n\n"
                        message += result["poem"]
                        message += f"\n\n📡 منبع: {result['source']} | حالت: {current_mode}"

                        send_message_with_keyboard(chat_id, message)

                    elif user_text == "🌿 پند سعدی":
                        use_api = (current_mode == "online")
                        result = poem_manager.get_poem("saadi", use_api)

                        source_emoji = "🌐" if result["source"] == "api" else "💾" if result[
                                                                                        "source"] == "local" else "🗄️"

                        message = f"{source_emoji} **پند سعدی**\n\n"
                        message += result["poem"]
                        message += f"\n\n📡 منبع: {result['source']} | حالت: {current_mode}"

                        send_message_with_keyboard(chat_id, message)

                    elif user_text == "🔥 شور مولانا":
                        use_api = (current_mode == "online")
                        result = poem_manager.get_poem("molana", use_api)

                        source_emoji = "🌐" if result["source"] == "api" else "💾" if result[
                                                                                        "source"] == "local" else "🗄️"

                        message = f"{source_emoji} **مولانا**\n\n"
                        message += result["poem"]
                        message += f"\n\n📡 منبع: {result['source']} | حالت: {current_mode}"

                        send_message_with_keyboard(chat_id, message)

                    elif user_text == "🎲 یک بیت شانسی":
                        poets = ["hafez", "saadi", "molana"]
                        poet = random.choice(poets)
                        poet_names = {"hafez": "حافظ", "saadi": "سعدی", "molana": "مولانا"}

                        use_api = (current_mode == "online")
                        result = poem_manager.get_poem(poet, use_api)

                        source_emoji = "🌐" if result["source"] == "api" else "💾" if result[
                                                                                        "source"] == "local" else "🗄️"

                        message = f"{source_emoji} **از دیوان {poet_names[poet]}** 🎲\n\n"
                        message += result["poem"]
                        message += f"\n\n📡 منبع: {result['source']} | حالت: {current_mode}"

                        send_message_with_keyboard(chat_id, message)

                    elif user_text == "🔄 حالت آنلاین":
                        user_modes[chat_id] = "online"
                        send_message_with_keyboard(chat_id,
                                                   "✅ **حالت آنلاین فعال شد!**\n\nاکنون از APIهای اینترنتی برای دریافت شعرهای جدید استفاده می‌شود.")

                    elif user_text == "💾 حالت آفلاین":
                        user_modes[chat_id] = "offline"
                        send_message_with_keyboard(chat_id,
                                                   "📂 **حالت آفلاین فعال شد!**\n\nاکنون فقط از داده‌های محلی استفاده می‌شود.")

                    elif user_text == "📊 آمار":
                        try:
                            # آمار کش API
                            conn = sqlite3.connect('api_poems_cache.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM api_poems")
                            api_cache_count = cursor.fetchone()[0]
                            conn.close()
                        except:
                            api_cache_count = 0

                        # آمار داده‌های محلی
                        local_counts = {
                            "hafez": len(poem_manager.local_poems["hafez"]),
                            "saadi": len(poem_manager.local_poems["saadi"]),
                            "molana": len(poem_manager.local_poems["molana"])
                        }

                        stats_msg = f"""📊 **آمار ربات**

📁 **داده‌های محلی:**
• حافظ: {local_counts['hafez']} بیت
• سعدی: {local_counts['saadi']} بیت  
• مولانا: {local_counts['molana']} بیت

🗄️ **کش API:**
• اشعار ذخیره شده: {api_cache_count} بیت

⚙️ **تنظیمات:**
• حالت فعلی شما: {current_mode}
• API فعال: {'✅' if poem_manager.use_api else '❌'}
• کش فعال: {'✅' if poem_manager.cache_enabled else '❌'}

🆔 شناسه شما: {chat_id}"""

                        send_message_with_keyboard(chat_id, stats_msg)

                    elif user_text == "📞 درباره ما":
                        about_msg = """📖 **ربات شعر فارسی - نسخه ترکیبی**

✨ **ویژگی‌ها:**
• ترکیب داده‌های محلی و API
• دو حالت آنلاین/آفلاین
• کش‌گذاری خودکار
• پشتیبانی از حافظ، سعدی، مولانا

🔧 **منابع:**
• داده‌های محلی (از فایل data.py)
• API گنجگاه (ganjgah.ir)
• API گنجور (ganjoor.net)

🔄 **حالت‌ها:**
• آنلاین: دریافت شعرهای جدید از اینترنت
• آفلاین: فقط از داده‌های محلی

با ❤️ برای دوستداران شعر فارسی"""
                        send_message_with_keyboard(chat_id, about_msg)

                    else:
                        send_message_with_keyboard(chat_id, "لطفاً از دکمه‌های پایین استفاده کنید 👇")

        time.sleep(0.5)


if __name__ == "__main__":
    keep_alive()
    main()