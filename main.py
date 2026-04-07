import telebot
import os
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# --- 1. إعداد السيرفر للعمل على Render ---
app = Flask('')
@app.route('/')
def home():
    return "البوت شغال بأحدث نسخة مستقرة! ✅"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- 2. إعدادات الكوكيز برمجياً (لحل مشكلة الملفات الخارجية) ---
def setup_cookies():
    # 1. كوكيز يوتيوب
    youtube_content = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	0	__Secure-1PAPISID	_JkIC-y0k06opf5L/At5GKMur37iwLAHhQ
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSID	g.a0008ghP3HptOAg-tcVx9h7tUfGCNofRyHB2cvPSjJ_D8OIlK3eVgEuJmme-prAlKwVdrohjlQACgYKAcASARUSFQHGX2MiF3d2UR1-JX_LslvTIZjIGhoVAUF8yKoVtCq1vSyaNwU6y8b_fbDu0076
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSIDCC	AKEyXzVfiqh8kfPfzsDSxBxqIoVQQBUDHBcSi4tWQCH3JLsUYNBh0PHcwuuC8rpviYFF9HmZ
.youtube.com	TRUE	/	TRUE	0	__Secure-1PSIDTS	sidts-CjUBWhotCXz8pTxfPLQjMVM-qdHmXhck7sYRxsPTcQQAGLV591h1RH8mHuHmOJ7LpLRBRjV1YRAA
.youtube.com	TRUE	/	TRUE	0	__Secure-3PAPISID	_JkIC-y0k06opf5L/At5GKMur37iwLAHhQ
.youtube.com	TRUE	/	TRUE	0	__Secure-3PSID	g.a0008ghP3HptOAg-tcVx9h7tUfGCNofRyHB2cvPSjJ_D8OIlK3eVfgTvAivgi9Ovy_k9dB7iYwACgYKAXYSARUSFQHGX2MiBB8H820hV3VACBX_4-azBxoVAUF8yKr3oK090XOI9g7wGX71LaI50076
.youtube.com	TRUE	/	TRUE	0	__Secure-3PSIDCC	AKEyXzXi8c5Z3PuqhJfnjBg5QUnrXIzmQrA2UdFsi9TDbdSCBNnfhONC8ghM1l0ipnL7LJjh1g
.youtube.com	TRUE	/	TRUE	0	__Secure-3PSIDTS	sidts-CjUBWhotCXz8pTxfPLQjMVM-qdHmXhck7sYRxsPTcQQAGLV591h1RH8mHuHmOJ7LpLRBRjV1YRAA
.youtube.com	TRUE	/	TRUE	0	__Secure-ROLLOUT_TOKEN	CIPDpazbv4qJngEQ8r6PnojWkwMY5cK0y6rbkwM%3D
.youtube.com	TRUE	/	FALSE	0	APISID	mG8AU_lDTUTvP4we/AJLtYVj49Peiex_0u
.youtube.com	TRUE	/	FALSE	0	HSID	Aod2CGj7yBTfZQ8II
.youtube.com	TRUE	/	TRUE	0	LOGIN_INFO	AFmmF2swRgIhAJlaute9A-B0FPGMiXQmEcjlInhWc4KeXcH2Coyii-B2AiEA7sft04Vr-uHndUD_kdX2hE8sr1QuFtAdymcI1CekFA0:QUQ3MjNmemlBQ08yOEtVa1Uzd1NYWExzNlloU2lldlh0WEc0SDRlczZjSU1fREhvV1Y2SmROaFBOUzBpZ3NraEJsM2pHOUpSWXlHWlczU0pheUxBOTBPaEdCQUJrM05MeDhkZlp1cWcwZ0pvdFhlc1NQU1huOFVhU3M0SGdWTFJ3bkhyMmJQX0ZsWWZZVW5vSERRZnRjbkdybll2YjBiWjhR
.youtube.com	TRUE	/	TRUE	0	PREF	tz=Asia.Dubai
.youtube.com	TRUE	/	TRUE	0	SAPISID	_JkIC-y0k06opf5L/At5GKMur37iwLAHhQ
.youtube.com	TRUE	/	FALSE	0	SID	g.a0008ghP3HptOAg-tcVx9h7tUfGCNofRyHB2cvPSjJ_D8OIlK3eVXdj4JwkDV2v4pCk-Dez84QACgYKATcSARUSFQHGX2Mi2miN6zBN2aRpuD-1WTjqahoVAUF8yKpvJ7ZS90CLXfR2OLL6iQ500076
.youtube.com	TRUE	/	FALSE	0	SIDCC	AKEyXzUmbM9-cmsxLKpbkGYlaZJWDxBSc-AsbHiBRu2cp7DGhRS8YKhU5jS9mIk9xrbJqrtD6w
.youtube.com	TRUE	/	TRUE	0	SSID	ANZCaGK11gKx-MPxH
.youtube.com	TRUE	/	TRUE	0	VISITOR_INFO1_LIVE	zm40fP4s7JI
.youtube.com	TRUE	/	TRUE	0	VISITOR_PRIVACY_METADATA	CgJTRBIEGgAgGQ%3D%3D
.youtube.com	TRUE	/	TRUE	0	YSC	nJRgcJ49n5g
"""

    # 2. كوكيز تيك توك (التي أرسلتها الآن)
    tiktok_content = """# Netscape HTTP Cookie File
