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
    # Render بيدينا بورت (Port) تلقائي لازم نستخدمه
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# 🔑 توكن البوت الخاص بك
TOKEN = "7969192892:AAGv8G2n7jXo8oZlX_Wl_Q" 
bot = telebot.TeleBot(TOKEN)

# 📂 مجلد التحميلات المؤقت
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🚀 [CrownDL Engine] - النظام قيد التشغيل والعبارات الأصلية الطويلة مفعلة")

# 2️⃣ دالة الترحيب بالعبارات الكاملة الطويلة
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👑 *مرحباً بك في بوت CrownDL المتقدم!* 👑\n\n"
        "أنا هنا لمساعدتك في تحميل الفيديوهات والصوتيات من مختلف المنصات "
        "بأعلى جودة ممكنة وبكل سهولة.\n\n"
        "🌐 *المنصات المدعومة حالياً:* \n"
        "• YouTube 🎥\n"
        "• TikTok 🎵\n"
        "• Facebook 👥\n"
        "• Instagram 📸\n"
        "• Twitter / X 🐦\n\n"
        "💡 *طريقة الاستخدام:* \n"
        "بكل بساطة، قم بنسخ رابط الفيديو من أي منصة وأرسله لي هنا في الشات، "
        "وسأقوم بالباقي من أجلك! 🚀"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# 3️⃣ دالة استقبال الروابط وتحليلها (بالعبارات المفصلة)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    checking_msg = bot.reply_to(
        message, 
        "🔍 *جاري فحص الرابط والتأكد من صحته...* \nيرجى الانتظار لحظات قليلة بينما أقوم بالاتصال بالسيرفر."
    )
    
    if not url.startswith(('http://', 'https://')):
        bot.edit_message_text(
            "❌ *خطأ في الرابط!*\nعذراً، يبدو أن النص الذي أرسلته ليس رابطاً صالحاً. يرجى إرسال رابط فيديو صحيح يبدأ بـ http أو https.",
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
        "🎉 *تم التعرف على الرابط بنجاح!* 🎉\n\nالرجاء اختيار الصيغة التي ترغب في تحميل الملف بها من الخيارات أدناه 👇:",
        chat_id=message.chat.id,
        message_id=checking_msg.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 4️⃣ دالة معالجة ضغطات الأزرار والتحميل (بالعبارات المفصلة)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, url = call.data.split('|')
    chat_id = call.message.chat.id
    
    status_msg = bot.send_message(
        chat_id, 
        "⏳ *جاري بدء عملية التحميل الآن...* \nقد يستغرق الأمر بعض الوقت اعتماداً على حجم الفيديو وسرعة السيرفر. يرجى عدم إرسال روابط أخرى حتى أنتهي."
    )
    
    if action == "vid":
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'max_filesize': 50 * 1024 * 1024
        }
        media_type = "فيديو"
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'max_filesize': 50 * 1024 * 1024
        }
        media_type = "صوت"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            if action == "aud":
                base, ext = os.path.splitext(file_path)
                file_path = base + ".mp3"
                
            title = info.get('title', 'ملف محمل')
            
            bot.edit_message_text(
                f"📤 *اكتمل التحميل بنجاح!* \nجاري الآن رفع ملف الـ {media_type} الخاص بك إلى تيليجرام...",
                chat_id=chat_id,
                message_id=status_msg.message_id
            )
            
            with open(file_path, 'rb') as f:
                if action == "vid":
                    bot.send_video(chat_id, f, caption=f"👑 تم التحميل بواسطة بوت CrownDL\n📌 العنوان: {title}")
                else:
                    bot.send_audio(chat_id, f, caption=f"👑 تم التحميل بواسطة بوت CrownDL\n📌 العنوان: {title}")
                    
            if os.path.exists(file_path):
                os.remove(file_path)
                
            bot.delete_message(chat_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(
            f"❌ *عذراً، حدث خطأ أثناء التحميل!*\n\nتأكد من أن الرابط يعمل بشكل صحيح، أو أن حجم الملف لا يتعدى حدود الرفع المسموحة (50 ميجابايت).",
            chat_id=chat_id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

# 5️⃣ تشغيل السيرفر الوهمي والبوت معاً
if __name__ == "__main__":
    # تشغيل Flask في سطر منفصل (Thread)
    server_thread = Thread(target=run_flask)
    server_thread.start()
    
    # تشغيل البوت
    print("🤖 البوت شغال الآن في الخلفية ومستعد لاستقبال الروابط...")
    bot.infinity_polling()
