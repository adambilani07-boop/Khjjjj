import requests
import time
import random
import string
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    session = requests.Session()
    try:
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 404:
            return "found"
        elif response.status_code == 200:
            return "taken"
        else:
            return "error"
    except:
        return "error"
    finally:
        session.close()

def generate_random_5char():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=5))

def main():
    count = int(input("كم عدد اليوزرات العشوائية تريد فحصها؟: "))
    threads = int(input("عدد الخيوط المتوازية (مثلاً 5 - 10): "))
    delay = float(input("وقت التأخير بين كل دورة خيوط (بالثواني، مثلاً 0.3): "))

    print(f"\n--- فحص {count} يوزر عشوائي خماسي بقوة {threads} خيط متوازي ---\n")
    send_telegram_message(f"✅ بدء الفحص القوي لـ {count} يوزر عشوائي خماسي بـ {threads} خيط")

    found_list = []
    taken_list = []
    error_list = []
    processed = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {}
        for _ in range(count):
            user = generate_random_5char()
            futures[executor.submit(check_username, user)] = user

        for future in as_completed(futures):
            user = futures[future]
            status = future.result()
            processed += 1

            if status == "found":
                msg = f"{processed}. {user} -> found"
                print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")
                found_list.append(user)
                send_telegram_message(f"🟢 {msg}")
            elif status == "taken":
                msg = f"{processed}. {user} -> taken"
                print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
                taken_list.append(user)
            else:
                msg = f"{processed}. {user} -> error"
                print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")
                error_list.append(user)

            if processed % threads == 0:
                time.sleep(delay)

    # === إحصاءات نهائية ===
    total = len(found_list) + len(taken_list) + len(error_list)
    summary = (
        f"\n{'='*50}\n"
        f"📊 الإحصاء النهائي:\n"
        f"🟢 متاح (found): {len(found_list)}\n"
        f"🔴 مأخوذ (taken): {len(taken_list)}\n"
        f"🟡 خطأ (error): {len(error_list)}\n"
        f"📌 المجموع الكلي: {total}\n"
        f"{'='*50}"
    )
    print(summary)
    send_telegram_message(
        f"🏁 انتهى الفحص القوي.\n"
        f"🟢 found: {len(found_list)}\n"
        f"🔴 taken: {len(taken_list)}\n"
        f"🟡 error: {len(error_list)}\n"
        f"المتاحون: {', '.join(found_list) if found_list else 'لا يوجد'}"
    )

if __name__ == "__main__":
    main()