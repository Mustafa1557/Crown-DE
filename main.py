import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- 1. إعداد السيرفر الوهمي (منع النوم) ---
app = Flask('')

@app.route('/')
def home():
    return "البوت شغال بنجاح! 🚀"

def run_flask():
    # ريندر بيحدد الـ Port تلقائياً
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# تشغيل السيرفر في خلفية الكود
threading.Thread(target=run_flask).start()

# --- 2. إعدادات البوت والمراقبة ---
API_TOKEN = os.getenv('BOT_TOKEN')
# نصيحة: حط الآيدي بتاعك هنا عشان تجيك تنبيهات منو بيستخدم البوت
ADMIN_ID = 8168754101

bot = telebot.TeleBot(API_TOKEN)

# --- 3. رسالة الترحيب المعدلة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت التحميل الذكي! 📥\n\n"
        "أرسل لي أي رابط فيديو من:\n"
        "✅ يوتيوب\n✅ فيسبوك\n✅ تيك توك\n✅ إنستغرام\n\n"
        "وسأقوم بتحميله لك فوراً وبأعلى جودة! 🔥"
    )
    bot.reply_to(message, welcome_text)
    
    # إشعار للمالك (اختياري)
    try:
        bot.send_message(ADMIN_ID, f"🔔 مستخدم جديد دخل البوت:\n👤 الاسم: {user_name}\n🆔 الآيدي: {message.from_user.id}")
    except:
        pass

# --- 4. معالجة التحميل (بدون تكرار الرابط) ---
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    
    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح يبدأ بـ http ❌")
        return

    # إشعار للمالك بالتحميل
    try:
        bot.send_message(ADMIN_ID, f"📥 {message.from_user.first_name} يحمل فيديو:\n{url}")
    except:
        pass

    # رسالة الحالة (يتم تعديلها لاحقاً)
    status_msg = bot.reply_to(message, "جاري فحص الرابط... ⏳")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'video_{chat_id}.%(ext)s',
        'max_filesize': 48 * 1024 * 1024, # حد 48 ميجا عشان التلغرام
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # تعديل الرسالة بدل إرسال واحدة جديدة
            bot.edit_message_text("جاري التحميل من المصدر... 📥", chat_id, status_msg.message_id)
            
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("جاري الرفع إلى تلجرام... 📤", chat_id, status_msg.message_id)
            
            with open(filename, 'rb') as video:
                # إرسال الفيديو ومسح رسالة التحميل
                bot.send_video(chat_id, video, caption="تم التحميل بنجاح! ✅")
                bot.delete_message(chat_id, status_msg.message_id)
            
            if os.path.exists(filename):
                os.remove(filename)
            
    except Exception as e:
        error_msg = str(e)
        if "File is too big" in error_msg:
            bot.edit_message_text("❌ عذراً، حجم الفيديو أكبر من المسموح به (50 ميجا).", chat_id, status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ حدث خطأ أثناء المعالجة. تأكد من الرابط.", chat_id, status_msg.message_id)
        
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)

# --- 5. تشغيل البوت مع حل مشكلة الـ Conflict ---
if __name__ == "__main__":
    # مسح أي اتصال قديم فور تشغيل السيرفر
    bot.remove_webhook()
    print("البوت شغال بأفضل إعدادات! 🔥")
    # استخدام infinity_polling لضمان الاستمرارية
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
