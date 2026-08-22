# كود بايثون مع واجهة موقع (Flask) - يفتح صفحة أمامك لإنشاء حساب ويجيب التوكن
from flask import Flask, render_template_string, request, jsonify
import requests
import time
import json
import random
import threading
from twocaptcha import TwoCaptcha

app = Flask(__name__)

# ====== الإعدادات ======
PROXY_LIST = ["http://user:pass@ip:port"]
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
# ======================

solver = TwoCaptcha(CAPTCHA_API_KEY)
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "*/*"
}

def rotate_proxy():
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        session.proxies = {"http": proxy, "https": proxy}

def solve_hcaptcha(sitekey="4c672d35-0701-42b2-88c3-78380b0db560"):
    result = solver.hcaptcha(sitekey=sitekey, url="https://discord.com/register", timeout=120)
    return result.get("code")

def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def create_discord_account(username, password):
    rotate_proxy()
    email = f"user{random.randint(10000,99999)}@tempmail.com"
    captcha_token = solve_hcaptcha()
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
    resp = session.post("https://discord.com/api/v9/auth/register", headers=headers, json=payload)
    if resp.status_code == 201:
        data = resp.json()
        token = data.get("token")
        user_id = data.get("id")
        send_to_telegram(f"✅ New account\nID: {user_id}\nToken: <code>{token}</code>")
        return {"success": True, "token": token, "user_id": user_id, "email": email, "password": password}
    else:
        return {"success": False, "error": resp.text}

# ======= واجهة الموقع =======
HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Discord Account Creator</title>
    <style>
        body { background: #1a1a2e; color: #eee; font-family: Arial; text-align: center; padding: 50px; }
        input, button { padding: 12px; margin: 8px; border-radius: 8px; border: none; font-size: 16px; }
        input { background: #16213e; color: #fff; width: 250px; }
        button { background: #0f3460; color: #fff; cursor: pointer; width: 180px; }
        button:hover { background: #1a5276; }
        #result { margin-top: 30px; background: #0d1b2a; padding: 20px; border-radius: 10px; white-space: pre-wrap; text-align: left; }
        .token { color: #4fc3f7; word-break: break-all; }
        .error { color: #ff6b6b; }
    </style>
</head>
<body>
    <h1>🚀 Discord Account Generator</h1>
    <form id="createForm">
        <input type="text" id="username" placeholder="Username" value="UserX_123" required><br>
        <input type="text" id="password" placeholder="Password" value="SecurePass123!" required><br>
        <button type="submit">Create Account</button>
    </form>
    <div id="result">⏳ Waiting for action...</div>
    <script>
        document.getElementById('createForm').onsubmit = async function(e) {
            e.preventDefault();
            const uname = document.getElementById('username').value;
            const pass = document.getElementById('password').value;
            document.getElementById('result').innerHTML = '⏳ Creating account... (captcha solving may take 30-60s)';
            try {
                const resp = await fetch('/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: uname, password: pass})
                });
                const data = await resp.json();
                if (data.success) {
                    document.getElementById('result').innerHTML = 
                        '✅ <b>Account Created!</b>\n' +
                        'User ID: ' + data.user_id + '\n' +
                        'Token: <span class="token">' + data.token + '</span>\n' +
                        'Email: ' + data.email + '\n' +
                        'Password: ' + data.password;
                } else {
                    document.getElementById('result').innerHTML = '❌ <span class="error">Error:</span> ' + data.error;
                }
            } catch(err) {
                document.getElementById('result').innerHTML = '❌ <span class="error">Request failed:</span> ' + err;
            }
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/create', methods=['POST'])
def create():
    data = request.get_json()
    username = data.get('username', 'UserX_123')
    password = data.get('password', 'SecurePass123!')
    result = create_discord_account(username, password)
    return jsonify(result)

if __name__ == '__main__':
    print("✅ Server running at: http://127.0.0.1:5000")
    print("📍 Open this URL in your browser")
    app.run(host='0.0.0.0', port=5000, debug=False)