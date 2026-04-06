import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- إعداد السيرفر الوهمي (منع النوم) ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is active! 🚀"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- إعدادات البوت والمراقبة ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = "123456789" # حط الآيدي بتاعك هنا للمراقبة
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً مصطفى! أرسل رابط الفيديو وسأقوم بتحميله لك فوراً. 📥")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    user = message.from_user
    
    if not url.startswith('http'):
        bot.reply_to(message, "يا حبوب، أرسل رابط صحيح ❌")
        return

    # إشعار للمالك (اختياري)
    try:
        bot.send_message(ADMIN_ID, f"📥 {user.first_name} يحمل: {url}")
    except:
        pass
        
    # رسالة الحالة الأولية
    sent_msg = bot.reply_to(message, "جاري معالجة الرابط... ⏳")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'video_{user.id}.%(ext)s',
        'max_filesize': 48 * 1024 * 1024,
        'quiet': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # تحديث الرسالة لـ "جاري التحميل"
            bot.edit_message_text("جاري تحميل الفيديو من السيرفر... 📥", message.chat.id, sent_msg.message_id)
            
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تحديث الرسالة لـ "جاري الرفع"
            bot.edit_message_text("جاري رفع الفيديو للتليجرام... 📤", message.chat.id, sent_msg.message_id)
            
            with open(filename, 'rb') as video:
                # إرسال الفيديو وحذف رسالة "جاري الرفع"
                bot.send_video(message.chat.id, video, caption="تم التحميل بنجاح! ✅")
                bot.delete_message(message.chat.id, sent_msg.message_id)
            
            os.remove(filename)
            
    except Exception as e:
        error_text = str(e)
        if "File is too big" in error_text:
            bot.edit_message_text("عذراً، الفيديو حجمه أكبر من 50 ميجا (حد تليجرام). ❌", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text(f"حصل خطأ: {error_text[:100]}", message.chat.id, sent_msg.message_id)
        
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

print("البوت شغال بأفضل إعدادات! 🔥")
bot.polling(none_stop=True)
