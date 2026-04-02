import http.server
import socketserver
import threading
import os
import telebot
import yt_dlp
import re
import random

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

# --- 2. إعدادات الإدارة والبوت 

# 🔒 سحب التوكن بشكل آمن من متغيرات البيئة في السيرفر
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

bot = telebot.TeleBot(TOKEN)
user_data = {} 

# --- 3. محرك التحميل المطور لتخطي الحظر ---
class CrownEngine:
    def __init__(self, d_type='video'):
        # قائمة User-Agents متنوعة لتجنب الحظر
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        ]
        
        self.opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'user_agent': random.choice(agents),
            'referer': 'https://www.tiktok.com/',
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'retries': 10,
            'socket_timeout': 30,
            'geo_bypass': True,
            'add_header': [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language: en-US,en;q=0.5',
            ],
        }

    def download(self, url):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info) if info else None
        except Exception as e:
            print(f"❌ Download Error: {e}")
            return None

# --- 4. نظام المراقبة ---
def notify_admin(user_info, action_type, detail):
    msg = (f"🔔 **إشعار جديد للمدير**\n\n"
           f"👤 المستخدم: {user_info.first_name}\n"
           f"🆔 الآيدي: `{user_info.id}`\n"
           f"⚙️ الحركة: {action_type}\n"
           f"🔗 الرابط: {detail}")
    try:
        bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
    except:
        pass

# --- 5. معالجة الرسائل بعبارات لينة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    notify_admin(message.from_user, "فتح البوت", "بداية الاستخدام")
    welcome_text = (
        f"يا مرحب بيك يا {message.from_user.first_name} في بوت CrownDL 👑\n\n"
        "أنا هنا عشان أخدمك وأنزل ليك الفيديوهات من يوتيوب وتيك توك وفيسبوك بكل سهولة.\n\n"
        "✨ **كل اللي عليك ترسل الرابط وهسي بنجهزه ليك!**"
    )
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(func=lambda m: True)
def handle_url(message):
    url = message.text
    uid = message.chat.id
    
    if re.match(r'(https?://.+)', url):
        notify_admin(message.from_user, "طلب تحميل", url)
        user_data[uid] = {'url': url}
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎥 فيديو (MP4)", callback_data="vid"),
            telebot.types.InlineKeyboardButton("🎵 صوت (MP3)", callback_data="aud")
        )
        bot.reply_to(message, "من عيوني! حابب أنزله ليك فيديو ولا صوت؟ 👇", reply_markup=markup)
    else:
        bot.reply_to(message, "يا غالي الرابط ده شكله ما تمام، أتأكد منه وأرسله تاني 🧐")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    url = user_data.get(uid, {}).get('url')
    
    if not url:
        bot.answer_callback_query(call.id, "حصل خطأ بسيط، أرسل الرابط تاني")
        return

    bot.edit_message_text("⏳ ثواني بس يا غالي، جاري سحب الفيديو من السيرفر...", uid, call.message.message_id)
    
    file_type = 'audio' if call.data == 'aud' else 'video'
    engine = CrownEngine(file_type)
    file_path = engine.download(url)
    
    if file_path and os.path.exists(file_path):
        try:
            bot.edit_message_text("🚀 الفيديو وصل! جاري الرفع لتليجرام...", uid, call.message.message_id)
            with open(file_path, 'rb') as f:
                caption = "تفضل يا ملك، تم التحميل بواسطة @CrownDL_bot 👑"
                if file_type == 'audio':
                    bot.send_audio(uid, f, caption=caption)
                else:
                    bot.send_video(uid, f, caption=caption)
            bot.delete_message(uid, call.message.message_id)
        except Exception as e:
            bot.send_message(uid, f"يا غالي حصلت مشكلة أثناء الإرسال: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
    else:
        bot.send_message(uid, "للأسف يا غالي السيرفر رفض الطلب، جرب فيديو تاني أو رابط يوتيوب 💔")

if __name__ == "__main__":
    print("✅ CrownDL Pro is running...")
    bot.infinity_polling()
