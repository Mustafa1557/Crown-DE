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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- 2. إعدادات الإدارة والبوت وسوبابيس ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8168754101

bot = telebot.TeleBot(TOKEN)
user_data = {} 

SUPABASE_URL = "https://nrcpotvspxdvxlxbwzto.supabase.co"
SUPABASE_KEY = "حط_الـ_anon_key_حقك_هنا_بين_علامات_التنصيص"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. محرك التحميل المطور (مفصل لكل موقع) ---
class CrownEngine:
    def __init__(self):
        # يوزرات عشوائية عشان نخدع المواقع
        self.agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        ]

    # 🔴 كود خاص بسحب اليوتيوب
    def download_youtube(self, url, d_type):
        opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/yt_%(title)s.%(ext)s',
            'user_agent': random.choice(self.agents),
            'nocheckcertificate': True,
            'quiet': True,
        }
        # هنا بعدين لما تعمل ملف كوكيز لليوتيوب حتضيف السطر ده بس:
        # if os.path.exists("youtube_cookies.txt"): opts['cookiefile'] = 'youtube_cookies.txt'
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"❌ YouTube Error: {e}")
            return None

    # 🔵 كود خاص بسحب الفيسبوك
    def download_facebook(self, url, d_type):
        opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/fb_%(title)s.%(ext)s',
            'user_agent': random.choice(self.agents),
            'nocheckcertificate': True,
            'quiet': True,
        }
        # هنا بنشغل كوكيز الفيس لو كانت موجودة بصيغة Netscape المظبوطة
        if os.path.exists("facebook_cookies.txt"):
            opts['cookiefile'] = 'facebook_cookies.txt'
            
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"❌ Facebook Error: {e}")
            return None

    # ⚫ كود خاص بسحب التيك توك
    def download_tiktok(self, url, d_type):
        opts = {
            'format': 'best[ext=mp4]/best' if d_type == 'video' else 'bestaudio/best',
            'outtmpl': '/tmp/tt_%(title)s.%(ext)s',
            'referer': 'https://www.tiktok.com/',
            'user_agent': random.choice(self.agents),
            'nocheckcertificate': True,
            'quiet': True,
        }
        # هنا بنشغل كوكيز التيك توك لو كانت موجودة بصيغة Netscape المظبوطة
        if os.path.exists("tiktok_cookies.txt"):
            opts['cookiefile'] = 'tiktok_cookies.txt'
            
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"❌ TikTok Error: {e}")
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

# --- 5. معالجة الرسائل ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    notify_admin(message.from_user, "فتح البوت", "بداية الاستخدام")
    
    welcome_text = (
        f"يا مرحب بيك يا {message.from_user.first_name} في بوت CrownDL 👑\n\n"
        "أنا هنا عشان أخدمك وأنزل ليك الفيديوهات من يوتيوب وتيك توك وفيسبوك بكل سهولة.\n\n"
        "✨ **كل اللي عليك ترسل الرابط وهسي بنجهزه ليك!**"
    )
    bot.send_message(message.chat.id, welcome_text)
    
    try:
        supabase.table('users').insert({
            'user_id': message.from_user.id, 
            'username': message.from_user.username or "No Username",
            'first_name': message.from_user.first_name or "No Name"
        }).execute()
    except: pass

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
    download_type = 'video' if call.data == "vid" else 'audio'
    
    engine = CrownEngine()
    file_path = None
    
    # 🌟 هنا الذكاء: بنشوف الرابط جاي من وين ونشغل الكود الخاص بيه
    if "youtube.com" in url_requested or "youtu.be" in url_requested:
        file_path = engine.download_youtube(url_requested, download_type)
        
    elif "facebook.com" in url_requested or "fb.watch" in url_requested:
        file_path = engine.download_facebook(url_requested, download_type)
        
    elif "tiktok.com" in url_requested:
        file_path = engine.download_tiktok(url_requested, download_type)
        
    else:
        # لو موقع تاني خالص
        try:
            with yt_dlp.YoutubeDL({'format': 'best'}) as ydl:
                info = ydl.extract_info(url_requested, download=True)
                file_path = ydl.prepare_filename(info)
        except: file_path = None

    # إرسال الملف للمستخدم
    if file_path and os.path.exists(file_path):
        bot.send_chat_action(uid, 'upload_video' if download_type == 'video' else 'upload_document')
        try:
            with open(file_path, 'rb') as f:
                if download_type == 'video':
                    bot.send_video(uid, f, caption="تم التحميل بواسطة CrownDL 👑")
                else:
                    bot.send_audio(uid, f, caption="تم التحميل بواسطة CrownDL 👑")
            os.remove(file_path)
        except Exception as e:
            bot.send_message(uid, f"حصلت مشكلة أثناء إرسال الملف 😢")
    else:
        bot.send_message(uid, "للأسف ما قدرت أحمل الرابط ده، جرب رابط تاني أو اتأكد من الرابط 🧐")

print("👑 البوت شغال الآن...")
bot.infinity_polling()
