import http.server
import socketserver
import threading
import os
import telebot
import yt_dlp
import re

# --- 1. كود الخداع لـ Render (Server Keep-Alive) ---
def run_static_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"✅ Web Server running on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Web server error: {e}")

threading.Thread(target=run_static_server, daemon=True).start()

# --- 2. إعدادات البوت ---
TOKEN = "8283078572:AAH50vJAbO4ASd48jJx1TrjGlSmYk4_WQUU"
bot = telebot.TeleBot(TOKEN)
user_data = {} 

# --- 3. كلاس المحرك المطور (CrownEngine) بخدعة الأندرويد ---
class CrownEngine:
    def __init__(self, d_type='video'):
        self.d_type = d_type
        self.opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            # 🛡️ الخدعة الكبرى: التظاهر بأننا تطبيق تيك توك أندرويد
            'user_agent': 'com.zhiliaoapp.musically/2022405040 (Linux; U; Android 12; en_US; Pixel 6 Pro; Build/SQ3A.220705.003; Cronet/58.0.2991.0)',
            'referer': 'https://www.tiktok.com/',
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'add_header': [
                'Accept-Language: en-US,en;q=0.9',
                'Range: bytes=0-',
            ],
        }

    def download(self, url):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None: return None
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"❌ Error Detail: {e}")
            return None

def is_valid_url(url):
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be|tiktok\.com|facebook\.com|instagram\.com|twitter\.com|x\.com|fb\.watch)/.+'
    return re.match(pattern, url)

# --- 4. معالجة الرسائل ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    bot.send_message(uid, "👑 **CrownDL V3 - Android Identity Active**\n\nأرسل رابط تيك توك الآن لنختبر الخدعة!", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_incoming_url(message):
    uid = message.chat.id
    url = message.text
    if is_valid_url(url):
        user_data[uid] = {'last_url': url}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("فيديو 🎬", callback_data="vid"),
            telebot.types.InlineKeyboardButton("موسيقى 🎵", callback_data="aud")
        )
        bot.reply_to(message, "⚙️ **اختر الصيغة:**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ الرابط غير مدعوم.")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    url = user_data.get(uid, {}).get('last_url')
    
    if not url:
        bot.send_message(uid, "❌ انتهت الجلسة.")
        return

    bot.edit_message_text("⏳ جاري محاولة خداع السيرفر والتحميل...", uid, call.message.message_id)
    
    file_type = 'audio' if call.data == 'aud' else 'video'
    engine = CrownEngine(file_type)
    file_path = engine.download(url)
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                if file_type == 'audio':
                    bot.send_audio(uid, f, caption="تم بواسطة @CrownDL_bot 👑")
                else:
                    bot.send_video(uid, f, caption="تم بواسطة @CrownDL_bot 👑")
        except Exception as e:
            bot.send_message(uid, f"❌ خطأ في الإرسال: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        bot.send_message(uid, "❌ فشل التحميل. تيك توك لا يزال يكتشف السيرفر. سنحتاج لبروكسي في المرحلة القادمة!")

if __name__ == "__main__":
    print("✅ CrownDL is LIVE now!")
    bot.infinity_polling()
