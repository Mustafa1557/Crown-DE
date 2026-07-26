import telebot
import os
import random
import uuid
from datetime import datetime, timezone
import threading
from flask import Flask
from yt_dlp import YoutubeDL
from supabase import create_client

# --- [0] إعداد Flask لإبقاء البوت Live ---
app = Flask('')
@app.route('/')
def home(): return "Bot is online ✅"

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

# --- [2] دوال VIP ---
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

def check_vip_status(user_id):
    try:
        response = supabase.table("users").select("is_vip, subscription_end").eq("user_id", str(user_id)).execute()
        if response.data:
            user = response.data[0]
            if user['is_vip']:
                if user['subscription_end']:
                    expiry = datetime.fromisoformat(user['subscription_end'].replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) < expiry:
                        return True
                    else:
                        supabase.table("users").update({"is_vip": False}).eq("user_id", str(user_id)).execute()
                        return False
                return True
    except Exception as e:
        print(f"VIP Check Error: {e}")
    return False

# --- [3] نظام الكوكيز الحذر ---
def get_cookie_for_url(url):
    cookie_name = None
    if "tiktok.com" in url:
        cookie_name = "tiktok_cookies.txt"

    if cookie_name:
        full_path = os.path.join(BASE_DIR, cookie_name)
        if os.path.exists(full_path):
            return full_path
    return None

# --- [4] دالة التحميل المرنة (تتجاوز خطأ الكوكيز) ---
def start_download(message, f_type, res, url_id):
    chat_id = message.chat.id
    url = url_storage.get(url_id)
    if not url:
        bot.send_message(chat_id, "انتهت صلاحية الرابط، أرسله مرة ثانية.")
        return

    status_msg = bot.send_message(chat_id, "🔍 جاري تجهيز طلبك...")
    cookie = get_cookie_for_url(url)

    # إعداد خيارات التحميل الأساسية بدون كوكيز أولاً لمنع توقف البوت
    base_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(BASE_DIR, f'file_{chat_id}_{url_id}.%(ext)s'),
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 50 * 1024 * 1024, # حد تيليجرام 50MB
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'add_header': ['Accept-Language: ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7'],
        'extractor_args': {'tiktok': {'webpage_download': True}}
    }

    filename = None
    bot.edit_message_text("⏳ جاري التحميل... هذا ممكن ياخذ دقيقة", chat_id, status_msg.message_id)

    # المحاولة 1: التنزيل المباشر بدون كوكيز
    try:
        with YoutubeDL(base_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e1:
        print(f"Direct download failed, trying cookies if available... Error: {e1}")
        
        # المحاولة 2: إذا فشل التنزيل المباشر وكان ملف الكوكيز موجوداً
        if cookie:
            try:
                cookie_opts = base_opts.copy()
                cookie_opts['cookiefile'] = cookie
                with YoutubeDL(cookie_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
            except Exception as e2:
                print(f"Cookie download also failed: {e2}")

    # معالجة رفع الملف أو إظهار الخطأ
    try:
        if filename and os.path.exists(filename):
            bot.edit_message_text("📤 جاري الرفع لك...", chat_id, status_msg.message_id)
            with open(filename, 'rb') as f:
                if f_type == "vid":
                    bot.send_video(chat_id, f, caption="تم بنجاح ✅")
                else:
                    bot.send_audio(chat_id, f, caption="تم بنجاح ✅")
            bot.delete_message(chat_id, status_msg.message_id)
        else:
            raise Exception("Unable to download video with or without cookies.")

    except Exception as e:
        error_text = str(e)
        print(f"Download Error: {error_text}")
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"Error for user {chat_id}\nURL: {url}\n\n{error_text[:2000]}")

        if "File size" in error_text or "max_filesize" in error_text:
            user_error = "حجم الفيديو أكبر من 50MB، ما أقدر أرسله."
        else:
            user_error = "تعذر التحميل. تأكد أن الرابط صحيح وعام وليس خاص."

        bot.edit_message_text(f"❌ {user_error}", chat_id, status_msg.message_id)

    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
        url_storage.pop(url_id, None)

# --- [5] استقبال الروابط ومعالجتها ---
@bot.message_handler(func=lambda m: m.text and "tiktok.com" in m.text)
def handle_link(message):
    register_or_update_user(message)
    url = message.text

    url_id = str(uuid.uuid4())[:8]
    url_storage[url_id] = url
    start_download(message, "vid", "best", url_id)

@bot.message_handler(func=lambda m: True)
def handle_other(message):
    bot.reply_to(message, "أرسل رابط تيك توك للتحميل 📥")

if __name__ == "__main__":
    print("Bot Started")
    bot.infinity_polling()
