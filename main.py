import os
import telebot
from telebot import types
from threading import Thread
from flask import Flask
from supabase import create_client, Client
import yt_dlp

# --- 1. سيرفر للحفاظ على البوت ---
app = Flask('')

@app.route('/')
def home():
    return "🚀 البوت شغال تمام!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

# --- 2. إعدادات ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8168754101

bot = telebot.TeleBot(TOKEN)
user_data = {}

SUPABASE_URL = "https://nrcpotvspxdvxlxbwzto.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TIKTOK_COOKIES = "/etc/secrets/tiktok_cookies.json"
FACEBOOK_COOKIES = "/etc/secrets/facebook_cookies.json"

# --- 3. الترحيب ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👑 أهلاً بك في CrownDL\nأرسل أي رابط للتحميل!")

# --- 4. استقبال الرسائل ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    chat_id = message.chat.id

    user_data[chat_id] = {'url': url}

    if "youtube.com" in url or "youtu.be" in url:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("720p", callback_data="yt_720"),
            types.InlineKeyboardButton("480p", callback_data="yt_480"),
            types.InlineKeyboardButton("360p", callback_data="yt_360")
        )
        bot.send_message(chat_id, "اختر الجودة:", reply_markup=markup)

    elif "facebook.com" in url or "fb.watch" in url:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("HD", callback_data="fb_hd"),
            types.InlineKeyboardButton("SD", callback_data="fb_sd")
        )
        bot.send_message(chat_id, "اختر الجودة:", reply_markup=markup)

    elif "tiktok.com" in url:
        bot.send_message(chat_id, "⏳ جاري التحميل...")
        download_video(chat_id, url, TIKTOK_COOKIES, "best")

    else:
        bot.send_message(chat_id, "❌ رابط غير مدعوم")

# --- 5. الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id

    if chat_id not in user_data:
        bot.send_message(chat_id, "❌ أرسل الرابط مرة أخرى")
        return

    url = user_data[chat_id]['url']
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

    if call.data == "yt_720":
        download_video(chat_id, url, None, "bestvideo[height<=720]+bestaudio/best")

    elif call.data == "yt_480":
        download_video(chat_id, url, None, "bestvideo[height<=480]+bestaudio/best")

    elif call.data == "yt_360":
        download_video(chat_id, url, None, "bestvideo[height<=360]+bestaudio/best")

    elif call.data == "fb_hd":
        download_video(chat_id, url, FACEBOOK_COOKIES, "best")

    elif call.data == "fb_sd":
        download_video(chat_id, url, FACEBOOK_COOKIES, "worst")

    # حذف الرابط بعد الاستخدام
    del user_data[chat_id]

# --- 6. التحميل ---
def download_video(chat_id, url, cookies_path, format_opt):
    ydl_opts = {
        'format': format_opt,
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'quiet': True,
    }

    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

            # فحص الحجم (50MB)
            if os.path.getsize(video_path) > 50 * 1024 * 1024:
                bot.send_message(chat_id, "❌ الفيديو كبير!")
                os.remove(video_path)
                return

            with open(video_path, 'rb') as video:
                bot.send_video(chat_id, video)

            os.remove(video_path)

            # تسجيل النجاح
            supabase.table("downloads").insert({
                "chat_id": chat_id,
                "url": url,
                "status": "success"
            }).execute()

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {str(e)}")

        try:
            supabase.table("downloads").insert({
                "chat_id": chat_id,
                "url": url,
                "status": "failed"
            }).execute()
        except:
            pass

# --- 7. التشغيل ---
if __name__ == "__main__":
    keep_alive()
    print("🤖 البوت شغال...")
    bot.infinity_polling()
