import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- 1. إعداد السيرفر الوهمي ---
app = Flask('')
@app.route('/')
def home():
    return "البوت مستقر وشغال بنظام الفحص الذكي! 🚀"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8168754101 
bot = telebot.TeleBot(API_TOKEN)

# --- 3. دالة فحص ملف الكوكيز (لضمان عدم توقف البوت) ---
def get_valid_cookie_file(url):
    cookie_file = None
    if "youtube.com" in url or "youtu.be" in url:
        cookie_file = "youtube_cookies.txt"
    elif "tiktok.com" in url:
        cookie_file = "tiktok_cookies.txt"
    elif "facebook.com" in url or "fb.watch" in url:
        cookie_file = "facebook_cookies.txt"
    
    # التأكد من وجود الملف وصحة صيغته (Netscape)
    if cookie_file and os.path.exists(cookie_file):
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if "# Netscape" in first_line:
                    return cookie_file
                else:
                    print(f"⚠️ تحذير: ملف {cookie_file} بصيغة JSON وغلط، تم تجاهله.")
        except Exception:
            pass
    return None

# --- 4. معالجة التحميل ---
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    user = message.from_user

    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح! ❌")
        return

    # إشعار المراقبة لمصطفى
    log_msg = (
        f"📥 طلب جديد:\n👤 {user.first_name}\n🆔 {user.id}\n🔗 {url}\n"
        f"📡 الحالة: متصل ✅"
    )
    try: bot.send_message(ADMIN_ID, log_msg)
    except: pass

    status_msg = bot.reply_to(message, "جاري فحص الرابط وتجهيز الملفات... ⏳")
    
    # اختيار الملف الصحيح فقط
    valid_cookies = get_valid_cookie_file(url)

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'video_{chat_id}.%(ext)s',
        'max_filesize': 48 * 1024 * 1024,
        'quiet': True,
        'no_warnings': True,
    }

    if valid_cookies:
        ydl_opts['cookiefile'] = valid_cookies
        print(f"✅ يتم استخدام الكوكيز: {valid_cookies}")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("جاري استخراج الفيديو... 📥", chat_id, status_msg.message_id)
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("جاري الرفع... 📤", chat_id, status_msg.message_id)
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption="✅ تم التحميل بنجاح!")
                bot.delete_message(chat_id, status_msg.message_id)
            
            if os.path.exists(filename): os.remove(filename)
            
    except Exception as e:
        error_msg = f"❌ فشل التحميل. قد يكون الحجم كبيراً أو الرابط محمي.\n(التفاصيل: {str(e)[:50]}...)"
        bot.edit_message_text(error_msg, chat_id, status_msg.message_id)
        if 'filename' in locals() and os.path.exists(filename): os.remove(filename)

# --- 5. التشغيل ---
if __name__ == "__main__":
    bot.remove_webhook()
    print("البوت شغال بنظام الحماية من أخطاء الكوكيز! 🔥")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
