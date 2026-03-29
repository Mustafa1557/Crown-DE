import http.server
import socketserver
import threading
import os
import telebot
import yt_dlp
import re

# --- 1. خادم البقاء (Keep-Alive) ---
def run_static_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except: pass

threading.Thread(target=run_static_server, daemon=True).start()

# --- 2. الإعدادات (مصطفى) ---
TOKEN = "8283078572:AAH50vJAbO4ASd48jJx1TrjGlSmYk4_WQUU"
ADMIN_ID = 8168754101
bot = telebot.TeleBot(TOKEN)
user_data = {} 

class CrownEngine:
    def __init__(self, d_type='video'):
        self.opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referer': 'https://www.google.com/',
        }

    def download(self, url):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info) if info else None
        except: return None

# --- 3. الأوامر والردود ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # إشعار للأدمن
    try: bot.send_message(ADMIN_ID, f"👤 مستخدم جديد: {message.from_user.first_name}")
    except: pass
    
    welcome_text = (
        "👑 **مرحباً بك في CrownDL**\n\n"
        "أرسل لي رابط الفيديو من (YouTube, TikTok, Facebook) وسأقوم بتحميله لك فوراً."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_url(message):
    url = message.text
    if re.match(r'(https?://.+)', url):
        user_data[message.chat.id] = {'url': url}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎬 فيديو (MP4)", callback_data="vid"),
            telebot.types.InlineKeyboardButton("🎵 صوت (MP3)", callback_data="aud")
        )
        bot.reply_to(message, "⚙️ **اختر الجودة المطلوبة:**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ من فضلك أرسل رابطاً صحيحاً.")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    url = user_data.get(uid, {}).get('url')
    if not url: return

    bot.edit_message_text("⏳ جاري المعالجة... يرجى الانتظار", uid, call.message.message_id)
    
    file_type = 'audio' if call.data == 'aud' else 'video'
    engine = CrownEngine(file_type)
    file_path = engine.download(url)
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                caption = "✅ تم التحميل بواسطة @CrownDL_bot"
                if file_type == 'audio': bot.send_audio(uid, f, caption=caption)
                else: bot.send_video(uid, f, caption=caption)
            bot.delete_message(uid, call.message.message_id)
        except:
            bot.send_message(uid, "❌ حدث خطأ أثناء إرسال الملف.")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
    else:
        bot.send_message(uid, "❌ فشل التحميل. الرابط قد يكون خاصاً أو غير مدعوم حالياً.")

if __name__ == "__main__":
    print("✅ CrownDL Engine Online")
    bot.infinity_polling()
