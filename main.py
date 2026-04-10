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
def home(): return "Bot is alive!"
def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask).start()

# --- [1] إعدادات البوت وقاعدة البيانات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
bot = telebot.TeleBot(BOT_TOKEN)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
url_storage = {} 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- [2] نظام الكوكيز ---
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
        if os.path.exists(full_path): return full_path
    return None

# --- [3] دالة التحميل (تعديل جذري للأخطاء) ---
def start_download(message, f_type, res, url_id):
    chat_id = message.chat.id
    url = url_storage.get(url_id)
    status_msg = bot.send_message(chat_id, "⏳ جاري استخراج الفيديو... انتظر قليلاً")
    cookie = get_cookie_for_url(url)
    
    opts = {
        'format': 'bestvideo+bestaudio/best' if f_type == 'vid' else 'bestaudio/best',
        'outtmpl': os.path.join(BASE_DIR, f'file_{chat_id}_{url_id}.%(ext)s'),
        'cookiefile': cookie,
        'nocheckcertificate': True,
        'quiet': False, # خليناه False عشان نشوف الخطأ في اللوج
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'add_header': [
            'Accept-Language: ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer: https://www.google.com/'
        ],
        'extractor_args': {'tiktok': {'webpage_download': True}} # حل لمشكلة تيك توك
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
                    bot.send_video(chat_id, f, caption="تم التحميل بواسطة بوتك 🚀")
                else:
                    bot.send_audio(chat_id, f)
            
            if os.path.exists(filename): os.remove(filename)
            bot.delete_message(chat_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Detailed Error: {e}")
        bot.edit_message_text(f"❌ فشل السيرفر في الوصول للفيديو.\nالسبب المحتمل: حماية المنصة (تيك توك/تويتر).\n\nجرب إرسال الرابط مرة أخرى بعد دقيقة.", chat_id, status_msg.message_id)

# --- [4] استقبال الروابط ومعالجتها ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith('http'))
def handle_link(message):
    url = message.text
    # تحويل روابط تويتر الغريبة
    if "/i/status/" in url:
        url = url.replace("/i/status/", "/user/status/")
    
    url_id = str(len(url_storage) + 1)
    url_storage[url_id] = url

    if any(p in url for p in ["tiktok.com", "x.com", "twitter.com", "instagram.com", "facebook.com"]):
        start_download(message, "vid", "best", url_id)
    elif "youtube" in url or "youtu.be" in url:
        # هنا ضيف شرط الـ VIP حقك
        start_download(message, "vid", "720", url_id)

if __name__ == "__main__":
    bot.infinity_polling()
