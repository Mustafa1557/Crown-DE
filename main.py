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
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving on port {port}")
        httpd.serve_forever()

threading.Thread(target=run_static_server, daemon=True).start()

# --- 2. إعدادات البوت ---
TOKEN = "8283078572:AAH50vJAbO4ASd48jJx1TrjGlSmYk4_WQUU"
bot = telebot.TeleBot(TOKEN)
user_data = {} 

# --- 3. كلاس المحرك المطور (CrownEngine) ---
class CrownEngine:
    def __init__(self, d_type='video'):
        self.d_type = d_type
        # إعدادات احترافية لتخطي الحظر وتسهيل الرفع
        self.opts = {
            # اختيار أفضل جودة فيديو مدموجة مسبقاً (عشان ما نحتاج ffmpeg للدمج)
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s', # الحفظ في مجلد /tmp الخاص بالسيرفرات
            'quiet': True,
            'no_warnings': True,
            # إضافة User-Agent حقيقي لتخطي حظر تيك توك وانستقرام
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'nocheckcertificate': True,
            'ignoreerrors': True,
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
    welcome_text = "👑 **مرحباً بك في CrownDL V2**\n\nأرسل رابط فيديو (يوتيوب، تيك توك، فيسبوك) وسأقوم بتحميله فوراً!"
    bot.send_message(uid, welcome_text, parse_mode="Markdown")

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

    bot.edit_message_text("⏳ جاري التحميل... انتظر ثواني.", uid, call.message.message_id)
    
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
        bot.send_message(uid, "❌ فشل التحميل. قد يكون الفيديو خاصاً أو محظوراً.")

if __name__ == "__main__":
    print("✅ CrownDL is LIVE now!")
    bot.infinity_polling()
