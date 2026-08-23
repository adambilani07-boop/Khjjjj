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
    # طريقة أقوى: استخدام صفحة AJAX الخاصة بـ Instagram
    url = f"https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/accounts/signup/",
        "Origin": "https://www.instagram.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    data = {
        "email": "",
        "username": username,
        "first_name": "",
        "opt_into_one_tap": "false"
    }
    session = requests.Session()
    # جلب الكوكيز أولاً
    try:
        session.get("https://www.instagram.com/", headers=headers, timeout=10)
        time.sleep(0.5)
        response = session.post(url, headers=headers, data=data, timeout=15)
        json_data = response.json()

        if json_data.get("status") == "ok":
            # إذا كان username موجوداً ومتاحاً
            if json_data.get("available") == True:
                return "found"
            elif json_data.get("available") == False:
                return "taken"
            elif json_data.get("username") == username and json_data.get("available") == True:
                return "found"
            else:
                # فحص احتياطي بطريقة HTML
                return fallback_check(username)
        else:
            return fallback_check(username)
    except:
        return fallback_check(username)
    finally:
        session.close()

def fallback_check(username):
    # طريقة احتياطية: فحص صفحة البروفايل
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    session = requests.Session()
    try:
        response = session.get(url, headers=headers, timeout=15, allow_redirects=False)
        # 404 = غير موجود = متاح
        if response.status_code == 404:
            return "found"
        # 200 = موجود = مأخوذ
        elif response.status_code == 200:
            return "taken"
        # 302 = إعادة توجيه (غالباً موجود)
        elif response.status_code == 302:
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
    threads = int(input("عدد الخيوط المتوازية (مثلاً 3 - 5): "))
    delay = float(input("وقت التأخير بين كل دورة خيوط (بالثواني، مثلاً 0.5): "))

    print(f"\n--- فحص {count} يوزر عشوائي خماسي (طريقة AJAX القوية) ---\n")
    send_telegram_message(f"✅ بدء الفحص القوي لـ {count} يوزر عشوائي خماسي")

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
                msg = f"{processed}. {user} -> ✅ متاح (found)"
                print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")
                found_list.append(user)
                send_telegram_message(f"🟢 {user} -> متاح")
            elif status == "taken":
                msg = f"{processed}. {user} -> ❌ مأخوذ (taken)"
                print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
                taken_list.append(user)
            else:
                msg = f"{processed}. {user} -> ⚠️ خطأ (error)"
                print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")
                error_list.append(user)

            if processed % threads == 0:
                time.sleep(delay)

    # === إحصاءات نهائية ===
    total = len(found_list) + len(taken_list) + len(error_list)
    summary = (
        f"\n{'='*55}\n"
        f"📊 الإحصاء النهائي:\n"
        f"🟢 متاح (found): {len(found_list)}\n"
        f"🔴 مأخوذ (taken): {len(taken_list)}\n"
        f"🟡 خطأ (error): {len(error_list)}\n"
        f"📌 المجموع الكلي: {total}\n"
        f"{'='*55}"
    )
    print(summary)

    if found_list:
        send_telegram_message(
            f"🏁 انتهى الفحص.\n"
            f"🟢 متاح: {len(found_list)}\n"
            f"🔴 مأخوذ: {len(taken_list)}\n"
            f"🟡 خطأ: {len(error_list)}\n"
            f"المتاحون: {', '.join(found_list)}"
        )
    else:
        send_telegram_message(
            f"🏁 انتهى الفحص.\n"
            f"🟢 متاح: 0\n"
            f"🔴 مأخوذ: {len(taken_list)}\n"
            f"🟡 خطأ: {len(error_list)}\n"
            f"لا يوجد يوزرات متاحة."
        )

if __name__ == "__main__":
    main()