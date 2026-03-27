import http.server
import socketserver
import threading
import os
import telebot
import yt_dlp
import re

# --- 1. كود الاستمرارية لـ Render ---
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

# --- 3. محرك التحميل الذكي (Clean Engine) ---
class CrownEngine:
    def __init__(self, d_type='video'):
        self.d_type = d_type
        self.opts = {
            # اختيار الجودة وتحويل الصوت
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            
            # --- ميزات الفلترة والسرعة ---
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, # لا يسحب قوائم التشغيل
            'skip_download': False,
            'noplaylist': True,    # تحميل فيديو واحد فقط حتى لو الرابط قائمة
            
            # --- خدعة تخطي الحظر ---
            'user_agent': 'com.zhiliaoapp.musically/2022405040 (Linux; U; Android 12; Pixel 6 Pro)',
            'referer': 'https://www.tiktok.com/',
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'retries': 5,            # إعادة محاولة 5 مرات عند انقطاع الاتصال
            'socket_timeout': 20,    # مهلة الانتظار
            
            # --- تنظيف البيانات المرفقة ---
            'writedescription': False,
            'writeinfojson': False,
            'add_header': ['Accept-Language: en-US,en;q=0.9'],
        }

    def download(self, url):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                # سحب المعلومات الأساسية فقط للسرعة
                info = ydl.extract_info(url, download=True)
                if info is None: return None
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"❌ Error Detail: {e}")
            return None

def is_valid_url(url):
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be|tiktok\.com|facebook\.com|instagram\.com|twitter\.com|x\.com|fb\.watch)/.+'
    return re.match(pattern, url)

# --- 4. إدارة الرسائل (Minimal UI) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    bot.send_message(uid, "👑 **مرحباً بك في CrownDL Pro**\n\nأرسل الرابط وسأقوم بالتحميل مباشرة بدون تعقيدات!", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_incoming_url(message):
    uid = message.chat.id
    url = message.text
    if is_valid_url(url):
        user_data[uid] = {'last_url': url}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎬 فيديو", callback_data="vid"),
            telebot.types.InlineKeyboardButton("🎵 موسيقى", callback_data="aud")
        )
        bot.reply_to(message, "⚙️ **اختر الصيغة:**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ الرابط غير مدعوم.")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    url = user_data.get(uid, {}).get('last_url')
    
    if not url:
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة.")
        return

    bot.edit_message_text("⏳ جاري المعالجة... يرجى الانتظار", uid, call.message.message_id)
    
    file_type = 'audio' if call.data == 'aud' else 'video'
    engine = CrownEngine(file_type)
    file_path = engine.download(url)
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                if file_type == 'audio':
                    bot.send_audio(uid, f, caption="✅ تم التحميل بنجاح بواسطة @CrownDL_bot")
                else:
                    bot.send_video(uid, f, caption="✅ تم التحميل بنجاح بواسطة @CrownDL_bot")
            bot.delete_message(uid, call.message.message_id) # مسح رسالة "جاري المعالجة"
        except Exception as e:
            bot.send_message(uid, f"❌ خطأ في الإرسال: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        bot.send_message(uid, "❌ فشل التحميل. يرجى التأكد من أن الرابط عام وليس خاصاً.")

if __name__ == "__main__":
    print("✅ CrownDL Pro is LIVE now!")
    bot.infinity_polling()
