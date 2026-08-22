# كود بايثون - يفتح موقع Discord الرسمي في متصفح حقيقي ويسوي حساب آلياً باستخدام Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from twocaptcha import TwoCaptcha
import time
import random
import requests
import json

# ====== الإعدادات ======
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
PROXY = "http://user:pass@ip:port"  # اختياري
# ======================

solver = TwoCaptcha(CAPTCHA_API_KEY)

def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def solve_hcaptcha_from_site(site_key, page_url):
    result = solver.hcaptcha(sitekey=site_key, url=page_url, timeout=120)
    return result.get("code")

def create_discord_account_browser(username, password):
    # إعدادات المتصفح
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--window-size=1280,720")

    # إضافة بروكسي إذا وجد
    if PROXY:
        chrome_options.add_argument(f'--proxy-server={PROXY}')

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("🌐 Opening Discord registration page...")
        driver.get("https://discord.com/register")
        time.sleep(3)

        # ملء البريد الإلكتروني
        email = f"user{random.randint(10000,99999)}@tempmail.com"
        email_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(email)
        time.sleep(1)

        # ملء اسم المستخدم
        username_input = driver.find_element(By.NAME, "username")
        username_input.clear()
        username_input.send_keys(username)
        time.sleep(1)

        # ملء كلمة المرور
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        time.sleep(1)

        # اختيار تاريخ ميلاد (فوق 18 سنة)
        # الشهر
        month_select = driver.find_element(By.NAME, "month")
        month_select.click()
        month_select.find_element(By.XPATH, "//option[@value='1']").click()
        time.sleep(0.5)

        # اليوم
        day_input = driver.find_element(By.NAME, "day")
        day_input.clear()
        day_input.send_keys("15")
        time.sleep(0.5)

        # السنة
        year_input = driver.find_element(By.NAME, "year")
        year_input.clear()
        year_input.send_keys("2000")
        time.sleep(1)

        # حل hCaptcha باستخدام 2captcha
        print("🔐 Solving hCaptcha via 2captcha...")
        site_key = driver.find_element(By.CLASS_NAME, "hcaptcha").get_attribute("data-sitekey")
        captcha_token = solve_hcaptcha_from_site(site_key, "https://discord.com/register")
        print(f"✅ Captcha solved: {captcha_token[:30]}...")

        # حقن التوكن في hCaptcha
        driver.execute_script(f"document.querySelector('[name=\"captcha-key\"]').value = '{captcha_token}'")
        time.sleep(1)

        # الضغط على زر الاستمرار
        print("🖱️ Submitting form...")
        continue_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        continue_button.click()

        # انتظار الرد
        time.sleep(5)

        # التحقق من نجاح التسجيل
        try:
            # بعد النجاح، يتم توجيه المستخدم إلى صفحة الدردشة أو يظهر توكن في localStorage
            token = driver.execute_script("return localStorage.getItem('token')")
            if not token:
                # محاولة استخراج التوكن من الـ network
                logs = driver.get_log("performance")
                for log in logs:
                    if "token" in str(log):
                        import re
                        match = re.search(r'"token":"([^"]+)"', str(log))
                        if match:
                            token = match.group(1)
                            break
            if token:
                send_to_telegram(f"✅ New Discord Account\nUsername: {username}\nToken: <code>{token}</code>\nEmail: {email}\nPass: {password}")
                print(f"✅ Success! Token: {token[:30]}...")
                return {"success": True, "token": token, "email": email, "username": username, "password": password}
            else:
                # إذا لم نجد التوكن، نأخذها من الصفحة
                page_text = driver.page_source
                import re
                match = re.search(r'"token":"([^"]+)"', page_text)
                if match:
                    token = match.group(1)
                    send_to_telegram(f"✅ New Account (from page)\nToken: <code>{token}</code>")
                    return {"success": True, "token": token}
        except Exception as e:
            print(f"⚠️ Could not extract token: {e}")

        # إذا وصلنا هنا، التسجيل فشل أو لم نجد التوكن
        error_msg = "Registration completed but token not found. Check browser manually."
        send_to_telegram(f"❌ {error_msg}")
        return {"success": False, "error": error_msg, "page_source": driver.page_source[:500]}

    except Exception as e:
        error = str(e)
        send_to_telegram(f"❌ Browser error: {error}")
        return {"success": False, "error": error}
    finally:
        # إبقاء المتصفح مفتوحاً لمشاهدة النتيجة (علّق السطر التالي إذا تريد إغلاقه تلقائياً)
        # driver.quit()
        pass

if __name__ == "__main__":
    username = input("Enter username: ") or "UserX_123"
    password = input("Enter password: ") or "SecurePass123!"
    result = create_discord_account_browser(username, password)
    print("\n=== RESULT ===")
    print(json.dumps(result, indent=2))