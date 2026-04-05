import os
import telebot
from telebot import types
from threading import Thread
from flask import Flask
from supabase import create_client, Client
import yt_dlp

# --- 1. تشغيل سيرفر الويب الوهمي للحفاظ على البوت صاحي ---
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

# --- 2. إعدادات الإدارة والبوت وسوبابيس ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8168754101

bot = telebot.TeleBot(TOKEN)
user_data = {} # لحفظ حالة المستخدم مؤقتاً (الرابط المختار)

SUPABASE_URL = "https://nrcpotvspxdvxlxbwzto.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- مسارات الكوكيز السرية في Render ---
TIKTOK_COOKIES = "/etc/secrets/tiktok_cookies.json"
FACEBOOK_COOKIES = "/etc/secrets/facebook_cookies.json"

# --- 3. دوال استقبال الرسائل والأزرار ---

# دالة الترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "يا مرحب بيك في بوت CrownDL 👑\nأرسل لي أي رابط من يوتيوب، فيسبوك، أو تيك توك وحأحمله ليك!"
    bot.send_message(message.chat.id, welcome_text)

# دالة استقبال الروابط وتوزيعها
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    chat_id = message.chat.id
    
    # حفظ الرابط مؤقتاً عشان نعرف المستخدم عاوز يحمل ياتو رابط
    user_data[chat_id] = {'url': url}
    
    # 1. روابط اليوتيوب
    if "youtube.com" in url or "youtu.be" in url:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("جودة عالية (720p)", callback_data="yt_720")
        btn2 = types.InlineKeyboardButton("جودة متوسطة (480p)", callback_data="yt_480")
        btn3 = types.InlineKeyboardButton("جودة منخفضة (360p)", callback_data="yt_360")
        markup.add(btn1, btn2, btn3)
        bot.send_message(chat_id, "🎬 اختر جودة التحميل لليوتيوب:", reply_markup=markup)
        
    # 2. روابط فيسبوك
    elif "facebook.com" in url or "fb.watch" in url:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("جودة عالية HD", callback_data="fb_hd")
        btn2 = types.InlineKeyboardButton("جودة عادية SD", callback_data="fb_sd")
        markup.add(btn1, btn2)
        bot.send_message(chat_id, "🎬 اختر جودة التحميل لفيسبوك:", reply_markup=markup)
        
    # 3. روابط تيك توك (تحميل مباشر بدون أزرار)
    elif "tiktok.com" in url:
        bot.send_message(chat_id, "⏳ جاري تحميل فيديو تيك توك بأعلى جودة ممكنة...")
        download_video(chat_id, url, TIKTOK_COOKIES, format_opt="best")
        
    else:
        bot.send_message(chat_id, "❌ عفواً، أرسل لي روابط يوتيوب، فيسبوك، أو تيك توك فقط!")

# دالة التعامل مع ضغطات الأزرار (Callback)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    # التأكد إن المستخدم عنده رابط مسجل
    if chat_id not in user_data:
        bot.send_message(chat_id, "❌ حصل خطأ، أرسل الرابط مرة تانية من فضلك.")
        return
        
    url = user_data[chat_id]['url']
    
    # مسح الأزرار بعد الضغط عليها
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    
    # فرز الخيارات
    if call.data == "yt_720":
        bot.send_message(chat_id, "⏳ جاري التحميل بجودة 720p...")
        download_video(chat_id, url, None, format_opt="bestvideo[height<=720]+bestaudio/best")
        
    elif call.data == "yt_480":
        bot.send_message(chat_id, "⏳ جاري التحميل بجودة 480p...")
        download_video(chat_id, url, None, format_opt="bestvideo[height<=480]+bestaudio/best")
        
    elif call.data == "yt_360":
        bot.send_message(chat_id, "⏳ جاري التحميل بجودة 360p...")
        download_video(chat_id, url, None, format_opt="bestvideo[height<=360]+bestaudio/best")
        
    elif call.data == "fb_hd":
        bot.send_message(chat_id, "⏳ جاري التحميل بجودة عالية HD...")
        download_video(chat_id, url, FACEBOOK_COOKIES, format_opt="best")
        
    elif call.data == "fb_sd":
        bot.send_message(chat_id, "⏳ جاري التحميل بجودة عادية SD...")
        download_video(chat_id, url, FACEBOOK_COOKIES, format_opt="worst")

# --- 4. دالة التحميل وتسجيل البيانات في Supabase ---
def download_video(chat_id, url, cookies_path, format_opt):
    ydl_opts = {
        'format': format_opt,
        'outtmpl': '/tmp/%(title)s.%(ext)s',
        'quiet': True,
    }
    
    # لو في كوكيز بنمرره، لو مافي (زي يوتيوب مثلاً) بنخليه يشتغل بدونه
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            
            # إرسال الفيديو للمستخدم
            with open(video_path, 'rb') as video:
                bot.send_video(chat_id, video, caption="تم التحميل بنجاح بواسطة CrownDL 👑")
                
            # مسح الملف من السيرفر لعدم امتلاء المساحة
            os.remove(video_path)
            
            # --- تسجيل العملية في قاعدة البيانات (Supabase) ---
            try:
                supabase.table("downloads").insert({
                    "chat_id": chat_id,
                    "url": url,
                    "status": "success"
                }).execute()
            except Exception as db_err:
                print(f"فشل التسجيل في قاعدة البيانات: {db_err}")
                
    except Exception as e:
        bot.send_message(chat_id, f"❌ حصلت مشكلة أثناء التحميل!\nالخطأ: {str(e)}")
        # تسجيل العملية كفاشلة في سوبابيس
        try:
            supabase.table("downloads").insert({
                "chat_id": chat_id,
                "url": url,
                "status": "failed"
            }).execute()
        except:
            pass

# --- 5. تشغيل كل شيء ---
if __name__ == "__main__":
    keep_alive()
    print("🤖 البوت بدأ العمل الآن بالنسخة الكاملة...")
    bot.infinity_polling()
