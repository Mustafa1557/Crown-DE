import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- 1. إعداد السيرفر للعمل على Render ---
app = Flask('')
@app.route('/')
def home():
    return "البوت شغال بأحدث نسخة مستقرة! ✅"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- 2. إعدادات الكوكيز برمجياً (لحل مشكلة الملفات الخارجية) ---
def setup_cookies():
    # كوكيز يوتيوب: ضع النص الذي يبدأ بـ # Netscape هنا
    youtube_content = """
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1743542400	VISITOR_INFO1_LIVE	PASTE_YOUR_YOUTUBE_DATA_HERE
.youtube.com	TRUE	/	TRUE	1743542400	LOGIN_INFO	PASTE_YOUR_YOUTUBE_DATA_HERE
"""
    # كوكيز فيسبوك: ضع النص الذي يبدأ بـ # Netscape هنا
    facebook_content = """
# Netscape HTTP Cookie File
.facebook.com	TRUE	/	TRUE	1743542400	c_user	PASTE_YOUR_FACEBOOK_DATA_HERE
.facebook.com	TRUE	/	TRUE	1743542400	xs	PASTE_YOUR_FACEBOOK_DATA_HERE
"""
    
    with open("youtube_cookies.txt", "w", encoding="utf-8") as f:
        f.write(youtube_content.strip())
    with open("facebook_cookies.txt", "w", encoding="utf-8") as f:
        f.write(facebook_content.strip())
    print("✅ تم توليد ملفات الكوكيز بنجاح داخل السيرفر.")

setup_cookies()

# --- 3. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8168754101 # معرف مصطفى للمراقبة
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    
    if not url.startswith('http'):
        bot.reply_to(message, "أرسل رابطاً صالحاً يا مصطفى! 🔗")
        return

    status_msg = bot.reply_to(message, "⏳ جاري فحص الرابط ومعالجته...")
    
    # تحديد ملف الكوكيز المناسب
    cookie_file = None
    if "youtube" in url or "youtu.be" in url:
        cookie_file = "youtube_cookies.txt"
    elif "facebook" in url or "fb.watch" in url:
        cookie_file = "facebook_cookies.txt"

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'video_{chat_id}.%(ext)s',
        'max_filesize': 48 * 1024 * 1024,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True, # يتجاهل أي خطأ في الكوكيز ويحاول التحميل بدونها
    }

    if cookie_file and os.path.exists(cookie_file):
        ydl_opts['cookiefile'] = cookie_file

    try:
        with YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("📥 جاري تحميل الفيديو...", chat_id, status_msg.message_id)
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("📤 جاري الرفع إلى تلجرام...", chat_id, status_msg.message_id)
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption="✅ تم التحميل بواسطة بوت مصطفى")
            
            if os.path.exists(filename): os.remove(filename)
            bot.delete_message(chat_id, status_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ فشل التحميل.\nتأكد من أن الفيديو عام وحجمه أقل من 50MB.", chat_id, status_msg.message_id)

if __name__ == "__main__":
    print("🚀 البوت انطلق بأحدث نسخة!")
    bot.infinity_polling()
