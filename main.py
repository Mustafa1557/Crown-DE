import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from flask import Flask
from threading import Thread

# 1️⃣ إعداد سيرفر Flask الوهمي لخدعة Render
app = Flask(__name__)

@app.route('/')
def home():
    return "CrownDL Bot is Running Successfully! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# 🔑 توكن البوت الخاص بك
TOKEN = "7969192892:AAGv8G2n7jXo8oZlX_Wl_Q" 
bot = telebot.TeleBot(TOKEN)

# 📂 مجلد التحميلات المؤقت
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🚀 [CrownDL Engine] - نظام قوائم التشغيل مفعل")

# 2️⃣ دالة الترحيب
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👑 *مرحباً بك في بوت CrownDL المتقدم!* 👑\n\n"
        "أنا هنا لمساعدتك في تحميل الفيديوهات، الصوتيات، وقوائم التشغيل من مختلف المنصات.\n\n"
        "💡 *طريقة الاستخدام:* \n"
        "انسخ رابط الفيديو أو قائمة التشغيل وأرسله لي هنا في الشات! 🚀"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# 3️⃣ دالة استقبال الروابط
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    checking_msg = bot.reply_to(
        message, 
        "🔍 *جاري فحص الرابط...* \nيرجى الانتظار لحظات."
    )
    
    if not url.startswith(('http://', 'https://')):
        bot.edit_message_text(
            "❌ *خطأ في الرابط!*\nيرجى إرسال رابط صحيح يبدأ بـ http أو https.",
            chat_id=message.chat.id,
            message_id=checking_msg.message_id,
            parse_mode="Markdown"
        )
        return

    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 تحميل كـ فيديو (Video)", callback_data=f"vid|{url}")
    btn_audio = InlineKeyboardButton("🎵 تحميل كـ صوت (Audio MP3)", callback_data=f"aud|{url}")
    markup.add(btn_video, btn_audio)
    
    bot.edit_message_text(
        "🎉 *تم التعرف على الرابط بنجاح!* \n\nالرجاء اختيار الصيغة التي ترغب في تحميل الملف بها من الخيارات أدناه 👇:",
        chat_id=message.chat.id,
        message_id=checking_msg.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 4️⃣ دالة معالجة ضغطات الأزرار والتحميل
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, url = call.data.split('|')
    chat_id = call.message.chat.id
    
    status_msg = bot.send_message(
        chat_id, 
        "⏳ *جاري بدء العملية...* \nإذا أرسلت قائمة تشغيل، سيتم تحميل الفيديوهات واحداً تلو الآخر."
    )
    
    # إعدادات yt-dlp العامة
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'max_filesize': 50 * 1024 * 1024, # حجم الملف لا يتعدى 50 ميجا
        'playlist_items': '1-5', # ⚠️ أقصى حد 5 فيديوهات من القائمة عشان السيرفر ما يعلق
    }
    
    if action == "vid":
        ydl_opts['format'] = 'best'
        media_type = "فيديو"
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        media_type = "صوت"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # استخراج المعلومات (سواء كان فيديو أو قائمة)
            info = ydl.extract_info(url, download=False)
            
            # فحص هل الرابط لقائمة تشغيل؟
            if 'entries' in info:
                total_videos = len(info['entries'])
                bot.edit_message_text(
                    f"📂 *تم اكتشاف قائمة تشغيل!* \nجاري تحميل أول 5 فيديوهات من أصل {total_videos}...",
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    parse_mode="Markdown"
                )
                
                # تحميل الفيديوهات في القائمة واحد واحد
                for entry in info['entries']:
                    if entry is None:
                        continue
                    
                    # تحميل الفيديو الحالي
                    entry_info = ydl.extract_info(entry['webpage_url'], download=True)
                    file_path = ydl.prepare_filename(entry_info)
                    
                    if action == "aud":
                        base, ext = os.path.splitext(file_path)
                        file_path = base + ".mp3"
                    
                    title = entry_info.get('title', 'ملف محمل')
                    
                    # رفع الملف للتليجرام
                    with open(file_path, 'rb') as f:
                        if action == "vid":
                            bot.send_video(chat_id, f, caption=f"👑 CrownDL (قائمة) | {title}")
                        else:
                            bot.send_audio(chat_id, f, caption=f"👑 CrownDL (قائمة) | {title}")
                    
                    # حذفه مباشرة لتوفير المساحة
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # حذف رسالة الحالة بعد الانتهاء
                bot.delete_message(chat_id, status_msg.message_id)
                bot.send_message(chat_id, "✅ *اكتمل تحميل قائمة التشغيل بنجاح!*", parse_mode="Markdown")
                
            else:
                # لو طلع فيديو واحد عادي مش قائمة
                bot.edit_message_text(
                    f"📤 *اكتمل التحميل!* \nجاري رفع الـ {media_type} الخاص بك إلى تيليجرام...",
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    parse_mode="Markdown"
                )
                
                # تحميل ورفع الفيديو الفردي
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
                if action == "aud":
                    base, ext = os.path.splitext(file_path)
                    file_path = base + ".mp3"
                
                title = info.get('title', 'ملف محمل')
                
                with open(file_path, 'rb') as f:
                    if action == "vid":
                        bot.send_video(chat_id, f, caption=f"👑 CrownDL | {title}")
                    else:
                        bot.send_audio(chat_id, f, caption=f"👑 CrownDL | {title}")
                        
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                bot.delete_message(chat_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(
            chat_id,
            f"❌ *عذراً، حدث خطأ!* \nتأكد من الرابط أو أن حجم الملف مناسب.",
            parse_mode="Markdown"
        )

# 5️⃣ تشغيل السيرفر الوهمي والبوت معاً
if __name__ == "__main__":
    server_thread = Thread(target=run_flask)
    server_thread.start()
    
    print("🤖 البوت شغال الآن ومستعد لاستقبال الروابط...")
    bot.infinity_polling()
