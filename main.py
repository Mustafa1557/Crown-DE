import telebot
import os
import uuid
import threading
from flask import Flask
from yt_dlp import YoutubeDL
from supabase import create_client

# --- [0] إعداد Flask لإبقاء البوت Live على Render ---
app = Flask('')
@app.route('/')
def home(): return "TikTok Bot is online ✅"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# --- [1] إعدادات البوت وقاعدة البيانات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = telebot.TeleBot(BOT_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
url_storage = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- [2] تسجيل المستخدمين ---
def register_or_update_user(message):
    try:
        user_data = {
            "user_id": str(message.from_user.id),
            "username": message.from_user.username or "Unknown",
            "first_name": message.from_user.first_name or "User"
        }
        supabase.table("users").upsert(user_data, on_conflict="user_id").execute()
    except Exception as e:
        print(f"Supabase Error: {e}")

# --- [3] جلب ملف كوكيز تيك توك ---
def get_tiktok_cookie():
    cookie_path = os.path.join(BASE_DIR, "tiktok_cookies.txt")
    if os.path.exists(cookie_path):
        return cookie_path
    else:
        print("Warning: tiktok_cookies.txt not found")
        return None

# --- [4] دالة التحميل والرفع ---
def start_download(message, url_id):
    chat_id = message.chat.id
    url = url_storage.get(url_id)
    if not url:
        bot.send_message(chat_id, "انتهت صلاحية الرابط، أرسله مرة ثانية.")
        return

    status_msg = bot.send_message(chat_id, "🔍 جاري تجهيز الفيديو من تيك توك...")
    cookie = get_tiktok_cookie()

    opts = {
        'format': 'best[ext=mp4]/bestvideo+bestaudio/best',
        'outtmpl': os.path.join(BASE_DIR, f'tiktok_{chat_id}_{url_id}.%(ext)s'),
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 50 * 1024 * 1024, # حد تيليجرام 50MB
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'add_header': ['Accept-Language: ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7'],
        'extractor_args': {'tiktok': {'webpage_download': True}}
    }

    if cookie:
        opts['cookiefile'] = cookie

    filename = None
    try:
        bot.edit_message_text("⏳ جاري التحميل...", chat_id, status_msg.message_id)
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 جاري الرفع لك...", chat_id, status_msg.message_id)
            with open(filename, 'rb') as f:
                bot.send_video(chat_id, f, caption="تم التحميل بنجاح ✅")

            bot.delete_message(chat_id, status_msg.message_id)

    except Exception as e:
        error_text = str(e)
        print(f"Download Error: {error_text}")
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"Error for user {chat_id}\nURL: {url}\n\n{error_text[:2000]}")

        if "File size" in error_text or "max_filesize" in error_text:
            user_error = "حجم الفيديو أكبر من 50MB، ما أقدر أرسله."
        else:
            user_error = "تعذر تحميل الفيديو. تأكد أن الحساب ليس خاصاً وأن الرابط صحيح."

        bot.edit_message_text(f"❌ {user_error}", chat_id, status_msg.message_id)

    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
        url_storage.pop(url_id, None)

# --- [5] استقبال روابط تيك توك فقط ---
@bot.message_handler(func=lambda m: m.text and "tiktok.com" in m.text)
def handle_tiktok_link(message):
    register_or_update_user(message)
    
    url_id = str(uuid.uuid4())[:8]
    url_storage[url_id] = message.text

    start_download(message, url_id)

# استقبال باقي الرسائل غير روابط تيك توك
@bot.message_handler(func=lambda m: True)
def handle_other(message):
    bot.reply_to(message, "أرسل رابط تيك توك فقط للتحميل 📥")

if __name__ == "__main__":
    print("TikTok Bot Started")
    bot.infinity_polling()
