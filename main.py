import telebot
import os
import random
import datetime
import threading
from flask import Flask
from yt_dlp import YoutubeDL
from supabase import create_client

# --- [0] إعداد Flask لإبقاء البوت Live ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- [1] إعدادات البوت وقاعدة البيانات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    ADMIN_ID = int(os.getenv("MY_ID") or 0)
except:
    ADMIN_ID = 0

bot = telebot.TeleBot(BOT_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
url_storage = {} 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- [2] دوال قاعدة البيانات ---
def register_user(message):
    user_data = {
        "user_id": str(message.from_user.id),
        "username": message.from_user.username or "Unknown",
        "first_name": message.from_user.first_name or "User"
    }
    try:
        supabase.table("users").upsert(user_data, on_conflict="user_id").execute()
    except: pass

def is_vip(user_id):
    try:
        res = supabase.table("users").select("is_vip, subscription_end").eq("user_id", str(user_id)).execute()
        if res.data:
            user = res.data[0]
            if user['is_vip']:
                if user['subscription_end']:
                    expiry = datetime.datetime.fromisoformat(user['subscription_end'].replace('Z', '+00:00'))
                    if datetime.datetime.now(datetime.timezone.utc) < expiry: return True
                    else: supabase.table("users").update({"is_vip": False}).eq("user_id", str(user_id)).execute()
                else: return True 
        return False
    except: return False

# --- [3] نظام الكوكيز (تأكد من رفع x_cookies.txt) ---
def get_cookie_for_url(url):
    cookie_name = None
    if "youtube" in url or "youtu.be" in url:
        cookie_name = random.choice(["youtube_cookies_1.txt", "youtube_cookies_2.txt"])
    elif "tiktok.com" in url:
        cookie_name = "tiktok_cookies.txt"
    elif "x.com" in url or "twitter.com" in url:
        cookie_name = "x_cookies.txt" 
    
    if cookie_name:
        full_path = os.path.join(BASE_DIR, cookie_name)
        if os.path.exists(full_path):
            return full_path
    return None

# --- [4] دالة التحميل المعدلة ---
def start_download(message, f_type, res, url_id):
    chat_id = message.chat.id
    url = url_storage.get(url_id)
    status_msg = bot.send_message(chat_id, "⏳ جاري المعالجة...")
    cookie = get_cookie_for_url(url)
    
    # تنسيق الجودة
    if "youtube" in url or "youtu.be" in url:
        fmt = f"best[height<={res}][ext=mp4]/best[ext=mp4]/best"
    else:
        # أعلى جودة لتيك توك وتويتر
        fmt = "bestvideo+bestaudio/best"

    opts = {
        'format': fmt,
        'outtmpl': os.path.join(BASE_DIR, f'file_{chat_id}_{url_id}.%(ext)s'),
        'cookiefile': cookie,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if f_type == "aud":
                new_name = filename.rsplit('.', 1)[0] + '.mp3'
                os.rename(filename, new_name)
                filename = new_name

            with open(filename, 'rb') as f:
                if f_type == "vid":
                    bot.send_video(chat_id, f)
                else:
                    bot.send_audio(chat_id, f)
            
            if os.path.exists(filename): os.remove(filename)
            bot.delete_message(chat_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(f"❌ فشل التحميل. تأكد من أن الرابط ليس لصور أو فيديو خاص.", chat_id, status_msg.message_id)

# --- [5] استقبال الروابط ومعالجتها ---
@bot.message_handler(commands=['start'])
def welcome(message):
    register_user(message)
    bot.reply_to(message, "مرحباً يا بطل! أرسل رابط تيك توك أو تويتر أو يوتيوب (للمشتركين).")

@bot.message_handler(func=lambda m: m.text and m.text.startswith('http'))
def handle_link(message):
    register_user(message)
    url = message.text

    # تنظيف روابط تويتر (X) الغريبة
    if "x.com/i/status/" in url:
        url = url.replace("x.com/i/status/", "x.com/anyuser/status/")
    elif "twitter.com/i/status/" in url:
        url = url.replace("twitter.com/i/status/", "twitter.com/anyuser/status/")

    url_id = str(len(url_storage) + 1)
    url_storage[url_id] = url

    # المنصات المجانية (تيك توك وتويتر)
    if any(p in url for p in ["tiktok.com", "instagram.com", "facebook.com", "x.com", "twitter.com"]):
        start_download(message, "vid", "best", url_id)
    
    # يوتيوب (VIP)
    elif "youtube" in url or "youtu.be" in url:
        if not is_vip(message.from_user.id):
            bot.reply_to(message, "⚠️ يوتيوب متاح لمشتركي VIP فقط.")
            return
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🎬 فيديو", callback_data=f"t|v|{url_id}"),
                   telebot.types.InlineKeyboardButton("🎵 صوت", callback_data=f"t|a|{url_id}"))
        bot.send_message(message.chat.id, "اختر النوع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data.split("|")
    if data[0] == "t":
        f_type, url_id = data[1], data[2]
        if f_type == "v":
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("720p", callback_data=f"q|720|{url_id}"),
                       telebot.types.InlineKeyboardButton("480p", callback_data=f"q|480|{url_id}"))
            bot.edit_message_text("اختر الجودة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        else: start_download(call.message, "aud", "best", url_id)
    elif data[0] == "q":
        res, url_id = data[1], data[2]
        start_download(call.message, "vid", res, url_id)

bot.infinity_polling()

