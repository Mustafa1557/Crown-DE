import http.server
import socketserver
import threading
import os
import telebot
import yt_dlp
import re
import random
from supabase import create_client, Client # استدعاء سوبابيس
from flask import Flask
from threading import Thread

# --- 1. كود إيهام Render بأن البوت عبارة عن موقع ويب (منع النوم) ---
app = Flask('')

@app.route('/')
def home():
    return "🚀 البوت شغال تمام والحمد لله!"

def run():
    # Render بيطلب إن البوت يشتغل على بورت معين هو بيبعته في الـ Environment
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# تشغيل السيرفر الوهمي في الخلفية
keep_alive()

# --- 2. إعدادات الإدارة والبوت وسوبابيس ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8168754101

bot = telebot.TeleBot(TOKEN)
user_data = {} 

# بيانات Supabase
SUPABASE_URL = "https://nrcpotvspxdvxlxbwzto.supabase.co"
SUPABASE_KEY = "حط_الـ_anon_key_حقك_هنا_بين_علامات_التنصيص"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. محرك التحميل المطور لتخطي الحظر مع الكوكيز الذكية ---
class CrownEngine:
    def __init__(self, url, d_type='video'):
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        ]
        
        self.opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'user_agent': random.choice(agents),
            'referer': 'https://www.tiktok.com/',
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'retries': 10,
            'socket_timeout': 30,
            'geo_bypass': True,
            'add_header': [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language: en-US,en;q=0.5',
            ],
        }

        # --- هنا سحر الكوكيز الذكية ---
        # إذا كان الرابط فيسبوك وكان الملف موجود، بنستخدم الكوكيز
        if "facebook.com" in url or "fb.watch" in url:
            if os.path.exists("facebook_cookies.txt"):
                self.opts['cookiefile'] = 'facebook_cookies.txt'
                print("تم استخدام كوكيز فيسبوك بنجاح.")
                
        # إذا كان الرابط تيك توك وكان الملف موجود، بنستخدم الكوكيز
        elif "tiktok.com" in url:
            if os.path.exists("tiktok_cookies.txt"):
                self.opts['cookiefile'] = 'tiktok_cookies.txt'
                print("تم استخدام كوكيز تيك توك بنجاح.")

    def download(self, url):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info) if info else None
        except Exception as e:
            print(f"❌ Download Error: {e}")
            return None

# --- 4. نظام المراقبة ---
def notify_admin(user_info, action_type, detail):
    msg = (f"🔔 **إشعار جديد للمدير**\n\n"
           f"👤 المستخدم: {user_info.first_name}\n"
           f"🆔 الآيدي: `{user_info.id}`\n"
           f"⚙️ الحركة: {action_type}\n"
           f"🔗 الرابط: {detail}")
    try:
        bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
    except:
        pass

# --- 5. معالجة الرسائل بعبارات لينة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    notify_admin(message.from_user, "فتح البوت", "بداية الاستخدام")
    
    welcome_text = (
        f"يا مرحب بيك يا {message.from_user.first_name} في بوت CrownDL 👑\n\n"
        "أنا هنا عشان أخدمك وأنزل ليك الفيديوهات من يوتيوب وتيك توك وفيسبوك بكل سهولة.\n\n"
        "✨ **كل اللي عليك ترسل الرابط وهسي بنجهزه ليك!**"
    )
    bot.send_message(message.chat.id, welcome_text)
    
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    first_name = message.from_user.first_name or "No Name"
    
    try:
        supabase.table('users').insert({
            'user_id': user_id, 
            'username': username,
            'first_name': first_name
        }).execute()
    except Exception as e:
        pass

@bot.message_handler(func=lambda m: True)
def handle_url(message):
    url = message.text
    uid = message.chat.id
    
    if re.match(r'(https?://.+)', url):
        notify_admin(message.from_user, "طلب تحميل", url)
        user_data[uid] = {'url': url}
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🎥 فيديو (MP4)", callback_data="vid"),
            telebot.types.InlineKeyboardButton("🎵 صوت (MP3)", callback_data="aud")
        )
        bot.reply_to(message, "من عيوني! حابب أنزله ليك فيديو ولا صوت؟ 👇", reply_markup=markup)
    else:
        bot.reply_to(message, "يا غالي الرابط ده شكله ما تمام، أتأكد منه وأرسله تاني 🧐")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    url_requested = user_data.get(uid, {}).get('url')
    
    if not url_requested:
        bot.answer_callback_query(call.id, "انتهت جلسة هذا الرابط، أرسله مرة أخرى!")
        return
        
    bot.answer_callback_query(call.id, "جاري التجهيز والتحميل... انتظرني ثواني ⏳")
    
    # تحديد النوع (فيديو أو صوت) بناءً على ضغطة المستخدم
    download_type = 'video' if call.data == "vid" else 'audio'
    
    # استدعاء محرك السحب الذكي بالكوكيز
    engine = CrownEngine(url=url_requested, d_type=download_type)
    file_path = engine.download(url_requested)
    
    if file_path and os.path.exists(file_path):
        bot.send_chat_action(uid, 'upload_video' if download_type == 'video' else 'upload_document')
        
        try:
            with open(file_path, 'rb') as f:
                if download_type == 'video':
                    bot.send_video(uid, f, caption="تم التحميل بواسطة CrownDL 👑")
                else:
                    bot.send_audio(uid, f, caption="تم التحميل بواسطة CrownDL 👑")
                    
            # حذف الملف بعد الإرسال عشان ما يملا السيرفر
            os.remove(file_path)
            
        except Exception as e:
            bot.send_message(uid, f"حصلت مشكلة أثناء إرسال الملف 😢")
            print(f"Error sending file: {e}")
    else:
        bot.send_message(uid, "للأسف ما قدرت أحمل الرابط ده، جرب رابط تاني أو اتأكد من الرابط 🧐")

# --- 6. تشغيل البوت المستمر ---
print("👑 البوت شغال الآن...")
bot.infinity_polling()
