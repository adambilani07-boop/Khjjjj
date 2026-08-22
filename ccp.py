# كود بايثون - ينشئ حساب ديسكورد عبر الموقع الرسمي، يستخدم بريد من temp-mail، اسم مستخدم عشوائي، كلمة مرور عشوائية، ويحفظ في bcc.txt
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
FILE_NAME = "bcc.txt"
# ======================

solver = TwoCaptcha(CAPTCHA_API_KEY)

def generate_random_username(length=8):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))

def generate_random_password():
    # كلمة مرور قوية مثل fshrechgsv@0876
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*"
    password = ''.join(random.choices(string.ascii_lowercase, k=8))
    password += ''.join(random.choices(string.digits, k=4))
    password += random.choice("!@#$%^&*")
    # خلط
    password_list = list(password)
    random.shuffle(password_list)
    return ''.join(password_list)

def get_temp_email():
    try:
        # استخدام خدمة temp-mail.org API
        response = requests.get("https://api.temp-mail.org/request/domains/format/json", timeout=10)
        domains = response.json()
        domain = random.choice(domains) if domains else "tempmail.com"
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{username}@{domain}"
        return email
    except Exception as e:
        print(f"⚠️ Temp-mail API error: {e}, using fallback")
        domains = ["tempmail.com", "10minutemail.com", "guerrillamail.com"]
        return f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}@{random.choice(domains)}"

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
    # توليد بيانات عشوائية
    username = generate_random_username()
    password = generate_random_password()
    email = get_temp_email()

    print(f"📧 Email: {email}")
    print(f"👤 Username: {username}")
    print(f"🔒 Password: {password}")

    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("🌐 Opening Discord registration page...")
        driver.get("https://discord.com/register")
        time.sleep(3)

        # إدخال البريد الإلكتروني
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(email)
        time.sleep(0.5)

        # إدخال اسم المستخدم
        username_input = driver.find_element(By.NAME, "username")
        username_input.clear()
        username_input.send_keys(username)
        time.sleep(0.5)

        # إدخال كلمة المرور
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        time.sleep(0.5)

        # اختيار تاريخ ميلاد (فوق 18 سنة)
        month_select = driver.find_element(By.NAME, "month")
        month_select.click()
        month_select.find_element(By.XPATH, "//option[@value='1']").click()
        time.sleep(0.3)

        day_input = driver.find_element(By.NAME, "day")
        day_input.clear()
        day_input.send_keys(str(random.randint(1, 28)))
        time.sleep(0.3)

        year_input = driver.find_element(By.NAME, "year")
        year_input.clear()
        year_input.send_keys(str(random.randint(1980, 2002)))
        time.sleep(1)

        # حل hCaptcha
        print("🔐 Solving hCaptcha via 2captcha...")
        site_key = driver.find_element(By.CLASS_NAME, "hcaptcha").get_attribute("data-sitekey")
        captcha_token = solve_hcaptcha_from_site(site_key, "https://discord.com/register")
        print("✅ Captcha solved")

        # حقن التوكن
        driver.execute_script(f"document.querySelector('[name=\"captcha-key\"]').value = '{captcha_token}'")
        time.sleep(1)

        # الضغط على زر الاستمرار
        continue_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        continue_button.click()
        time.sleep(8)

        # استخراج التوكن
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
            # حفظ في ملف bcc.txt
            save_to_file(username, token, email, password)

            # إرسال للتليجرام
            msg = (f"✅ <b>New Discord Account</b>\n"
                   f"👤 Username: <code>{username}</code>\n"
                   f"🔑 Token: <code>{token}</code>\n"
                   f"📧 Email: <code>{email}</code>\n"
                   f"🔒 Password: <code>{password}</code>")
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
            error_msg = "Account created but token not found"
            send_to_telegram(f"❌ {error_msg}\nUsername: {username}\nEmail: {email}")
            return {"success": False, "error": error_msg, "username": username, "email": email}

    except Exception as e:
        error = str(e)
        send_to_telegram(f"❌ Error: {error}\nUsername: {username}")
        try:
            driver.quit()
        except:
            pass
        return {"success": False, "error": error, "username": username}

if __name__ == "__main__":
    print("🚀 Discord Account Creator (temp-mail + random data)")
    print(f"📁 Data saved to: {FILE_NAME}")
    print("📱 Results sent to Telegram")

    # حذف الملف القديم إذا وجد
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)
        print(f"🗑️ Old {FILE_NAME} deleted")

    count = int(input("How many accounts to create? (default: 1): ") or "1")

    for i in range(count):
        print(f"\n--- Account {i+1}/{count} ---")
        start_time = time.time()
        result = create_discord_account()
        elapsed = time.time() - start_time
        print(f"Result: {result.get('success')} | Time: {elapsed:.1f}s")

        if i < count - 1:
            wait_time = 10  # 10 ثواني بين كل حساب
            print(f"⏳ Waiting {wait_time} seconds...")
            time.sleep(wait_time)

    print(f"\n✅ All done! Check {FILE_NAME} for saved accounts")