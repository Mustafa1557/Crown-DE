import os
import telebot
from telebot import types
import yt_dlp
from flask import Flask
import threading

# إعدادات Flask عشان السيرفر يفضل شغال في Render
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# حط التوكن بتاعك هنا
BOT_TOKEN = "7902181711:AAGyv09Y97K_g52I0uG13DAr7l6hP8G8F5U"
bot = telebot.TeleBot(BOT_TOKEN)

# دالة لتحميل الفيديوهات بدون كوكيز
def download_video(url, chat_id):
    # رسالة جاري التحميل
    msg = bot.send_message(chat_id, "⏳ جاري محاولة تحميل الفيديو، يرجى الانتظار...")
    
    # إعدادات yt-dlp بدون كوكيز
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # إرسال الفيديو للمستخدم
            bot.send_message(chat_id, "📤 جاري إرسال الفيديو...")
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video)
                
            # مسح الملف بعد الإرسال لتوفير المساحة
            os.remove(filename)
            bot.delete_message(chat_id, msg.message_id)
            bot.send_message(chat_id, "✅ تم التحميل بنجاح!")
            
    except Exception as e:
        bot.delete_message(chat_id, msg.message_id)
        # إرسال رسالة الخطأ للمستخدم عشان نعرف المشكلة من وين
        bot.send_message(chat_id, f"❌ فشل التحميل. السبب:\n{str(e)}")

# استقبال الروابط
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "youtube.com" in url or "youtu.be" in url or "tiktok.com" in url or "facebook.com" in url:
        # تشغيل التحميل في Thread منفصل عشان البوت ما يهنجش
        threading.Thread(target=download_video, args=(url, message.chat.id)).start()
    else:
        bot.send_message(message.chat.id, "⚠️ يرجى إرسال رابط صالح من (يوتيوب، تيك توك، أو فيسبوك)")

if __name__ == '__main__':
    keep_alive()
    print("البوت بدأ العمل الان بدون كوكيز... 🤖")
    bot.infinity_polling()
