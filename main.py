import telebot
import os
import time
import shutil
import threading  # <-- تم إضافة الاستيراد الناقص هنا
from flask import Flask, jsonify
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor
from supabase import create_client, Client
from datetime import datetime

# --- [0] إعداد خادم الويب ---
app = Flask('')

@app.route('/')
def home():
    return "خادم البوت يعمل بكفاءة عالية ✅"

@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()}), 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    # تشغيل Flask بدون الـ Reloader لضمان استقراره داخل الـ Thread
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# تشغيل خادم الويب في الخلفية قبل بدء البوت
threading.Thread(target=run_flask, daemon=True).start()

# --- [1] إعدادات البوت و Supabase ---
TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID = os.getenv("ADMIN_ID", "123456789")

# تحويل الـ ADMIN_ID إلى رقم بأمان لمنع الأخطاء في حال كان فارغاً
try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    ADMIN_ID = 123456789

if not TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("تأكد من تعبئة BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY في المتغيرات البيئية")

bot = telebot.TeleBot(TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

executor = ThreadPoolExecutor(max_workers=4)

# --- [2] دوال السيرفر وقاعدة البيانات ---
def log_event(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def save_user(user_id, username):
    try:
        supabase.table("users").upsert({
            "user_id": int(user_id),
            "username": username or "بدون_يوزر"
        }).execute()
        log_event(f"➕ مستخدم محفوظ: @{username} ({user_id})")
    except Exception as e:
        log_event(f"❌ خطأ حفظ مستخدم: {e}")

def get_all_users():
    try:
        res = supabase.table("users").select("user_id").execute()
        return [int(u['user_id']) for u in res.data]
    except Exception as e:
        log_event(f"❌ خطأ جلب المستخدمين: {e}")
        return []

def get_cookie_file(platform):
    """يجيب ملف الكوكي حسب المنصة"""
    if platform == "TikTok":
        cookie_path = os.path.join(BASE_DIR, "tiktok_cookies.txt")
    elif platform == "Facebook":
        cookie_path = os.path.join(BASE_DIR, "fb_cookies.txt")
    else:
        return None

    if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
        return cookie_path
    return None

def notify_admin(text):
    try:
        bot.send_message(ADMIN_ID, f"🔔 إشعار نظام\n{text}")
    except Exception as e:
        log_event(f"❌ فشل إرسال إشعار للأدمن: {e}")

# --- [3] دالة معالجة وتحميل الفيديو ---
def download_video(url, chat_id, message_id, username):
    unique_id = f"{chat_id}_{int(time.time())}"
    filename = os.path.join(BASE_DIR, f'video_{unique_id}.mp4')

    if 'tiktok.com' in url or 'vxtiktok.com' in url:
        platform = "TikTok"
    elif 'facebook.com' in url or 'fb.watch' in url:
        platform = "Facebook"
    else:
        bot.edit_message_text("❌ المنصة غير مدعومة", chat_id, message_id)
        return

    cookie_file = get_cookie_file(platform)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 49 * 1024 * 1024,
        'socket_timeout': 30,
        'retries': 2,
        'fragment_retries': 2,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'merge_output_format': 'mp4'
    }

    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    try:
        log_event(f"📥 بدء تحميل {platform} لـ @{username}")
        bot.edit_message_text(f"⏳ جاري سحب الفيديو من {platform}...", chat_id, message_id)

        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        bot.edit_message_text("📤 جاري الرفع إلى تليجرام...", chat_id, message_id)

        caption = "✨ @CrownDL_bot"

        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, caption=caption)

        bot.delete_message(chat_id, message_id)
        log_event(f"✅ تم الإرسال لـ @{username}")
        notify_admin(f"✅ تحميل ناجح\nالمنصة: {platform}\nالمستخدم: @{username}")

    except Exception as e:
        error = str(e).lower()
        log_event(f"❌ خطأ {platform} @{username}: {e}")

        if "file size" in error or "too large" in error:
            msg = "❌ حجم الفيديو أكبر من 50MB"
        elif "private" in error or "login" in error or "confirm you're not a bot" in error:
            msg = "❌ الفيديو خاص أو الكوكي منتهي"
        else:
            msg = "❌ فشل التحميل. جرب رابط آخر"

        bot.edit_message_text(msg, chat_id, message_id)
        notify_admin(f"❌ فشل تحميل\nالمنصة: {platform}\nالمستخدم: @{username}")

    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

