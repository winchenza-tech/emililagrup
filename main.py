import asyncio
import nest_asyncio
import datetime
import os
import random
from collections import deque
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from google import genai
from google.genai import types

# --- 1. WEB SUNUCUSU ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Zenithar 7/24 Görev Başında!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- 2. AYARLAR VE HAFIZA ---
nest_asyncio.apply()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

AUTHORIZED_GROUP_ID = -1002906566461

# --- 👑 YÖNETİCİ AYARLARI ---
ADMIN_IDS = [7094870780, 993948902, 8363077895]
ZENITHAR_ID = 7094870780

UNAUTHORIZED_IMAGE_URL = "https://i.ibb.co/zTjGk8rv/MG-8095.jpg"
UNAUTHORIZED_ERROR_TEXT = (
    "Sadece BEKLER grubunda çalışacağını söyledik.\n\n"
    "Okuduğun basit bir cümleyi anlamayacak kadar gerizekalı isen "
    "altta verdiğim linkten beyin gelişim egzersizleri yapabilirsin.\n"
    "https://www.mentalup.net/blog/zeka-gelistirici-oyunlar"
)

# --- 🔥 ÖZEL KİŞİ AYARLARI ---
FELICIA_ID = 5457659716
TUNA_ID = 5571011500
FELICIA_NAME = "Felicia"
TUNA_NAME = "Tuna"

# Model ismi
MODEL_NAME = 'gemini-2.0-flash'

client = genai.Client(api_key=GOOGLE_API_KEY)

group_history = deque(maxlen=110)
admin_pm_history = deque(maxlen=5) # Adminlerin bota attığı son 5 mesaj için hafıza
message_id_cache = {} 
last_usage = {}
COOLDOWN_MINUTES = 10
pending_replies = {} 

# --- 🃏 TAROT KARTLARI ---
TAROT_CARDS = [
    "Deli", "Büyücü", "Azize", "İmparatoriçe", "İmparator", "Aziz",
    "Aşıklar", "Savaş Arabası", "Güç", "Ermiş", "Kader Çarkı", "Adalet",
    "Asılan Adam", "Ölüm", "Denge", "Şeytan", "Yıkılan Kule", "Yıldız",
    "Ay", "Güneş", "Mahkeme", "Dünya"
]

# --- 3. BOT FONKSİYONLARI ---

async def record_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private' and update.effective_user.id in ADMIN_IDS:
        # Adminlerin bota yazdığı metin mesajlarını hafızaya al
        if update.message and update.message.text:
            admin_pm_history.append(f"👤 {update.effective_user.first_name}: {update.message.text}")

        if update.effective_user.id in pending_replies:
            target_id = pending_replies.pop(update.effective_user.id)
            if update.message.text: await context.bot.send_message(chat_id=AUTHORIZED_GROUP_ID, text=update.message.text, reply_to_message_id=target_id)
            elif update.message.voice: await context.bot.send_voice(chat_id=AUTHORIZED_GROUP_ID, voice=update.message.voice.file_id, reply_to_message_id=target_id)
            elif update.message.audio: await context.bot.send_audio(chat_id=AUTHORIZED_GROUP_ID, audio=update.message.audio.file_id, reply_to_message_id=target_id)
            return

    if update.effective_chat.id == AUTHORIZED_GROUP_ID and update.message and update.message.text:
        u_id = update.effective_user.id
        u_name = FELICIA_NAME if u_id == FELICIA_ID else TUNA_NAME if u_id == TUNA_ID else update.effective_user.first_name
        if len(u_name) <= 2: u_name = f"{u_name}"
        group_history.append(f"{u_name}: {update.message.text}")
        message_id_cache[update.message.message_id] = {"name": u_name, "text": update.message.text}
        if len(message_id_cache) > 50: del message_id_cache[next(iter(message_id_cache))]

async def announce_command(update, context):
    if update.effective_user.id in ADMIN_IDS and context.args:
        await context.bot.send_message(chat_id=AUTHORIZED_GROUP_ID, text=f"📢{' '.join(context.args)}")

async def comment_command(update, context):
    if update.effective_chat.id != AUTHORIZED_GROUP_ID or not update.message.reply_to_message: return
    target = update.message.reply_to_message
    t_name = FELICIA_NAME if target.from_user.id == FELICIA_ID else TUNA_NAME if target.from_user.id == TUNA_ID else target.from_user.first_name
    if t_name.lower() == "zenithar":
        await update.message.reply_text("Zenithar'a ihanet edemem. O benim yaratıcım")
        return
    roast_prompt = f"(Acımasız, üstün zekalı, alaycısın). HEDEF KİŞİ: {t_name} MESAJI: {target.text} GÖREVİN: Dalga geç, aşağıla. Maks 20 kelime."
    try:
        res = client.models.generate_content(model=MODEL_NAME, contents=roast_prompt)
        await target.reply_text(f"💀{res.text}")
    except: pass

async def kamilaca_command(update, context):
    if update.effective_chat.id != AUTHORIZED_GROUP_ID or not update.message.reply_to_message: return
    target = update.message.reply_to_message
    prompt = f"(Sivri dilli, zeki, komik ve feminist bir kadınsın). MESAJ: {target.text} GÖREVİN: Bu mesaja alaycı bir şekilde cevap ver ve konuyu mutlaka erkeklerin genel bir kusuruna (örneğin beceriksizliklerine, düz mantıklarına) bağlayıp 'zaten erkekler şöyle böyle...' diyerek eleştir. Maksimum 30 kelime olsun."
    try:
        res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        await target.reply_text(f"💅 {res.text}")
    except: pass

async def emilile_command(update, context):
    if update.effective_chat.id != AUTHORIZED_GROUP_ID or not update.message.reply_to_message: return
    target = update.message.reply_to_message
    prompt = f"(Alıngan, sürekli trip atan ve sitemkar birisin). MESAJ: {target.text} GÖREVİN: Bu mesaja cevap verirken konuyu bir şekilde 'Zenithar'a bağla ve ona sitem et, trip at. 'Zenithar da hep böyle yapıyor' tarzında bir alınganlık göster. Maksimum 30 kelime olsun."
    try:
        res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        await target.reply_text(f"😒 {res.text}")
    except: pass

async def
