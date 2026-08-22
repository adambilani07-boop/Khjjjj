# الكود المعدل - يجمع التوكنات ويرسلها إلى بوت تليجرام
import requests
import time
import json
import random
from captcha_solver import TwoCaptchaSolver
from email_generator import TempMail

class DiscordCreator:
    def __init__(self, proxy_list, api_key_2captcha, telegram_bot_token, telegram_chat_id):
        self.proxy_list = proxy_list
        self.captcha_solver = TwoCaptchaSolver(api_key_2captcha)
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
        proxy = random.choice(self.proxy_list)
        self.session.proxies = {"http": proxy, "https": proxy}

    def get_temp_email(self):
        email = TempMail.generate()
        return email

    def solve_hcaptcha(self, sitekey="4c672d35-0701-42b2-88c3-78380b0db560"):
        token = self.captcha_solver.solve_hcaptcha(
            sitekey=sitekey,
            url="https://discord.com/register"
        )
        return token

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

    def create_account(self, username, password):
        self.rotate_proxy()
        email = self.get_temp_email()
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
            # إرسال التوكن فوراً للتليجرام
            msg = f"<b>New Discord Account</b>\nUser ID: <code>{user_id}</code>\nToken: <code>{token}</code>\nEmail: {email}\nPass: {password}"
            self.send_to_telegram(msg)
            return {
                "token": token,
                "user_id": user_id,
                "email": email,
                "password": password
            }
        else:
            error_msg = f"Failed to create: {response.text}"
            self.send_to_telegram(f"<b>Error</b>\n{error_msg}")
            raise Exception(error_msg)

    def mass_create(self, count, base_username, password):
        accounts = []
        for i in range(count):
            try:
                uname = f"{base_username}_{random.randint(1000,9999)}"
                acc = self.create_account(uname, password)
                accounts.append(acc)
                print(f"[+] Created: {acc['email']} | Token: {acc['token'][:20]}...")
                time.sleep(random.uniform(15, 30))
            except Exception as e:
                print(f"[-] Error: {e}")
                time.sleep(60)
        # إرسال ملف JSON كنسخة احتياطية
        with open("accounts.json", "w") as f:
            json.dump(accounts, f, indent=2)
        self.send_to_telegram("✅ Mass creation finished. Check accounts.json attached (send manually).")
        return accounts

if __name__ == "__main__":
    proxy_list = ["http://user:pass@ip:port"]
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_ID = "YOUR_CHAT_ID_HERE"
    creator = DiscordCreator(proxy_list, "YOUR_2CAPTCHA_API_KEY", BOT_TOKEN, CHAT_ID)
    result = creator.mass_create(count=10, base_username="UserX", password="SecurePass123")