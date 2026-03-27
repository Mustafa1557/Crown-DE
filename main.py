import http.server
import socketserver
import threading
import os
import telebot
import yt_dlp
import re

# --- 1. كود منع النوم (Keep-Alive Server) ---
def run_static_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🚀 Admin Server active on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Server error: {e}")

threading.Thread(target=run_static_server, daemon=True).start()

# --- 2. إعدادات الإدارة والبوت (ببياناتك يا مصطفى) ---
TOKEN = "8283078572:AAH50vJAbO4ASd48jJx1TrjGlSmYk4_WQUU"
ADMIN_ID = 8168754101
bot = telebot.TeleBot(TOKEN)
user_data = {} 

# --- 3. محرك التحميل (CrownEngine V4 Pro) ---
class CrownEngine:
    def __init__(self, d_type='video'):
        self.opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
            'user_agent': 'com.zhiliaoapp.musically/2022405040 (Linux; U; Android 12; Pixel 6 Pro)',
            'referer': 'https://www.tiktok.com/',
            'retries': 5,
            'socket_timeout': 25,
            'ignoreerrors': True,
            # تنظيف يوتيوب من الوصف والزحمة
            'writedescription': False,
            'writeinfojson': False,
        }

    def download(self, url):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info) if info else None
        except:
            return None

# --- 4. نظام المراقبة والإشعارات ---
def notify_admin(user_info, action_type, detail):
    if ADMIN_ID != 0:
        msg = (f"🔔 **إشعار إداري جديد**\n\n"
               f"👤 المستخدم: {user_info.first_name}\n"
               f"🆔 الآيدي: `{user_info.id}`\n"
               f"⚙️ العملية: {action_type}\n"
               f"🔗 التفاصيل: {detail}")
        try:
            bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
        except:
            print("❌ فشل إرسال إشعار للأدمن")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    notify_admin(message.from_user, "ضغط Start", "بدأ استخدام البوت")
    bot.send_message(message.chat.id, "👑 **CrownDL V4 - نسخة الإدارة**\n\nأرسل رابط فيديو تيك توك أو يوتيوب وسأقوم بالتحميل فوراً!", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_url(message):
    url = message.text
    uid = message.chat.id
    
    if re.match(r'(https?://.+)', url):
        # مراقبة الرابط المرسل
        notify_admin(message.from_user, "أرسل رابطاً للتحميل", url)
        
        user_data[uid] = {'url': url}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎬 فيديو", callback_data="vid"),
            telebot.types.InlineKeyboardButton("🎵 موسيقى", callback_data="aud")
        )
        bot.reply_to(message, "⚙️ **اختر الصيغة:**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ الرابط غير مدعوم حالياً.")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    url = user_data.get(uid, {}).get('url')
    
    if not url: return

    bot.edit_message_text("⏳ جاري التحميل... سأرسله لك فوراً", uid, call.message.message_id)
    
    file_type = 'audio' if call.data == 'aud' else 'video'
    engine = CrownEngine(file_type)
    file_path = engine.download(url)
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                caption = "✅ تم التحميل بواسطة @CrownDL_bot"
                if file_type == 'audio':
                    bot.send_audio(uid, f, caption=caption)
                else:
                    bot.send_video(uid, f, caption=caption)
            bot.delete_message(uid, call.message.message_id)
        except Exception as e:
            bot.send_message(uid, f"❌ خطأ في الإرسال: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
    else:
        bot.send_message(uid, "❌ فشل التحميل. قد يكون الرابط خاصاً أو محظوراً.")

if __name__ == "__main__":
    print("✅ Admin System Online")
    bot.infinity_polling()
