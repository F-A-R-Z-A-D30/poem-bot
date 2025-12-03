from flask import Flask
from threading import Thread
import requests
import time
import random
import sqlite3
import os
import sys

# ==========================================
TOKEN = "1613886570:03yF4qFiCCT3p8AhkplRwCIKeXCZi_BY9aM"
# ==========================================

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# --- سرور Flask ---
app = Flask(__name__)


@app.route('/')
def home():
    return "🤖 ربات شعر فارسی API"


@app.route('/ping')
def ping():
    return "pong"


@app.route('/status')
def status():
    return {
        "status": "active",
        "service": "poetry-api-bot",
        "developer": "فرزاد قجری",
        "contact": "09302446141"
    }


def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


def keep_alive():
    server = Thread(target=run_server, daemon=True)
    server.start()
    print(f"✅ سرور فعال روی پورت {os.environ.get('PORT', 8080)}")


# --- API Manager ---
class APIPoemManager:
    def __init__(self):
        print("🌐 مدیر API در حال راه‌اندازی...")
        self.api_urls = [
            "https://api.ganjgah.ir/api/v1/poem/random",
            "https://api.ganjoor.net/api/ganjoor/poem/random"
        ]

        self.poets_map = {
            "hafez": "حافظ",
            "saadi": "سعدی",
            "molana": "مولانا"
        }

        self._init_database()

    def _init_database(self):
        """دیتابیس برای کش اشعار"""
        try:
            self.conn = sqlite3.connect('poetry_cache.db', check_same_thread=False)
            cursor = self.conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS poem_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poet TEXT,
                    verse1 TEXT,
                    verse2 TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    request_count INTEGER DEFAULT 0
                )
            ''')

            self.conn.commit()
            print("✅ دیتابیس راه‌اندازی شد")
        except Exception as e:
            print(f"⚠️ خطا در دیتابیس: {e}")
            self.conn = None

    def _fetch_from_api(self, poet_key):
        """گرفتن شعر از API"""
        poet_persian = self.poets_map.get(poet_key)
        if not poet_persian:
            return None

        # اول گنجگاه
        try:
            response = requests.get(
                self.api_urls[0],
                params={"poet": poet_persian},
                timeout=2
            )

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    poem_data = data[0]
                    poem_text = poem_data.get('poem', '')

                    lines = []
                    for line in poem_text.split('\n'):
                        line = line.strip()
                        if line and len(line) > 5:
                            lines.append(line)

                    if len(lines) >= 2:
                        return {
                            'verse1': lines[0],
                            'verse2': lines[1],
                            'source': 'ganjgah'
                        }
                    elif lines:
                        return {
                            'verse1': lines[0],
                            'verse2': '',
                            'source': 'ganjgah'
                        }
        except:
            pass

        # اگر گنجگاه نشد، گنجور
        try:
            ganjoor_map = {"hafez": 1, "saadi": 2, "molana": 3}
            if poet_key not in ganjoor_map:
                return None

            response = requests.get(
                self.api_urls[1],
                params={"poetId": ganjoor_map[poet_key]},
                timeout=2
            )

            if response.status_code == 200:
                data = response.json()
                if data:
                    verses = data.get('verses', [])
                    if len(verses) >= 2:
                        v1 = verses[0].get('text', '').strip()
                        v2 = verses[1].get('text', '').strip()

                        if v1 and v2:
                            return {
                                'verse1': v1,
                                'verse2': v2,
                                'source': 'ganjoor'
                            }
        except:
            pass

        return None

    def _save_to_cache(self, poet, verse1, verse2, source):
        """ذخیره در کش"""
        if not self.conn or not verse1:
            return

        try:
            cursor = self.conn.cursor()

            cursor.execute('''
                DELETE FROM poem_cache 
                WHERE id IN (
                    SELECT id FROM poem_cache 
                    WHERE poet = ? 
                    ORDER BY created_at DESC 
                    LIMIT -1 OFFSET 30
                )
            ''', (poet,))

            cursor.execute('''
                INSERT INTO poem_cache (poet, verse1, verse2, source)
                VALUES (?, ?, ?, ?)
            ''', (poet, verse1, verse2, source))

            self.conn.commit()
        except:
            pass

    def _get_from_cache(self, poet):
        """گرفتن از کش"""
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT verse1, verse2, source 
                FROM poem_cache 
                WHERE poet = ? 
                ORDER BY RANDOM() 
                LIMIT 1
            ''', (poet,))

            result = cursor.fetchone()
            if result:
                return {
                    'verse1': result[0],
                    'verse2': result[1],
                    'source': f"کش ({result[2]})"
                }
        except:
            pass

        return None

    def _update_user_stats(self, user_id):
        """آپدیت آمار کاربر"""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id) VALUES (?)
            ''', (user_id,))

            cursor.execute('''
                UPDATE users SET request_count = request_count + 1 
                WHERE user_id = ?
            ''', (user_id,))

            self.conn.commit()
        except:
            pass

    def get_poem(self, poet_key, user_id=None):
        """دریافت شعر"""
        if poet_key not in self.poets_map:
            return {
                'success': False,
                'poem': f"شاعر '{poet_key}' پشتیبانی نمی‌شود."
            }

        # اول از کش بگیر
        cached = self._get_from_cache(poet_key)
        if cached:
            if user_id:
                self._update_user_stats(user_id)
            return {
                'success': True,
                'poem': f"{cached['verse1']}\n{cached['verse2']}".strip(),
                'source': cached['source']
            }

        # از API بگیر
        result = self._fetch_from_api(poet_key)

        if result:
            # ذخیره در کش
            self._save_to_cache(
                poet_key,
                result['verse1'],
                result['verse2'],
                result['source']
            )

            # آپدیت آمار
            if user_id:
                self._update_user_stats(user_id)

            poem_text = f"{result['verse1']}"
            if result['verse2']:
                poem_text += f"\n{result['verse2']}"

            return {
                'success': True,
                'poem': poem_text,
                'source': result['source']
            }

        # اگر هیچ کدام کار نکرد
        if user_id:
            self._update_user_stats(user_id)

        # پیام خطا
        error_messages = [
            "در حال حاضر دسترسی به منابع شعر ممکن نیست. لطفاً چند لحظه دیگر تلاش کنید.",
            "شعرها در خواب زیبا هستند... کمی بعد دوباره امتحان کنید.",
            "اتصال به سرور با مشکل مواجه شد. لطفاً دوباره تلاش کنید."
        ]

        return {
            'success': False,
            'poem': random.choice(error_messages),
            'source': 'خطا'
        }

    def get_stats(self, user_id=None):
        """دریافت آمار"""
        if not self.conn:
            return {}

        try:
            cursor = self.conn.cursor()

            stats = {}

            # آمار کلی
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(request_count) FROM users")
            stats['total_requests'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM poem_cache")
            stats['cached_poems'] = cursor.fetchone()[0] or 0

            # آمار کاربر
            if user_id:
                cursor.execute("SELECT request_count FROM users WHERE user_id = ?", (user_id,))
                user_data = cursor.fetchone()
                stats['user_requests'] = user_data[0] if user_data else 0

            return stats

        except:
            return {}


# --- مقداردهی ---
manager = APIPoemManager()


# --- توابع ربات ---
def send_message(chat_id, text, keyboard_type="main"):
    """ارسال پیام"""

    keyboards = {
        "main": {
            "keyboard": [
                [{"text": "📖 فال حافظ"}, {"text": "🌿 پند سعدی"}],
                [{"text": "🔥 اشعار مولانا"}, {"text": "🎲 شعر تصادفی"}],
                [{"text": "📊 آمار ربات"}, {"text": "📞 درباره ما"}]
            ],
            "resize_keyboard": True
        },
        "back": {
            "keyboard": [
                [{"text": "🔙 برگشت"}]
            ],
            "resize_keyboard": True
        }
    }

    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboards.get(keyboard_type, keyboards["main"]),
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False


def get_updates(offset=0):
    """دریافت آپدیت‌ها"""
    try:
        url = f"{BASE_URL}/getUpdates"
        params = {
            "offset": offset,
            "timeout": 30,
            "limit": 100
        }
        response = requests.get(url, params=params, timeout=35)
        return response.json() if response.status_code == 200 else None
    except:
        return None


# --- تابع اصلی ---
def main():
    print("🤖 ربات شعر فارسی در حال راه‌اندازی...")
    keep_alive()
    time.sleep(3)

    print("✅ ربات آماده است!")
    print("👤 توسعه‌دهنده: فرزاد قجری")

    last_update_id = 0

    while True:
        try:
            updates = get_updates(last_update_id + 1)

            if updates and updates.get("ok"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]

                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_text = update["message"]["text"].strip()

                        if user_text in ["/start", "🔙 برگشت"]:
                            welcome = """<b>🌹 به ربات شعر فارسی خوش آمدید!</b>

📚 <b>من می‌توانم زیباترین شعرها را برای شما بخوانم:</b>

• 📖 <b>فال حافظ</b> - غزلیات عرفانی
• 🌿 <b>پند سعدی</b> - حکمت‌های اخلاقی  
• 🔥 <b>اشعار مولانا</b> - اشعار عاشقانه
• 🎲 <b>شعر تصادفی</b> - سورپرایز شعر

✨ <b>ویژگی‌ها:</b>
• دریافت زنده از منابع معتبر
• کش هوشمند برای سرعت بیشتر
• رابط کاربری آسان

<i>لطفاً انتخاب کنید:</i>"""

                            send_message(chat_id, welcome)

                        elif user_text == "📖 فال حافظ":
                            result = manager.get_poem("hafez", chat_id)

                            if result['success']:
                                response = f"<b>📖 فال حافظ</b>\n\n{result['poem']}\n\n<i>با نیت خیر و دل پاک...</i>"
                            else:
                                response = f"<b>⚠️ خطا در دریافت شعر</b>\n\n{result['poem']}"

                            send_message(chat_id, response, "back")

                        elif user_text == "🌿 پند سعدی":
                            result = manager.get_poem("saadi", chat_id)

                            if result['success']:
                                response = f"<b>🌿 پند سعدی</b>\n\n{result['poem']}\n\n<i>از گلستان و بوستان سعدی</i>"
                            else:
                                response = f"<b>⚠️ خطا در دریافت شعر</b>\n\n{result['poem']}"

                            send_message(chat_id, response, "back")

                        elif user_text == "🔥 اشعار مولانا":
                            result = manager.get_poem("molana", chat_id)

                            if result['success']:
                                response = f"<b>🔥 مولانا جلال‌الدین رومی</b>\n\n{result['poem']}\n\n<i>مثنوی معنوی</i>"
                            else:
                                response = f"<b>⚠️ خطا در دریافت شعر</b>\n\n{result['poem']}"

                            send_message(chat_id, response, "back")

                        elif user_text == "🎲 شعر تصادفی":
                            poets = ["hafez", "saadi", "molana"]
                            poet = random.choice(poets)
                            poet_names = {"hafez": "حافظ", "saadi": "سعدی", "molana": "مولانا"}

                            result = manager.get_poem(poet, chat_id)

                            if result['success']:
                                response = f"<b>🎲 از دیوان {poet_names[poet]}</b>\n\n{result['poem']}"
                            else:
                                response = f"<b>⚠️ خطا در دریافت شعر</b>\n\n{result['poem']}"

                            send_message(chat_id, response, "back")

                        elif user_text == "📊 آمار ربات":
                            stats = manager.get_stats(chat_id)

                            stats_text = f"""<b>📊 آمار ربات</b>

<b>📈 آمار کلی:</b>
👥 کاربران: {stats.get('total_users', 0)}
📨 درخواست‌ها: {stats.get('total_requests', 0)}
🗄️ شعرهای ذخیره شده: {stats.get('cached_poems', 0)}

<b>📊 آمار شما:</b>
📊 درخواست‌های شما: {stats.get('user_requests', 0)}

<code>🆔 شناسه شما: {chat_id}</code>"""

                            send_message(chat_id, stats_text, "back")

                        elif user_text == "📞 درباره ما":
                            about_us = """<b>📞 درباره ما</b>

<b>👨‍💻 توسعه‌دهنده:</b>
<code>فرزاد قجری</code>

<b>📱 تماس مستقیم:</b>
<code>09302446141</code>

<b>📧 ایمیل:</b>
<code>farzadghajari707@gmail.com</code>

<b>🎯 خدمات تخصصی:</b>
✅ ساخت انواع ربات تلگرام
✅ طراحی وب‌سایت و اپلیکیشن
✅ برنامه‌نویسی پایتون و Django
✅ پایگاه داده و API
✅ پشتیبانی مادام‌العمر

<b>✨ این ربات:</b>
• دریافت شعر از منابع معتبر فارسی
• سیستم کش هوشمند
• رابط کاربری فارسی
• آمارگیری پیشرفته

<b>💼 برای سفارش پروژه:</b>
لطفاً از طریق شماره تماس یا ایمیل فوق ارتباط برقرار کنید.

<b>🕒 پاسخگویی:</b>
همه‌روزه از ساعت ۹ صبح تا ۱۲ شب

<i>با افتخار در خدمت جامعه برنامه‌نویسی ایران 🇮🇷</i>

<code>#برنامه‌نویس_پایتون #ربات_تلگرام #شعر_فارسی</code>"""

                            send_message(chat_id, about_us, "back")

                        else:
                            send_message(chat_id, "لطفاً از دکمه‌های پایین استفاده کنید 👇")

            time.sleep(0.1)

        except Exception as e:
            print(f"⚠️ خطا در پردازش: {e}")
            time.sleep(5)


# --- اجرا ---
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 ربات متوقف شد")
    except Exception as e:
        print(f"❌ خطای اصلی: {e}")