import telebot
import os
import random
import datetime
from yt_dlp import YoutubeDL
from supabase import create_client

# --- [1] قراءة البيانات من متغيرات البيئة (Render) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# محاولة قراءة ADMIN_ID وتحويله لرقم، لو فشل نضع القيمة 0
try:
    ADMIN_ID = int(os.getenv("MY_ID") or 0)
except:
    ADMIN_ID = 0

# تشغيل البوت والاتصال بسوبابيس
bot = telebot.TeleBot(BOT_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
url_storage = {} 

# --- [2] نظام الرسائل الجماعية (Broadcaster) ---
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    # حماية: المطور فقط
    if message.from_user.id != ADMIN_ID:
        return

    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        bot.reply_to(message, "⚠️ اكتب الرسالة بعد الأمر.")
        return

    try:
        users = supabase.table("users").select("user_id").execute()
        count = 0
        for user in users.data:
            try:
                bot.send_message(user['user_id'], text_to_send)
                count += 1
            except:
                continue 
        bot.reply_to(message, f"✅ تم الإرسال إلى {count} مستخدم.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

# --- [3] دوال قاعدة البيانات ---
def register_user(message):
    user_data = {
        "user_id": str(message.from_user.id),
        "username": message.from_user.username or "Unknown",
        "first_name": message.from_user.first_name or "User"
    }
    try:
        supabase.table("users").upsert(user_data, on_conflict="user_id").execute()
    except Exception as e:
        print(f"Database Error: {e}")

def is_vip(user_id):
    try:
        res = supabase.table("users").select("is_vip, subscription_end").eq("user_id", str(user_id)).execute()
        if res.data:
            user = res.data[0]
            if user['is_vip']:
                if user['subscription_end']:
                    expiry = datetime.datetime.fromisoformat(user['subscription_end'].replace('Z', '+00:00'))
                    if datetime.datetime.now(datetime.timezone.utc) < expiry:
                        return True
                    else:
                        supabase.table("users").update({"is_vip": False}).eq("user_id", str(user_id)).execute()
                else:
                    return True 
        return False
    except:
        return False

# --- [4] نظام الكوكيز ---
def get_cookie_for_url(url):
    if "youtube" in url or "youtu.be" in url:
        return random.choice(["youtube_cookies_1.txt", "youtube_cookies_2.txt"])
    elif "instagram.com" in url:
        return "ig_cookies.txt"
    elif "x.com" in url or "twitter.com" in url:
        return "x_cookies.txt"
    elif "facebook.com" in url or "fb.watch" in url:
        return "fb_cookies.txt"
    return None

# --- [5] دالة التحميل ---
def start_download(message, f_type, res, url_id, is_direct=False):
    chat_id = message.chat.id
    url = url_storage.get(url_id)
    status_msg = bot.send_message(chat_id, "⏳ جاري المعالجة...")
    cookie = get_cookie_for_url(url)
    
    if "youtube" in url or "youtu.be" in url:
        fmt = f"best[height<={res}][ext=mp4]/best[ext=mp4]/best"
    else:
        fmt = "bestvideo+bestaudio/best"

    opts = {
        'format': fmt,
        'outtmpl': f'file_{chat_id}_{url_id}.%(ext)s',
        'cookiefile': cookie,
        'nocheckcertificate': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
                if f_type == "vid": bot.send_video(chat_id, f)
                else: bot.send_audio(chat_id, f)
            
            os.remove(filename)
            bot.delete_message(chat_id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ فشل التحميل.", chat_id, status_msg.message_id)

# --- [6] معالجة الروابط ---
@bot.message_handler(commands=['start'])
def welcome(message):
    register_user(message)
    bot.reply_to(message, "أهلاً بك!\nالتحميل من تيك توك وإنستغرام مجاني.\nيوتيوب للـ VIP فقط.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith('http'))
def handle_link(message):
    register_user(message)
    url = message.text
    url_id = str(len(url_storage) + 1)
    url_storage[url_id] = url

    if any(p in url for p in ["tiktok.com", "instagram.com", "facebook.com", "x.com", "twitter.com"]):
        start_download(message, "vid", "best", url_id, is_direct=True)
    elif "youtube" in url or "youtu.be" in url:
        if not is_vip(message.from_user.id):
            bot.reply_to(message, "⚠️ يوتيوب متاح للـ VIP فقط.")
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
            bot.send_message(call.message.chat.id, "اختر الجودة:", reply_markup=markup)
        else:
            start_download(call.message, "aud", "best", url_id)
    elif data[0] == "q":
        res, url_id = data[1], data[2]
        start_download(call.message, "vid", res, url_id)

if __name__ == "__main__":
    bot.infinity_polling()
