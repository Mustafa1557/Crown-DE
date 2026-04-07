import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- 1. إعداد السيرفر الوهمي (منع النوم) ---
app = Flask('')
@app.route('/')
def home():
    return "البوت شغال بأفضل إعدادات! 🚀"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8168754101 # آيدي مصطفى للمراقبة
bot = telebot.TeleBot(API_TOKEN)

# --- 3. معالجة التحميل الذكي ---
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    user = message.from_user

    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح! ❌")
        return

    # إشعار للمالك (مصطفى) فيه تفاصيل المستخدم والحالة
    status_info = "متصل ✅"
    log_msg = (
        f"📥 محاولة تحميل جديدة:\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🆔 الآيدي: {user.id}\n"
        f"🌐 اللغة: {user.language_code}\n"
        f"📡 الحالة: {status_info}\n"
        f"🔗 الرابط: {url}"
    )
    try:
        bot.send_message(ADMIN_ID, log_msg)
    except:
        pass

    status_msg = bot.reply_to(message, "جاري فحص الرابط وتطبيق الكوكيز... ⏳")
    
    # تحديد ملف الكوكيز بناءً على الموقع
    cookie_file = None
    if "youtube.com" in url or "youtu.be" in url:
        cookie_file = "youtube_cookies.txt"
    elif "tiktok.com" in url:
        cookie_file = "tiktok_cookies.txt"
    elif "facebook.com" in url or "fb.watch" in url:
        cookie_file = "facebook_cookies.txt"

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'video_{chat_id}.%(ext)s',
        'max_filesize': 48 * 1024 * 1024, # حد التلغرام 48 ميجا
        'quiet': True,
        'no_warnings': True,
    }

    # تفعيل الكوكيز إذا كان الملف موجوداً
    if cookie_file and os.path.exists(cookie_file):
        ydl_opts['cookiefile'] = cookie_file

    try:
        with YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("جاري استخراج الفيديو بأعلى جودة... 📥", chat_id, status_msg.message_id)
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("جاري الرفع إلى تلجرام... 📤", chat_id, status_msg.message_id)
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption="✅ تم التحميل بنجاح!")
                bot.delete_message(chat_id, status_msg.message_id)
            
            if os.path.exists(filename): os.remove(filename)
            
    except Exception as e:
        error_text = "❌ حدث خطأ: قد يكون حجم الفيديو كبيراً جداً أو الرابط غير مدعوم."
        bot.edit_message_text(error_text, chat_id, status_msg.message_id)
        if 'filename' in locals() and os.path.exists(filename): os.remove(filename)

# --- 4. تشغيل البوت ---
if __name__ == "__main__":
    bot.remove_webhook()
    print("البوت شغال وجاهز بكل الكوكيز! 🔥")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