.tiktok.com	TRUE	/	TRUE	0	cmpl_token	AgQYAPMJ_hfkTtK57OKAqT9dLPOzk2MLSf-FgmCgGM8
.tiktok.com	TRUE	/	FALSE	0	d_ticket	66781a2e29eb3bab6d994138f48c604829cf8
.tiktok.com	TRUE	/	TRUE	0	msToken	v7UIAVMPFxwaWUJMZkBsG-mGWiD5JH2MOf0vS9-CXWPYylnwbN88MrWtuGePZs8x2WkSq9KjQ-eaI4peCFmYCJlBczqkZjUB-jieHwfnORJix9WEwfdv43reEJvJ0T_xqVz0s6rzxwHwBDBGhHVHyM4=
.tiktok.com	TRUE	/	TRUE	0	multi_sids	7625170481289462805%3Acc93a4d47bc53d39b5c95807f1d23f80
.tiktok.com	TRUE	/	FALSE	0	odin_tt	c42a2a20b209d53b2e919ebdf432fee9ee191f18b71528090a239ecce7febd70c4835349ed16f7148260d4aca4bbb0a92450caf2726c1b38211333c8253592b0c960ed9cfb8074668d8cff915234d261
.tiktok.com	TRUE	/	TRUE	0	sessionid	cc93a4d47bc53d39b5c95807f1d23f80
.tiktok.com	TRUE	/	TRUE	0	sessionid_ss	cc93a4d47bc53d39b5c95807f1d23f80
.tiktok.com	TRUE	/	TRUE	0	sid_guard	cc93a4d47bc53d39b5c95807f1d23f80%7C1775373815%7C15552000%7CFri%2C+02-Oct-2026+07%3A23%3A35+GMT
.tiktok.com	TRUE	/	TRUE	0	sid_tt	cc93a4d47bc53d39b5c95807f1d23f80
.tiktok.com	TRUE	/	TRUE	0	sid_ucp_v1	1.0.1-KGEyMmYzM2M2NGQxZjI3YTU2Y2VjMTU4MTgzZThmOTBiZDc5NTkxMTcKIgiViLaI8oSD6WkQ95vIzgYYswsgDDDCmMjOBjgBQPIHSAQQAxoCbXkiIGNjOTNhNGQ0N2JjNTNkMzliNWM5NTgwN2YxZDIzZjgwMk4KIFp5kcM5PWjsm35M_W6XJsC2gQdYRdNTjagIkumuVVkyEiAf5j7M4KShEO7aZ2ZHkOa7RO1B17kaZ3ZsLzQddqEvlBgBIgZ0aWt0b2s
.tiktok.com	TRUE	/	TRUE	0	ssid_ucp_v1	1.0.1-KGEyMmYzM2M2NGQxZjI3YTU2Y2VjMTU4MTgzZThmOTBiZDc5NTkxMTcKIgiViLaI8oSD6WkQ95vIzgYYswsgDDDCmMjOBjgBQPIHSAQQAxoCbXkiIGNjOTNhNGQ0N2JjNTNkMzliNWM5NTgwN2YxZDIzZjgwMk4KIFp5kcM5PWjsm35M_W6XJsC2gQdYRdNTjagIkumuVVkyEiAf5j7M4KShEO7aZ2ZHkOa7RO1B17kaZ3ZsLzQddqEvlBgBIgZ0aWt0b2s
.tiktok.com	TRUE	/	FALSE	0	store-country-code	sd
.tiktok.com	TRUE	/	FALSE	0	store-country-code-src	uid
.tiktok.com	TRUE	/	FALSE	0	store-country-sign	MEIEDOx2rjNNlNEZSLOShAQgzcNYpeOH-NWolDUPNhjZEzw5jkNnU6NUNRmosstnG6sEECwD7VfKGtW4ClFv-KRSPBM
.tiktok.com	TRUE	/	FALSE	0	store-idc	alisg
.tiktok.com	TRUE	/	TRUE	0	tt_chain_token	oIpr1j0035Tj9QdQ6SJKcQ==
.tiktok.com	TRUE	/	TRUE	0	tt_csrf_token	0CHVS5tw-8rpf-eLFGPKDEPT37QldbH5f-EQ
.tiktok.com	TRUE	/	TRUE	0	tt_session_tlb_tag	sttt%7C5%7CzJOk1HvFPTm1yVgH8dI_gP_________VblDGE4Gs54CuKUW-YSSMVKphZICnkDY3fochPeZxz-E%3D
.tiktok.com	TRUE	/	FALSE	0	tt-target-idc	alisg
.tiktok.com	TRUE	/	FALSE	0	tt-target-idc-sign	bT9IrZyG0lTwCVpDsBcwibIM-egzbM5RapvP1cWZnWq9iqLVUsDizva4nOItceWjrlDFQF9jkCWmTdNj0ATjcECu0HVDf6YeYNlY3Cq--5ZE1BfCZi8I5RihJI7Tl_bCJf5gqIvS1CbA2FnbsjDLC76n-A2f7Jpqd7s5HSO-LwIKpr34p5N5sNeee6ISn3k6gbKn54WnJtlG0t-U79_mAB7RRVYiPl-ndYW0syYntF7DMVoViOYz5a_-GaBtmkGUonIJQy1tbUOgm89LRAWvPSDYUpgN77f0CprF-ElyqeB7i9NuskQs6zABwiJ89Lr04TND8r9rDCQ2NW0fuMHLN3ESkq8gpbfymNRJb6Qj0jy4fBrQ2XZ3SbXyhChZaZwNeEwWyeEjqzarRMgIBu4XSGaq1anHIYDhVWkE5-ti4lVSxaxYJ3zqk16B632L9h50P43bUFoWW4rSXq798ZxbZCUoo_p-XXEA15LGR6_ETo_AXR_ZbAJPNCb9eQKFV68i
.tiktok.com	TRUE	/	TRUE	0	ttwid	1%7CZWMACB3btjab12q8SRfuC_r17an-S6dBy2daIJQMRu4%7C1775585283%7C61f05d479436c045702d89ce403fcaa794011fb2a0e46838250322234da95f91
.tiktok.com	TRUE	/	TRUE	0	uid_tt	a5773beda77e82d7bbbcc51f4d36246517a5dc7a9cbcdac779d03fda619e3622
.tiktok.com	TRUE	/	TRUE	0	uid_tt_ss	a5773beda77e82d7bbbcc51f4d36246517a5dc7a9cbcdac779d03fda619e3622
.www.tiktok.com	TRUE	/	TRUE	0	delay_guest_mode_vid	3
.www.tiktok.com	TRUE	/	TRUE	0	tiktok_webapp_theme	dark
.www.tiktok.com	TRUE	/	TRUE	0	tiktok_webapp_theme_source	auto
www.tiktok.com	FALSE	/	FALSE	0	last_login_method	email
www.tiktok.com	FALSE	/	FALSE	0	msToken	v7UIAVMPFxwaWUJMZkBsG-mGWiD5JH2MOf0vS9-CXWPYylnwbN88MrWtuGePZs8x2WkSq9KjQ-eaI4peCFmYCJlBczqkZjUB-jieHwfnORJix9WEwfdv43reEJvJ0T_xqVz0s6rzxwHwBDBGhHVHyM4=
www.tiktok.com	FALSE	/	FALSE	0	tt_ticket_guard_has_set_public_key	1
"""

    # 3. كوكيز فيسبوك (التي أرسلتها الآن)
    facebook_content = """# Netscape HTTP Cookie File
