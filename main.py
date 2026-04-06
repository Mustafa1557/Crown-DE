import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- إعداد السيرفر الوهمي (منع النوم) ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- إعدادات البوت والمراقبة ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8168754101
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    welcome_text = f"أهلاً {user.first_name}! أرسل رابط الفيديو وسأقوم بتحميله لك. 📥"
    bot.reply_to(message, welcome_text)
    
    # إشعار للمالك بدخول مستخدم جديد
    log_msg = f"🔔 مستخدم جديد دخل البوت:\n👤 الاسم: {user.first_name}\n🆔 الآيدي: {user.id}\n🔗 اليوزر: @{user.username}"
    bot.send_message(ADMIN_ID, log_msg)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    user = message.from_user
    
    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح! ❌")
        return
        
    # إشعار للمالك بوجود عملية تحميل
    bot.send_message(ADMIN_ID, f"📥 {user.first_name} يحاول تحميل فيديو:\n{url}")
    
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
                bot.send_video(message.chat.id, video, caption=f"تم التحميل بنجاح! ✅\nبواسطة: @{bot.get_me().username}")
            
            os.remove(filename)
            bot.delete_message(message.chat.id, sent_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"خطأ: {str(e)}", message.chat.id, sent_msg.message_id)
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

print("البوت والمراقبة شغالين! 🔥")
bot.polling(none_stop=True)
