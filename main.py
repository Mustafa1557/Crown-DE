import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- إعداد سيرفر وهمي لمنع النوم ---
app = Flask('')

@app.route('/')
def home():
    return "البوت شغال بنجاح! 🚀"

def run_flask():
    # ريندر بيحدد الـ Port تلقائياً في متغير البيئة
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# تشغيل السيرفر في "خيط" (Thread) منفصل عشان ما يعطل البوت
t = threading.Thread(target=run_flask)
t.start()

# --- إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً يا مصطفى! أرسل رابط الفيديو (يوتيوب، فيس، تيك توك) وححمله ليك فوراً. 📥")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح! ❌")
        return
        
    sent_msg = bot.reply_to(message, "جاري المعالجة... انتظر قليلاً ⏳")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video_%(id)s.%(ext)s',
        'max_filesize': 48 * 1024 * 1024,
        'quiet': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="تم التحميل بنجاح! ✅")
            
            os.remove(filename)
            bot.delete_message(message.chat.id, sent_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"خطأ: {str(e)}", message.chat.id, sent_msg.message_id)
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

print("البوت والسيرفر شغالين الآن! 🔥")
bot.polling(none_stop=True)
