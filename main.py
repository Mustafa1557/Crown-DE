import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# 🔑 توكن البوت الخاص بك
TOKEN = "7969192892:AAGv8G2n7jXo8oZlX_Wl_Q" # استبدله بالتوكن حقك لو اتغير
bot = telebot.TeleBot(TOKEN)

# 📂 مجلد التحميلات المؤقت
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🚀 [CrownDL Engine] - النظام قيد التشغيل والعبارات الأصلية الطويلة مفعلة")

# 1️⃣ دالة الترحيب بالعبارات الكاملة الطويلة
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

# 2️⃣ دالة استقبال الروابط وتحليلها (بالعبارات المفصلة)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # رسالة فحص الرابط الطويلة
    checking_msg = bot.reply_to(
        message, 
        "🔍 *جاري فحص الرابط والتأكد من صحته...* \nيرجى الانتظار لحظات قليلة بينما أقوم بالاتصال بالسيرفر."
    )
    
    # التحقق من أن النص عبارة عن رابط
    if not url.startswith(('http://', 'https://')):
        bot.edit_message_text(
            "❌ *خطأ في الرابط!*\nعذراً، يبدو أن النص الذي أرسلته ليس رابطاً صالحاً. يرجى إرسال رابط فيديو صحيح يبدأ بـ http أو https.",
            chat_id=message.chat.id,
            message_id=checking_msg.message_id,
            parse_mode="Markdown"
        )
        return

    # إنشاء الأزرار الشفافة
    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 تحميل كـ فيديو (Video)", callback_data=f"vid|{url}")
    btn_audio = InlineKeyboardButton("🎵 تحميل كـ صوت (Audio MP3)", callback_data=f"aud|{url}")
    markup.add(btn_video, btn_audio)
    
    # تعديل الرسالة وإظهار الخيارات بالعبارة الكاملة
    bot.edit_message_text(
        "🎉 *تم التعرف على الرابط بنجاح!* 🎉\n\nالرجاء اختيار الصيغة التي ترغب في تحميل الملف بها من الخيارات أدناه 👇:",
        chat_id=message.chat.id,
        message_id=checking_msg.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# 3️⃣ دالة معالجة ضغطات الأزرار والتحميل (بالعبارات المفصلة)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, url = call.data.split('|')
    chat_id = call.message.chat.id
    
    # إشعار المستخدم ببدء العملية (العبارة الطويلة)
    status_msg = bot.send_message(
        chat_id, 
        "⏳ *جاري بدء عملية التحميل الآن...* \nقد يستغرق الأمر بعض الوقت اعتماداً على حجم الفيديو وسرعة السيرفر. يرجى عدم إرسال روابط أخرى حتى أنتهي."
    )
    
    # إعدادات yt-dlp
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
            # استخراج معلومات الفيديو والتحميل
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # في حالة الصوت، الامتداد بيتغير لـ mp3
            if action == "aud":
                base, ext = os.path.splitext(file_path)
                file_path = base + ".mp3"
                
            title = info.get('title', 'ملف محمل')
            
            # تحديث الرسالة للإرسال بالعبارات الكاملة
            bot.edit_message_text(
                f"📤 *اكتمل التحميل بنجاح!* \nجاري الآن رفع ملف الـ {media_type} الخاص بك إلى تيليجرام...",
                chat_id=chat_id,
                message_id=status_msg.message_id
            )
            
            # إرسال الملف للتليجرام
            with open(file_path, 'rb') as f:
                if action == "vid":
                    bot.send_video(chat_id, f, caption=f"👑 تم التحميل بواسطة بوت CrownDL\n📌 العنوان: {title}")
                else:
                    bot.send_audio(chat_id, f, caption=f"👑 تم التحميل بواسطة بوت CrownDL\n📌 العنوان: {title}")
                    
            # حذف الملف بعد الإرسال لتوفير مساحة السيرفر
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # حذف رسالة الحالات المؤقتة
            bot.delete_message(chat_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(
            f"❌ *عذراً، حدث خطأ أثناء التحميل!*\n\nتأكد من أن الرابط يعمل بشكل صحيح، أو أن حجم الملف لا يتعدى حدود الرفع المسموحة (50 ميجابايت).\n\n_تفاصيل الخطأ: {str(e)[:100]}_",
            chat_id=chat_id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

# تشغيل البوت
bot.infinity_polling()
