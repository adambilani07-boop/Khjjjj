# الكود الكامل مع دعم 2captcha - نسخة بايثون جاهزة للتشغيل
import requests
import time
import json
import random
import sys
from twocaptcha import TwoCaptcha

class DiscordCreator:
    def __init__(self, proxy_list, api_key_2captcha, telegram_bot_token, telegram_chat_id):
        self.proxy_list = proxy_list
        self.captcha_solver = TwoCaptcha(api_key_2captcha)
        self.session = requests.Session()
        self.base_url = "https://discord.com/api/v9"
        self.telegram_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }

    def rotate_proxy(self):
        if not self.proxy_list:
            return
        proxy = random.choice(self.proxy_list)
        self.session.proxies = {
            "http": proxy,
            "https": proxy
        }

    def get_temp_email(self):
        try:
            resp = requests.get("https://api.temp-mail.org/request/domains/format/json")
            domain = random.choice(resp.json())
            username = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
            email = f"{username}@{domain}"
            return email
        except:
            return f"user{random.randint(10000,99999)}@tempmail.com"

    def solve_hcaptcha(self, sitekey="4c672d35-0701-42b2-88c3-78380b0db560", max_retries=3):
        for attempt in range(max_retries):
            try:
                result = self.captcha_solver.hcaptcha(
                    sitekey=sitekey,
                    url="https://discord.com/register",
                    timeout=120
                )
                return result.get("code")
            except Exception as e:
                print(f"Captcha attempt {attempt+1} failed: {e}")
                time.sleep(5)
        raise Exception("All captcha attempts failed")

    def send_to_telegram(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Telegram send error: {e}")

    def check_balance(self):
        try:
            balance = self.captcha_solver.balance()
            return balance
        except:
            return 0.0

    def create_account(self, username, password):
        self.rotate_proxy()
        email = self.get_temp_email()

        balance = self.check_balance()
        if balance < 0.01:
            self.send_to_telegram("⚠️ Low balance in 2captcha: " + str(balance))
            time.sleep(60)
            return None

        captcha_token = self.solve_hcaptcha()

        payload = {
            "email": email,
            "username": username,
            "password": password,
            "invite": None,
            "consent": True,
            "date_of_birth": "2000-01-01",
            "gift_code_sku_id": None,
            "captcha_key": captcha_token
        }

        response = self.session.post(
            f"{self.base_url}/auth/register",
            headers=self.headers,
            json=payload
        )

        if response.status_code == 201:
            data = response.json()
            token = data.get("token")
            user_id = data.get("id")
            msg = (f"<b>New Discord Account</b>\n"
                   f"User ID: <code>{user_id}</code>\n"
                   f"Token: <code>{token}</code>\n"
                   f"Email: {email}\n"
                   f"Pass: {password}")
            self.send_to_telegram(msg)
            return {
                "token": token,
                "user_id": user_id,
                "email": email,
                "password": password
            }
        elif response.status_code == 429:
            retry_after = response.json().get("retry_after", 30)
            self.send_to_telegram(f"⏳ Rate limited. Waiting {retry_after}s")
            time.sleep(retry_after)
            return self.create_account(username, password)
        else:
            error_msg = f"Failed: {response.status_code} - {response.text[:200]}"
            self.send_to_telegram(f"<b>Error</b>\n{error_msg}")
            raise Exception(error_msg)

    def mass_create(self, count, base_username, password):
        accounts = []
        success_count = 0
        for i in range(count):
            try:
                uname = f"{base_username}_{random.randint(1000,9999)}"
                acc = self.create_account(uname, password)
                if acc:
                    accounts.append(acc)
                    success_count += 1
                    print(f"[{success_count}/{count}] Created: {acc['email']}")
                delay = random.uniform(20, 45)
                print(f"Waiting {delay:.1f}s...")
                time.sleep(delay)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(90)
        final_msg = f"✅ Mass creation finished. Success: {success_count}/{count}"
        self.send_to_telegram(final_msg)
        with open("accounts.json", "w") as f:
            json.dump(accounts, f, indent=2)
        return accounts

if __name__ == "__main__":
    PROXY_LIST = [
        "http://user:pass@ip1:port",
        "http://user:pass@ip2:port"
    ]
    CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    CHAT_ID = "YOUR_CHAT_ID"

    creator = DiscordCreator(PROXY_LIST, CAPTCHA_API_KEY, BOT_TOKEN, CHAT_ID)
    creator.mass_create(count=5, base_username="DiscordUser", password="SecurePass123!")