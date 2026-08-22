# كود بايثون - إنشاء حساب ديسكورد كل 10 ثواني، حفظ البيانات في ملف vv.txt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from twocaptcha import TwoCaptcha
import time
import random
import requests
import json
import re
import string
import os

# ====== الإعدادات ======
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
INTERVAL_SECONDS = 10
FILE_NAME = "vv.txt"
# ======================

solver = TwoCaptcha(CAPTCHA_API_KEY)

def generate_random_username(length=8):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def generate_random_email():
    domains = ["tempmail.com", "10minutemail.com", "guerrillamail.com", "mailnator.com"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domains)}"

def save_to_file(username, token, email, password):
    with open(FILE_NAME, "a", encoding="utf-8") as f:
        f.write(f"Username: {username}\n")
        f.write(f"Token: {token}\n")
        f.write(f"Email: {email}\n")
        f.write(f"Password: {password}\n")
        f.write("-" * 50 + "\n")
    print(f"💾 Saved to {FILE_NAME}")

def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def solve_hcaptcha_from_site(site_key, page_url):
    result = solver.hcaptcha(sitekey=site_key, url=page_url, timeout=120)
    return result.get("code")

def create_discord_account():
    username = generate_random_username()
    password = generate_random_password()
    email = generate_random_email()

    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print(f"🌐 Creating account... Username: {username}")
        driver.get("https://discord.com/register")
        time.sleep(2)

        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(email)
        time.sleep(0.3)

        username_input = driver.find_element(By.NAME, "username")
        username_input.clear()
        username_input.send_keys(username)
        time.sleep(0.3)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        time.sleep(0.3)

        month_select = driver.find_element(By.NAME, "month")
        month_select.click()
        month_select.find_element(By.XPATH, "//option[@value='1']").click()
        time.sleep(0.2)

        day_input = driver.find_element(By.NAME, "day")
        day_input.clear()
        day_input.send_keys(str(random.randint(1, 28)))
        time.sleep(0.2)

        year_input = driver.find_element(By.NAME, "year")
        year_input.clear()
        year_input.send_keys(str(random.randint(1980, 2002)))
        time.sleep(1)

        print("🔐 Solving hCaptcha...")
        site_key = driver.find_element(By.CLASS_NAME, "hcaptcha").get_attribute("data-sitekey")
        captcha_token = solve_hcaptcha_from_site(site_key, "https://discord.com/register")
        print(f"✅ Captcha solved")

        driver.execute_script(f"document.querySelector('[name=\"captcha-key\"]').value = '{captcha_token}'")
        time.sleep(1)

        continue_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        continue_button.click()
        time.sleep(6)

        token = None
        try:
            token = driver.execute_script("return localStorage.getItem('token')")
        except:
            pass

        if not token:
            try:
                logs = driver.get_log("performance")
                for log in logs:
                    if "token" in str(log):
                        match = re.search(r'"token":"([^"]+)"', str(log))
                        if match:
                            token = match.group(1)
                            break
            except:
                pass

        if not token:
            try:
                page_text = driver.page_source
                match = re.search(r'"token":"([^"]+)"', page_text)
                if match:
                    token = match.group(1)
            except:
                pass

        driver.quit()

        if token:
            # حفظ في الملف
            save_to_file(username, token, email, password)

            # إرسال للتليجرام
            msg = (f"✅ <b>Discord Account</b>\n"
                   f"👤 User: <code>{username}</code>\n"
                   f"🔑 Token: <code>{token}</code>\n"
                   f"📧 Email: <code>{email}</code>\n"
                   f"🔒 Pass: <code>{password}</code>")
            send_to_telegram(msg)
            print(f"✅ Success! Token: {token[:30]}...")
            return {
                "success": True,
                "username": username,
                "token": token,
                "email": email,
                "password": password
            }
        else:
            send_to_telegram(f"❌ Token not found\nUser: {username}\nEmail: {email}")
            return {"success": False, "username": username, "email": email}

    except Exception as e:
        error = str(e)
        send_to_telegram(f"❌ Error: {error}\nUser: {username}")
        try:
            driver.quit()
        except:
            pass
        return {"success": False, "error": error, "username": username}

if __name__ == "__main__":
    print("🚀 Starting Discord account creator every 10 seconds")
    print(f"📁 Data saved to: {FILE_NAME}")
    print("📱 Results sent to Telegram")

    # حذف الملف القديم إذا وجد
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)
        print(f"🗑️ Old {FILE_NAME} deleted")

    count = int(input("How many accounts to create? (default: 5): ") or "5")

    for i in range(count):
        print(f"\n--- Account {i+1}/{count} ---")
        start_time = time.time()
        result = create_discord_account()
        elapsed = time.time() - start_time
        print(f"Result: {result.get('success')} | Time: {elapsed:.1f}s")

        if i < count - 1:
            wait_time = max(0, INTERVAL_SECONDS - elapsed)
            print(f"⏳ Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

    print(f"\n✅ All done! Check {FILE_NAME} for saved accounts")