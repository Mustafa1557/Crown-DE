import os
import telebot
from telebot import types
from threading import Thread
from flask import Flask
from supabase import create_client, Client
import yt_dlp

# --- 1. سيرفر ---
app = Flask('')

@app.route('/')
def home():
    return "🚀 البوت شغال!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# --- 2. إعدادات ---
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

SUPABASE_URL = "https://nrcpotvspxdvxlxbwzto.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

user_data = {}

TIKTOK_COOKIES = "/etc/secrets/tiktok_cookies.txt"
FACEBOOK_COOKIES = "/etc/secrets/facebook_cookies.txt"

# --- 3. start ---
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "👑 CrownDL جاهز! أرسل الرابط")

# --- 4. استقبال ---
@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text
    chat_id = m.chat.id

    user_data[chat_id] = url

    if "youtube" in url or "youtu.be" in url:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("720p", callback_data="yt720"),
            types.InlineKeyboardButton("480p", callback_data="yt480"),
            types.InlineKeyboardButton("360p", callback_data="yt360")
        )
        bot.send_message(chat_id, "اختر الجودة", reply_markup=markup)

    elif "facebook" in url or "fb.watch" in url:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("HD", callback_data="fbhd"),
            types.InlineKeyboardButton("SD", callback_data="fbsd")
        )
        bot.send_message(chat_id, "اختر الجودة", reply_markup=markup)

    elif "tiktok" in url:
        smart_download(chat_id, url, TIKTOK_COOKIES, "best")

    else:
        bot.send_message(chat_id, "❌ رابط غير مدعوم")

# --- 5. الأزرار ---
@bot.callback_query_handler(func=lambda c: True)
def buttons(c):
    chat_id = c.message.chat.id

    if chat_id not in user_data:
        bot.send_message(chat_id, "❌ أرسل الرابط مرة تانية")
        return

    url = user_data[chat_id]
    bot.edit_message_reply_markup(chat_id, c.message.message_id, reply_markup=None)

    if c.data == "yt720":
        smart_download(chat_id, url, None, "bestvideo[height<=720]+bestaudio/best")

    elif c.data == "yt480":
        smart_download(chat_id, url, None, "bestvideo[height<=480]+bestaudio/best")

    elif c.data == "yt360":
        smart_download(chat_id, url, None, "bestvideo[height<=360]+bestaudio/best")

    elif c.data == "fbhd":
        smart_download(chat_id, url, FACEBOOK_COOKIES, "best")

    elif c.data == "fbsd":
        smart_download(chat_id, url, FACEBOOK_COOKIES, "worst")

    del user_data[chat_id]

# --- 6. تحميل ذكي ---
def smart_download(chat_id, url, cookies_path, format_opt):
    bot.send_message(chat_id, "⏳ جاري التحميل...")

    use_cookies = False
    if cookies_path and os.path.exists(cookies_path) and cookies_path.endswith(".txt"):
        use_cookies = True

    try:
        download(chat_id, url, format_opt, cookies_path if use_cookies else None)

    except Exception as e:
        print("فشل أول مرة:", e)

        try:
            bot.send_message(chat_id, "🔁 إعادة المحاولة...")
            download(chat_id, url, format_opt, None)

        except Exception:
            bot.send_message(chat_id, "❌ فشل التحميل نهائياً!")

# --- 7. تنفيذ التحميل ---
def download(chat_id, url, format_opt, cookies_path):
    ydl_opts = {
        'format': format_opt,
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }

    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)

        # منع الفيديو الكبير
        if os.path.getsize(path) > 50 * 1024 * 1024:
            bot.send_message(chat_id, "❌ الفيديو كبير")
            os.remove(path)
            return

        with open(path, 'rb') as v:
            bot.send_video(chat_id, v)

        os.remove(path)

        try:
            supabase.table("downloads").insert({
                "chat_id": chat_id,
                "url": url,
                "status": "success"
            }).execute()
        except:
            pass

# --- 8. تشغيل ---
if __name__ == "__main__":
    keep_alive()
    print("🤖 البوت شغال...")
    bot.infinity_polling()