# --- [4] البث الجماعي ---
def send_broadcast(text, admin_chat_id):
    users = get_all_users()
    if not users:
        bot.send_message(admin_chat_id, "❌ لا يوجد مستخدمين مسجلين")
        return

    status = bot.send_message(admin_chat_id, f"📢 بدء الإرسال لـ {len(users)} مستخدم...")
    success = fail = 0

    for uid in users:
        try:
            bot.send_message(uid, text)
            success += 1
            time.sleep(0.05)
        except telebot.apihelper.ApiTelegramException as e:
            fail += 1
            if e.error_code == 403:
                try:
                    supabase.table("users").delete().eq("user_id", int(uid)).execute()
                except:
                    pass
        except:
            fail += 1

    bot.edit_message_text(
        f"✅ اكتمل الإرسال الجماعي\n📊 الإحصائيات:\n- ناجح: {success}\n- فشل / حظر: {fail}",
        admin_chat_id, status.message_id
    )

# --- [5] المستقبلات ---
@bot.message_handler(commands=['start'])
def welcome(m):
    save_user(m.chat.id, m.from_user.username)
    username = m.from_user.username or f"User_{m.chat.id}"
    name = m.from_user.first_name or "بدون اسم"

    bot.reply_to(m, "مرحباً بك! أرسل رابط فيديو TikTok أو Facebook وسيتم تحميله فوراً. 🤖")
    notify_admin(f"👤 مستخدم جديد\nID: {m.chat.id}\nUsername: @{username}\nالاسم: {name}")

@bot.message_handler(commands=['stats'])
def stats(m):
    if m.chat.id != ADMIN_ID:
        return
    users = get_all_users()
    tiktok_cookie = "موجود" if os.path.exists(os.path.join(BASE_DIR, "tiktok_cookies.txt")) else "مفقود"
    fb_cookie = "موجود" if os.path.exists(os.path.join(BASE_DIR, "fb_cookies.txt")) else "مفقود"

    bot.reply_to(m, f"📊 إحصائيات النظام:\n\n👥 المستخدمين: {len(users)}\n🍪 كوكيز TikTok: {tiktok_cookie}\n🍪 كوكيز Facebook: {fb_cookie}")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(m):
    if m.chat.id != ADMIN_ID:
        return
    text = m.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(m, "⚠️ اكتب نص الرسالة بعد الأمر\nمثال: `/broadcast تحديث جديد`", parse_mode="Markdown")
        return
    executor.submit(send_broadcast, text, m.chat.id)

@bot.message_handler(func=lambda m: m.text and any(x in m.text for x in ['tiktok.com', 'vxtiktok.com', 'facebook.com', 'fb.watch']))
def handle_link(m):
    username = m.from_user.username or f"User_{m.chat.id}"
    msg = bot.reply_to(m, "🔍 جاري فحص الرابط...")
    executor.submit(download_video, m.text.strip(), m.chat.id, msg.message_id, username)

@bot.message_handler(func=lambda m: m.text and m.text.startswith('http') and not any(x in m.text for x in ['tiktok.com', 'vxtiktok.com', 'facebook.com', 'fb.watch']))
def fallback(m):
    bot.reply_to(m, "❌ الرابط غير مدعوم. ندعم TikTok و Facebook فقط.")

if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        log_event("⚠️ تحذير: FFmpeg غير مثبت. التحميل سيفشل")
    log_event("النظام يعمل الآن...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

