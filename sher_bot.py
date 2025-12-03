from flask import Flask
from threading import Thread
import requests
import time
import random
import data  # این همون فایل شعرهای توست

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


# --- بخش ۲: منطق ربات شاعر ---
def get_updates(offset=0):
    try:
        url = f"{BASE_URL}/getUpdates"
        params = {"offset": offset, "timeout": 5}
        return requests.get(url, params=params).json()
    except:
        return None


def send_message_with_keyboard(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    keyboard = {
        "keyboard": [
            [{"text": "📖 فال حافظ"}, {"text": "🌿 پند سعدی"}],
            [{"text": "🔥 شور مولانا"}, {"text": "🎲 یک بیت شانسی"}],
            [{"text": "📞 درباره ما"}]
        ],
        "resize_keyboard": True
    }
    payload = {"chat_id": chat_id, "text": text, "reply_markup": keyboard}
    try:
        requests.post(url, json=payload)
    except:
        pass


def main():
    print("✅ ربات شاعر روی سرور روشن شد!")
    last_update_id = 0

    while True:
        updates = get_updates(last_update_id + 1)
        if updates and updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                last_update_id = update["update_id"]

                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_text = update["message"]["text"]

                    if user_text == "/start":
                        send_message_with_keyboard(chat_id, "سلام! به ربات شعر خوش اومدی 🌹")

                    elif user_text == "📖 فال حافظ":
                        poem = random.choice(data.POEMS["hafez"])
                        send_message_with_keyboard(chat_id, f"📖 **حافظ:**\n\n{poem}")

                    elif user_text == "🌿 پند سعدی":
                        poem = random.choice(data.POEMS["saadi"])
                        send_message_with_keyboard(chat_id, f"🌿 **سعدی:**\n\n{poem}")

                    elif user_text == "🔥 شور مولانا":
                        poem = random.choice(data.POEMS["molana"])
                        send_message_with_keyboard(chat_id, f"🔥 **مولانا:**\n\n{poem}")

                    elif user_text == "🎲 یک بیت شانسی":
                        all_poems = data.POEMS["hafez"] + data.POEMS["saadi"] + data.POEMS["molana"]
                        poem = random.choice(all_poems)
                        send_message_with_keyboard(chat_id, f"🎲 **شانسی:**\n\n{poem}")

                    elif user_text == "📞 درباره ما":
                        send_message_with_keyboard(chat_id, "طراحی شده با ❤️ روی سرور ابری.")

                    else:
                        send_message_with_keyboard(chat_id, "لطفاً دکمه‌ها را انتخاب کنید 👇")

        time.sleep(1)  # خیلی مهم برای جلوگیری از فشار به سرور


if __name__ == "__main__":
    keep_alive()  # اول سرور قلابی روشن میشه
    main()  # بعد ربات اصلی