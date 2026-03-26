import http.server
import socketserver
import threading
import os

# كود عشان Render يفتكر إن البوت "موقع" ويشغله مجاناً
def run_static_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_static_server, daemon=True).start()

# --- هنا يبدأ كود البوت القديم بتاعك ---
import telebot
# ... باقي الكود ...




import telebot
import yt_dlp
import os
import re

# 1. الإعدادات والتوكن (تأكد من حمايته لاحقاً)
TOKEN = "8283078572:AAH50vJAbO4ASd48jJx1TrjGlSmYk4_WQUU"
bot = telebot.TeleBot(TOKEN)

# مخزن بيانات مؤقت للمستخدمين
user_data = {} 

# 2. كلاس المحرك (The Engine) المسؤول عن التحميل
class CrownEngine:
    def __init__(self, d_type='video'):
        self.d_type = d_type
        # إعدادات متوافقة مع أغلب السيرفرات (Koyeb, Render, Railway)
        self.opts = {
            'format': 'bestaudio/best' if d_type == 'audio' else 'bestvideo+bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4' if d_type == 'video' else None,
            # إضافة خيار لجعل التحميل متوافق مع قيود بعض المواقع
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'addmetadata': True,
        }

    def download(self, url):
        try:
            # التأكد من وجود مجلد التحميلات
            if not os.path.exists('downloads'): 
                os.makedirs('downloads')
            
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"❌ Error in Download: {e}")
            return None

# 3. دالة التحقق من الروابط (Regex)
def is_valid_url(url):
    # يدعم: يوتيوب، تيك توك، فيسبوك، إنستغرام، وتويتر (X)
    pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be|tiktok\.com|facebook\.com|instagram\.com|twitter\.com|x\.com)/.+'
    return re.match(pattern, url)

# 4. معالجة الأوامر والرسائل
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    if uid not in user_data: 
        user_data[uid] = {'count': 0, 'last_url': ''}
    
    welcome_text = (
        "👑 **مرحباً بك في بوت CrownDL**\n\n"
        "أنا بوت تحميل من يوتيوب، تيك توك، وغيرها..\n"
        f"📊 فيديوهاتك المحملة حتى الآن: {user_data[uid]['count']}\n\n"
        "🚀 **أرسل لي أي رابط لبدء التحميل!**"
    )
    bot.send_message(uid, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_incoming_url(message):
    uid = message.chat.id
    url = message.text
    
    if is_valid_url(url):
        # حفظ الرابط الأخير للمستخدم
        if uid not in user_data: 
            user_data[uid] = {'count': 0, 'last_url': ''}
        user_data[uid]['last_url'] = url
        
        # إنشاء أزرار الاختيار
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("فيديو 🎬 (MP4)", callback_data="vid"),
            telebot.types.InlineKeyboardButton("موسيقى 🎵 (MP3)", callback_data="aud")
        )
        bot.reply_to(message, "⚙️ **اختر الصيغة المطلوبة:**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ الرابط غير مدعوم أو غير صحيح، يرجى التأكد من الرابط.")

# 5. معالجة ضغطات الأزرار (التحميل والإرسال)
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    url = user_data.get(uid, {}).get('last_url')
    
    if not url:
        bot.send_message(uid, "❌ انتهت الجلسة، الرجاء إرسال الرابط مرة أخرى.")
        return

    # تحديث الرسالة لإشعار المستخدم بالبدء
    bot.edit_message_text("⏳ جاري المعالجة والتحميل... قد يستغرق ذلك دقيقة.", uid, call.message.message_id)
    
    # اختيار النوع بناءً على الزر
    file_type = 'audio' if call.data == 'aud' else 'video'
    engine = CrownEngine(file_type)
    file_path = engine.download(url)
    
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                if file_type == 'audio':
                    bot.send_audio(uid, f, caption="تم التحميل بواسطة @CrownDL_bot 👑")
                else:
                    bot.send_video(uid, f, caption="تم التحميل بواسطة @CrownDL_bot 👑")
            
            # تحديث العداد
            user_data[uid]['count'] += 1
        except Exception as e:
            bot.send_message(uid, f"❌ فشل إرسال الملف: {e}")
        finally:
            # حذف الملف فوراً للحفاظ على مساحة السيرفر
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        bot.send_message(uid, "❌ عذراً، لم نتمكن من تحميل هذا الفيديو. تأكد من أن الرابط يعمل بشكل عام.")

# تشغيل البوت
if __name__ == "__main__":
    print("✅ CrownDL V2 is firing up...")
    bot.infinity_polling()
