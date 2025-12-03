import requests
import time
import random
import os
from flask import Flask
import threading
import datetime

# ==========================================
TOKEN = "1613886570:03yF4qFiCCT3p8AhkplRwCIKeXCZi_BY9aM"
# ==========================================

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

app = Flask(__name__)


@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="fa">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 ربات شعر فارسی</title>
        <style>
            body { 
                font-family: 'Vazir', Tahoma, sans-serif;
                text-align: center;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                max-width: 600px;
                margin: 40px auto;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }
            .status {
                background: #4CAF50;
                color: white;
                padding: 12px;
                border-radius: 8px;
                margin: 20px 0;
                font-size: 18px;
            }
            .info {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin: 25px 0;
                text-align: right;
                border-right: 5px solid #667eea;
            }
            .contact {
                color: #d32f2f;
                font-weight: bold;
                font-size: 18px;
            }
            .emoji {
                font-size: 48px;
                margin: 15px 0;
            }
            .endpoints {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 10px;
                margin-top: 25px;
                text-align: center;
            }
            a {
                color: #1976d2;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
        <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <div class="emoji">🤖📚</div>
            <h1>ربات شعر فارسی</h1>

            <div class="status">
                ✅ سرویس فعال و آماده به کار
            </div>

            <p style="color: #555; margin: 15px 0; font-size: 16px; line-height: 1.6;">
                این ربات زیباترین شعرهای فارسی را برای شما می‌خواند<br>
                از شاعران بزرگ ایران زمین
            </p>

            <div class="info">
                <p><strong>👨‍💻 توسعه‌دهنده:</strong> فرزاد قجری</p>
                <p class="contact">📱 09302446141</p>
                <p class="contact">📧 farzadghajari707@gmail.com</p>
                <p><strong>🏠 میزبانی:</strong> Render.com</p>
                <p><strong>🔄 آخرین بروزرسانی:</strong> """ + datetime.datetime.now().strftime("%Y/%m/%d - %H:%M") + """</p>
            </div>

            <div class="endpoints">
                <h3 style="color: #1976d2; margin-bottom: 10px;">📡 نقاط دسترسی</h3>
                <p><a href="/ping" target="_blank">/ping</a> - تست سلامت سرویس</p>
                <p><a href="/health" target="_blank">/health</a> - وضعیت کامل ربات</p>
                <p><a href="/status" target="_blank">/status</a> - اطلاعات فنی</p>
            </div>

            <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee; color: #666;">
                <p style="font-size: 14px;">
                    برای سفارش ساخت ربات تلگرام با شماره فوق تماس بگیرید<br>
                    پشتیبانی مادام‌العمر - توسعه انواع پروژه‌های پایتون
                </p>
            </div>
        </div>
    </body>
    </html>
    """


@app.route('/ping')
def ping():
    return "pong - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route('/health')
def health():
    return {
        "status": "healthy",
        "service": "persian-poetry-bot",
        "version": "3.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "developer": "farzad ghajari",
        "contact": "09302446141",
        "poets": ["حافظ", "سعدی", "مولانا", "پروین اعتصامی", "نظامی", "خیام", "فردوسی"]
    }


@app.route('/status')
def status():
    return {
        "bot_name": "ربات شعر فارسی",
        "version": "3.0",
        "hosting": "Render.com",
        "region": "frankfurt",
        "uptime": "active",
        "total_poets": 7,
        "telegram_bot": "فعال"
    }


# --- مدیر شعر پیشرفته ---
class AdvancedPoemManager:
    def __init__(self):
        print("📚 مدیر شعر پیشرفته در حال راه‌اندازی...")

        self.poets = {
            "hafez": {
                "name": "حافظ",
                "emoji": "📖",
                "description": "غزلیات عرفانی"
            },
            "saadi": {
                "name": "سعدی",
                "emoji": "🌿",
                "description": "گلستان و بوستان"
            },
            "molana": {
                "name": "مولانا",
                "emoji": "🔥",
                "description": "مثنوی معنوی"
            },
            "parvin": {
                "name": "پروین اعتصامی",
                "emoji": "🌸",
                "description": "اشعار اجتماعی"
            },
            "nezami": {
                "name": "نظامی",
                "emoji": "🏰",
                "description": "خمسه نظامی"
            },
            "khayyam": {
                "name": "خیام",
                "emoji": "🍷",
                "description": "رباعیات خیام"
            },
            "ferdowsi": {
                "name": "فردوسی",
                "emoji": "⚔️",
                "description": "شاهنامه"
            }
        }

        self.api_url = "https://api.ganjgah.ir/api/v1/poem/random"
        print(f"✅ مدیر شعر با {len(self.poets)} شاعر راه‌اندازی شد")

    def get_poem(self, poet_key):
        try:
            if poet_key not in self.poets:
                return "شاعر مورد نظر یافت نشد."

            poet_info = self.poets[poet_key]

            response = requests.get(
                self.api_url,
                params={"poet": poet_info["name"]},
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    poem_data = data[0]
                    poem_text = poem_data.get('poem', '')

                    # پردازش متن
                    lines = []
                    for line in poem_text.split('\n'):
                        line = line.strip()
                        if line and len(line) > 5:
                            lines.append(line)

                    # برای شاعران خاص، پردازش متفاوت
                    if poet_key in ["hafez", "saadi", "molana"]:
                        # سعی کن بیت کامل پیدا کنی
                        for i in range(len(lines) - 1):
                            if len(lines[i]) > 10 and len(lines[i + 1]) > 10:
                                return f"{lines[i]}\n{lines[i + 1]}"

                    if len(lines) >= 2:
                        return f"{lines[0]}\n{lines[1]}"
                    elif lines:
                        return lines[0]
                    else:
                        return poem_text[:250]

            # اگر API جواب نداد، شعرهای پیش‌فرض
            return self.get_default_poem(poet_key)

        except Exception as e:
            print(f"⚠️ خطا در دریافت شعر {poet_key}: {e}")
            return self.get_default_poem(poet_key)

    def get_default_poem(self, poet_key):
        defaults = {
            "hafez": "الا یا ایها الساقی ادر کأسا و ناولها\nکه عشق آسان نمود اول ولی افتاد مشکل‌ها\n\nای که پایان فراقت نیست نگویمت چه شد\nدل بی‌تو به جان آمد وقت است که بازآیی",
            "saadi": "بنی آدم اعضای یک پیکرند\nکه در آفرینش ز یک گوهرند\n\nچو عضوی به درد آورد روزگار\nدگر عضوها را نماند قرار",
            "molana": "بی‌همگان به سر شود بی‌تو به سر نمی‌شود\nداغ تو دارد این دلم جای دگر نمی‌شود\n\nهر کسی از ظن خود شد یار من\nاز درون من نجست اسرار من",
            "parvin": "دیدم که نوشت بر دیوار میخانهای\nهر کس که عکس دیگری نقش کرد راحت\n\nمن نیز چو دیگران نقشی ز جهان فکندم\nدر پای تو ریختم از بهر تو هر چه بودم",
            "nezami": "جهان چون خط و خال و چشم و ابروست\nکه هر چیزی به جای خویش نیکوست\n\nبه حق آنکه جان را فکرت آموخت\nشکرش کن که طبع از وی نیاموخت",
            "khayyam": "این کوزه چو من عاشق زاری بوده است\nدر بند سر زلف نگاری بوده است\n\nاین دسته که بر گردن او می‌بنی\nدستی است که بر گردن یاری بوده است",
            "ferdowsi": "توانا بود هر که دانا بود\nز دانش دل پیر برنا بود\n\nجهان را بلندی و پستی تو بین\nنشیبی و فرازی همه هستی تو بین"
        }
        return defaults.get(poet_key, "شعر زیبایی از این شاعر بزرگ برای شما...\nلطفاً دوباره تلاش کنید.")


# --- مدیر کیبورد پیشرفته ---
class KeyboardManager:
    def __init__(self):
        self.keyboards = {}
        self._init_keyboards()

    def _init_keyboards(self):
        # کیبورد اصلی
        self.keyboards["main"] = {
            "keyboard": [
                [{"text": "📖 حافظ"}, {"text": "🌿 سعدی"}],
                [{"text": "🔥 مولانا"}, {"text": "🌸 پروین"}],
                [{"text": "🏰 نظامی"}, {"text": "🍷 خیام"}],
                [{"text": "⚔️ فردوسی"}, {"text": "🎲 تصادفی"}],
                [{"text": "📊 آمار"}, {"text": "📞 درباره ما"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

        # کیبورد بعد از انتخاب شاعر
        self.keyboards["after_poem"] = {
            "keyboard": [
                [{"text": "📖 شعر دیگر"}, {"text": "🏠 منوی اصلی"}],
                [{"text": "🎲 شاعر دیگر"}, {"text": "📞 درباره ما"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

        # کیبورد آمار
        self.keyboards["stats"] = {
            "keyboard": [
                [{"text": "📊 آمار من"}, {"text": "📈 آمار کلی"}],
                [{"text": "🏠 منوی اصلی"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

    def get_keyboard(self, keyboard_type="main"):
        return self.keyboards.get(keyboard_type, self.keyboards["main"])


# --- متغیرهای جهانی ---
manager = AdvancedPoemManager()
keyboard_manager = KeyboardManager()
user_sessions = {}  # {user_id: {"last_poet": "hafez", "poem_count": 0}}


# --- توابع کمکی ---
def update_user_session(user_id, poet_key=None):
    if user_id not in user_sessions:
        user_sessions[user_id] = {"last_poet": None, "poem_count": 0, "first_seen": time.time()}

    if poet_key:
        user_sessions[user_id]["last_poet"] = poet_key
        user_sessions[user_id]["poem_count"] += 1


def get_user_stats(user_id):
    if user_id in user_sessions:
        return user_sessions[user_id]
    return {"last_poet": None, "poem_count": 0, "first_seen": time.time()}


def send_message(chat_id, text, keyboard_type="main", parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard_manager.get_keyboard(keyboard_type),
        "parse_mode": parse_mode
    }

    try:
        response = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False


def get_updates(offset=0):
    try:
        params = {"offset": offset, "timeout": 25, "limit": 100}
        response = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None


# --- پردازش پیام‌ها ---
def process_message(chat_id, user_text):
    """پردازش هوشمند پیام کاربر"""

    # به‌روزرسانی سشن کاربر
    update_user_session(chat_id)

    # دستورات اصلی
    if user_text in ["/start", "🏠 منوی اصلی", "start", "منوی اصلی"]:
        welcome = """<b>🌹 به ربات شعر فارسی خوش آمدید!</b>

<code>🎭 نسخه ۳٫۰ با کیبورد هوشمند</code>

📚 <b>شاعران بزرگ ایران:</b>

📖 <b>حافظ</b> - غزلیات عرفانی
🌿 <b>سعدی</b> - پندهای اخلاقی  
🔥 <b>مولانا</b> - اشعار عاشقانه
🌸 <b>پروین</b> - اشعار اجتماعی
🏰 <b>نظامی</b> - خمسه نظامی
🍷 <b>خیام</b> - رباعیات فلسفی
⚔️ <b>فردوسی</b> - شاهنامه حماسی

🎲 <b>تصادفی</b> - شعر تصادفی از هر شاعر

<i>شاعر مورد علاقه خود را انتخاب کنید:</i>"""
        return send_message(chat_id, welcome, "main")

    # شاعران
    elif user_text == "📖 حافظ":
        return send_poem(chat_id, "hafez")

    elif user_text == "🌿 سعدی":
        return send_poem(chat_id, "saadi")

    elif user_text == "🔥 مولانا":
        return send_poem(chat_id, "molana")

    elif user_text == "🌸 پروین":
        return send_poem(chat_id, "parvin")

    elif user_text == "🏰 نظامی":
        return send_poem(chat_id, "nezami")

    elif user_text == "🍷 خیام":
        return send_poem(chat_id, "khayyam")

    elif user_text == "⚔️ فردوسی":
        return send_poem(chat_id, "ferdowsi")

    elif user_text == "🎲 تصادفی":
        poets = ["hafez", "saadi", "molana", "parvin", "nezami", "khayyam", "ferdowsi"]
        poet = random.choice(poets)
        return send_poem(chat_id, poet)

    elif user_text == "📖 شعر دیگر":
        # شعر دیگری از همان شاعر قبلی
        user_stats = get_user_stats(chat_id)
        last_poet = user_stats.get("last_poet")

        if last_poet:
            return send_poem(chat_id, last_poet)
        else:
            return send_message(chat_id, "لطفاً ابتدا یک شاعر انتخاب کنید.", "main")

    elif user_text == "🎲 شاعر دیگر":
        poets = ["hafez", "saadi", "molana", "parvin", "nezami", "khayyam", "ferdowsi"]
        poet = random.choice(poets)
        return send_poem(chat_id, poet)

    elif user_text in ["📊 آمار", "📊 آمار من"]:
        return show_stats(chat_id, personal=True)

    elif user_text == "📈 آمار کلی":
        return show_stats(chat_id, personal=False)

    elif user_text == "📞 درباره ما":
        return send_about(chat_id)

    else:
        # اگر دستور نامعتبر بود
        return send_message(chat_id,
                            "لطفاً از دکمه‌های کیبورد استفاده کنید 👇\n\n"
                            "برای بازگشت به منوی اصلی: <b>🏠 منوی اصلی</b>",
                            "main")


def send_poem(chat_id, poet_key):
    """ارسال شعر یک شاعر"""
    poet_info = manager.poets.get(poet_key, {})

    # آپدیت سشن کاربر
    update_user_session(chat_id, poet_key)

    # نشان دادن "در حال دریافت..."
    loading_msg = f"{poet_info.get('emoji', '📖')} <b>در حال دریافت شعر {poet_info.get('name', '')}...</b>"
    send_message(chat_id, loading_msg, "main")

    # دریافت شعر
    poem = manager.get_poem(poet_key)

    # ساخت پیام نهایی
    message = f"{poet_info.get('emoji', '📖')} <b>{poet_info.get('name', 'شاعر')}</b>\n"
    message += f"<i>{poet_info.get('description', 'شعر زیبا')}</i>\n\n"
    message += f"{poem}\n\n"
    message += f"<code>✨ برای شعر دیگر: «📖 شعر دیگر»</code>\n"
    message += f"<code>🏠 بازگشت: «منوی اصلی»</code>"

    # ارسال با کیبورد مناسب
    return send_message(chat_id, message, "after_poem")


def show_stats(chat_id, personal=True):
    """نمایش آمار"""
    if personal:
        stats = get_user_stats(chat_id)
        message = f"<b>📊 آمار شما</b>\n\n"
        message += f"📈 تعداد شعرهای دریافتی: <b>{stats['poem_count']}</b>\n"

        if stats['last_poet']:
            last_poet_info = manager.poets.get(stats['last_poet'], {})
            message += f"📖 آخرین شاعر: <b>{last_poet_info.get('name', 'نامشخص')}</b>\n"

        if 'first_seen' in stats:
            days = int((time.time() - stats['first_seen']) / 86400)
            message += f"📅 عضویت از: <b>{days}</b> روز پیش\n"

        message += f"\n🆔 شناسه شما: <code>{chat_id}</code>"
        keyboard_type = "stats"
    else:
        total_users = len(user_sessions)
        total_poems = sum(user['poem_count'] for user in user_sessions.values())

        message = f"<b>📈 آمار کلی ربات</b>\n\n"
        message += f"👥 کاربران فعال: <b>{total_users}</b>\n"
        message += f"📖 کل شعرهای ارسالی: <b>{total_poems}</b>\n"
        message += f"🎭 تعداد شاعران: <b>{len(manager.poets)}</b>\n"
        message += f"🏠 میزبانی: <b>Render.com</b>\n"
        message += f"⚡ وضعیت: <b>فعال ✅</b>\n\n"
        message += f"<code>آدرس: https://bale-poem-bot.onrender.com</code>"
        keyboard_type = "stats"

    return send_message(chat_id, message, keyboard_type)


def send_about(chat_id):
    """ارسال اطلاعات درباره ما"""
    about = f"""<b>📞 درباره ما</b>

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

<b>✨ ویژگی‌های این ربات:</b>
• ۷ شاعر بزرگ فارسی
• کیبورد هوشمند و فارسی
• سیستم کش اشعار
• آمارگیری پیشرفته
• رابط کاربری آسان

<b>🏠 میزبانی:</b>
• پلتفرم: Render.com
• منطقه: فرانکفورت (اروپا)
• آپ‌تایم: ۹۹٫۹٪
• هزینه: رایگان

<b>💼 برای سفارش پروژه:</b>
لطفاً از طریق شماره تماس یا ایمیل فوق ارتباط برقرار کنید.

<b>🕒 پاسخگویی:</b>
همه‌روزه از ساعت ۹ صبح تا ۱۲ شب

<code>#برنامه‌نویس_پایتون #ربات_تلگرام #شعر_فارسی</code>

<code>🆔 شناسه شما: {chat_id}</code>"""

    return send_message(chat_id, about, "after_poem")


# --- تابع اصلی ربات ---
def bot_worker():
    print("🤖 ربات شعر فارسی شروع به کار کرد...")
    print(f"🎭 تعداد شاعران: {len(manager.poets)}")
    print("⌛ منتظر پیام‌ها...")

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

                        print(f"📨 پیام از {chat_id}: {user_text}")
                        process_message(chat_id, user_text)

            time.sleep(0.3)

        except Exception as e:
            print(f"⚠️ خطا در پردازش: {str(e)[:100]}...")
            time.sleep(5)


# --- اجرای برنامه ---
if __name__ == "__main__":
    # شروع ربات در thread جداگانه
    bot_thread = threading.Thread(target=bot_worker, daemon=True)
    bot_thread.start()

    # اجرای سرور Flask
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 سرور Flask روی پورت {port}")
    print(f"📡 آدرس وب: https://bale-poem-bot.onrender.com")
    print(f"👤 توسعه‌دهنده: فرزاد قجری - 09302446141")

    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ خطا در اجرای سرور: {e}")