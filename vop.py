import requests
import time
import random
import string
from colorama import Fore, Style, init

init(autoreset=True)

# === إعدادات Telegram ===
TELEGRAM_BOT_TOKEN = input("أدخل توكن البوت: ")
TELEGRAM_CHAT_ID = input("أدخل معرف الدردشة (Chat ID): ")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def check_username(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return "found"
        elif response.status_code == 200:
            return "taken"
        else:
            return "error"
    except:
        return "error"

def generate_random_5char():
    # حروف صغيرة + أرقام (مثل نمط hpovg)
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=5))

def main():
    count = int(input("كم عدد اليوزرات العشوائية تريد فحصها؟: "))
    delay = float(input("وقت الانتظار بين الطلبات بالثواني (مثلاً 0.5): "))

    print(f"\n--- فحص {count} يوزر عشوائي خماسي ---\n")
    send_telegram_message(f"✅ بدء الفحص لـ {count} يوزر عشوائي خماسي")

    found_list = []

    for idx in range(1, count + 1):
        user = generate_random_5char()
        status = check_username(user)
        if status == "found":
            msg = f"{idx}. {user} -> found"
            print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")
            send_telegram_message(f"🟢 {msg}")
            found_list.append(user)
        elif status == "taken":
            msg = f"{idx}. {user} -> taken"
            print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
        else:
            msg = f"{idx}. {user} -> error"
            print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")
        time.sleep(delay)

    send_telegram_message(f"🏁 انتهى الفحص. تم العثور على {len(found_list)} يوزر متاح: {', '.join(found_list) if found_list else 'لا شيء'}")

if __name__ == "__main__":
    main()