.facebook.com	TRUE	/	TRUE	0	c_user	61578432281821
.facebook.com	TRUE	/	TRUE	0	datr	ov7RafLXMN7nF8yPiOj296DI
.facebook.com	TRUE	/	TRUE	0	fr	1io1XxJ1wdmRwVXX6.AWfYSkkTRPJ6IW0wqU7mxgYGfoM0ejbUKq-q5DSoa3zKyfHb-6c.Bp1M2W..AAA.0.0.Bp1UkH.AWf3JVaD8VHqKUiJnoxEvCzbaVM
.facebook.com	TRUE	/	TRUE	0	ps_l	1
.facebook.com	TRUE	/	TRUE	0	ps_n	1
.facebook.com	TRUE	/	TRUE	0	sb	pf7RaSM7i4NQXJXd230cXNAc
.facebook.com	TRUE	/	TRUE	0	wd	1366x657
.facebook.com	TRUE	/	TRUE	0	xs	18%3A64VMFI-lT93ZYQ%3A2%3A1775370710%3A-1%3A-1%3A%3AAcxTfv2g_XnJwaovZfcmACmLb7V3m8txoPqRuLa-Ow
"""

    # حفظ الملفات داخل السيرفر
    with open("youtube_cookies.txt", "w", encoding="utf-8") as f:
        f.write(youtube_content.strip())
    with open("tiktok_cookies.txt", "w", encoding="utf-8") as f:
        f.write(tiktok_content.strip())
    with open("facebook_cookies.txt", "w", encoding="utf-8") as f:
        f.write(facebook_content.strip())
    print("✅ تم تجهيز جميع الملفات بنجاح.")

setup_cookies()


# --- 3. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8168754101 # معرف مصطفى للمراقبة
bot = telebot.TeleBot(API_TOKEN)

# مخزن مؤقت للروابط عشان ما نتخطى حد الـ 64 حرف في الأزرار
url_storage = {}

@bot.message_handler(func=lambda message: True)
def ask_format(message):
    url = message.text
    if not url.startswith('http'):
        return

    # حفظ الرابط برقم تعريفي بسيط
    url_id = str(len(url_storage) + 1)
    url_storage[url_id] = url

    markup = telebot.types.InlineKeyboardMarkup()
    # بنرسل الـ ID بس (مثلاً vid|1) بدلاً من الرابط الكامل
    btn_video = telebot.types.InlineKeyboardButton("🎬 تحميل فيديو", callback_data=f"vid|{url_id}")
    btn_audio = telebot.types.InlineKeyboardButton("🎵 تحميل صوت MP3", callback_data=f"aud|{url_id}")
    
    markup.add(btn_video, btn_audio)
    bot.reply_to(message, "ممتاز، اختار داير تحمل شنو:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    # استخراج النوع والـ ID
    format_type, url_id = call.data.split("|")
    url = url_storage.get(url_id) # استرجاع الرابط الأصلي من المخزن
    
    if not url:
        bot.answer_callback_query(call.id, "❌ عذراً، الرابط انتهت صلاحيته.")
        return

    chat_id = call.message.chat.id
    status_msg = bot.send_message(chat_id, "⏳ جاري المعالجة... انتظر لحظة")
    
    # تحديد ملف الكوكيز
    cookie_file = "youtube_cookies.txt" if "youtube" in url or "youtu.be" in url else None
    
    # إعدادات محسنة لتجنب الحظر
    ydl_opts = {
        'format': 'best[height<=720][ext=mp4]/best' if format_type == "vid" else 'bestaudio/best',
        'outtmpl': f'file_{chat_id}_{url_id}.%(ext)s',
        'cookiefile': cookie_file,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    if format_type == "aud":
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("📥 جاري التحميل من السيرفر...", chat_id, status_msg.message_id)
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == "aud": filename = filename.rsplit('.', 1)[0] + '.mp3'

        with open(filename, 'rb') as f:
            bot.edit_message_text("✅ جاري الرفع لتلجرام...", chat_id, status_msg.message_id)
            if format_type == "vid": bot.send_video(chat_id, f)
            else: bot.send_audio(chat_id, f)
        
        os.remove(filename)
        bot.delete_message(chat_id, status_msg.message_id)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حصل خطأ: {str(e)}")
if __name__ == "__main__":
    print("🚀 البوت انطلق بأحدث نسخة...")
    bot.infinity_polling()
