import os
import asyncio
import threading
import aiohttp
import discord
from discord import Intents
from flask import Flask
import re

# ===== Environment Variables =====
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ===== Flask App =====
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Discord Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

# ===== کلاینت دیسکورد =====
intents = Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ===== لیست چنل‌های مجاز =====
ALLOWED_CHANNELS = [
    1119716452065366026,
    1087031811877654538,
    1119726229621321819,
    1087132698096705726
]

# ===== دیکشنری کامل پرچم‌ها =====
FLAG_MAP = {
    ':flag_us:': '🇺🇸', ':flag_ca:': '🇨🇦', ':flag_mx:': '🇲🇽',
    ':flag_uk:': '🇬🇧', ':flag_gb:': '🇬🇧', ':flag_de:': '🇩🇪',
    ':flag_fr:': '🇫🇷', ':flag_it:': '🇮🇹', ':flag_es:': '🇪🇸',
    ':flag_pt:': '🇵🇹', ':flag_nl:': '🇳🇱', ':flag_be:': '🇧🇪',
    ':flag_at:': '🇦🇹', ':flag_ch:': '🇨🇭', ':flag_se:': '🇸🇪',
    ':flag_no:': '🇳🇴', ':flag_dk:': '🇩🇰', ':flag_fi:': '🇫🇮',
    ':flag_pl:': '🇵🇱', ':flag_cz:': '🇨🇿', ':flag_sk:': '🇸🇰',
    ':flag_hu:': '🇭🇺', ':flag_ro:': '🇷🇴', ':flag_bg:': '🇧🇬',
    ':flag_gr:': '🇬🇷', ':flag_tr:': '🇹🇷', ':flag_ie:': '🇮🇪',
    ':flag_is:': '🇮🇸', ':flag_lt:': '🇱🇹', ':flag_lv:': '🇱🇻',
    ':flag_ee:': '🇪🇪', ':flag_ru:': '🇷🇺', ':flag_ua:': '🇺🇦',
    ':flag_ir:': '🇮🇷', ':flag_ae:': '🇦🇪', ':flag_sa:': '🇸🇦',
    ':flag_in:': '🇮🇳', ':flag_cn:': '🇨🇳', ':flag_jp:': '🇯🇵',
    ':flag_kr:': '🇰🇷', ':flag_vn:': '🇻🇳', ':flag_th:': '🇹🇭',
    ':flag_my:': '🇲🇾', ':flag_sg:': '🇸🇬', ':flag_ph:': '🇵🇭',
    ':flag_id:': '🇮🇩', ':flag_pk:': '🇵🇰', ':flag_bd:': '🇧🇩',
    ':flag_np:': '🇳🇵', ':flag_lk:': '🇱🇰', ':flag_kh:': '🇰🇭',
    ':flag_af:': '🇦🇫', ':flag_iq:': '🇮🇶', ':flag_sy:': '🇸🇾',
    ':flag_jo:': '🇯🇴', ':flag_lb:': '🇱🇧', ':flag_il:': '🇮🇱',
    ':flag_ye:': '🇾🇪', ':flag_om:': '🇴🇲', ':flag_qa:': '🇶🇦',
    ':flag_kw:': '🇰🇼', ':flag_eg:': '🇪🇬', ':flag_za:': '🇿🇦',
    ':flag_ng:': '🇳🇬', ':flag_ke:': '🇰🇪', ':flag_tz:': '🇹🇿',
    ':flag_gh:': '🇬🇭', ':flag_dz:': '🇩🇿', ':flag_ma:': '🇲🇦',
    ':flag_tn:': '🇹🇳', ':flag_ly:': '🇱🇾', ':flag_et:': '🇪🇹',
    ':flag_so:': '🇸🇴', ':flag_ug:': '🇺🇬', ':flag_rw:': '🇷🇼',
    ':flag_cd:': '🇨🇩', ':flag_cg:': '🇨🇬', ':flag_ga:': '🇬🇦',
    ':flag_cm:': '🇨🇲', ':flag_ci:': '🇨🇮', ':flag_sn:': '🇸🇳',
    ':flag_ml:': '🇲🇱', ':flag_bf:': '🇧🇫', ':flag_ne:': '🇳🇪',
    ':flag_td:': '🇹🇩', ':flag_au:': '🇦🇺', ':flag_nz:': '🇳🇿',
    ':flag_fj:': '🇫🇯', ':flag_pg:': '🇵🇬', ':flag_br:': '🇧🇷',
    ':flag_ar:': '🇦🇷', ':flag_cl:': '🇨🇱', ':flag_co:': '🇨🇴',
    ':flag_pe:': '🇵🇪', ':flag_ve:': '🇻🇪', ':flag_ec:': '🇪🇨',
    ':flag_bo:': '🇧🇴', ':flag_py:': '🇵🇾', ':flag_uy:': '🇺🇾',
}

OTHER_EMOJI_MAP = {
    ':arrow_up:': '⬆️',
    ':arrow_down:': '⬇️',
    ':arrow_forward:': '▶️',
    ':arrow_backward:': '◀️',
    ':white_check_mark:': '✅',
    ':x:': '❌',
    ':warning:': '⚠️',
    ':information_source:': 'ℹ️',
    ':truck:': '🚛',
    ':package:': '📦',
    ':moneybag:': '💰',
    ':fire:': '🔥',
    ':star:': '⭐',
    ':star2:': '🌟',
    ':sparkles:': '✨',
    ':zap:': '⚡',
    ':clock:': '🕐',
    ':calendar:': '📅',
    ':globe_with_meridians:': '🌐',
}

EMOJI_MAP = {**FLAG_MAP, **OTHER_EMOJI_MAP}

def convert_emoji(text):
    if not text:
        return text
    for code, emoji in EMOJI_MAP.items():
        text = text.replace(code, emoji)
    return text

FOOTER_TEXT = "\n\n⚡️@Caspiancboy⚡️"

async def telegram(method, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            return await response.json()

async def send_message(text):
    full_text = text + FOOTER_TEXT
    await telegram("sendMessage", {
        "chat_id": CHAT_ID,
        "text": full_text,
        "parse_mode": "HTML"
    })

def embed_to_text(embed, author_name=None):
    parts = []
    
    if author_name:
        parts.append(f"👤Driver <b>{author_name}</b>")
        parts.append("")
    
    if embed.title:
        parts.append(f{convert_emoji(embed.title)}")
    
    if embed.description:
        parts.append(f"{convert_emoji(embed.description)}")
    
    if embed.fields:
        for field in embed.fields:
            if field.name and field.value:
                clean_name = convert_emoji(field.name)
                clean_value = convert_emoji(field.value)
                
                if "From" in field.name:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                elif "To" in field.name:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                elif "Cargo" in field.name or "Details" in field.name:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                elif "Accepted distance" in field.name:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                elif "Profit" in field.name:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                elif "Truck" in field.name:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                elif "Statistics" in field.name:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                elif "Rank" in field.name:
                    clean_value = clean_value.replace(':arrow_up:', '⬆️')
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
                else:
                    parts.append(f"<b>{clean_name}:</b> {clean_value}")
    
    if embed.footer and embed.footer.text:
        parts.append(f"\n{convert_emoji(embed.footer.text)}")
    
    return "\n".join(parts) if parts else None

# ===== رویداد پیام با دیباگ کامل =====
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # ===== دیباگ: همه پیام‌ها رو توی لاگ نشون بده =====
    print("=" * 60)
    print(f"📨 پیام جدید دریافت شد!")
    print(f"📌 چنل ID: {message.channel.id}")
    print(f"📌 نام چنل: {message.channel.name}")
    print(f"📌 نویسنده: {message.author}")
    print(f"📝 محتوا: {message.content[:100] if message.content else '(خالی)'}")
    print(f"📊 تعداد Embedها: {len(message.embeds)}")
    
    # ===== بررسی چنل =====
    if message.channel.id not in ALLOWED_CHANNELS:
        print(f"⛔ چنل {message.channel.id} مجاز نیست. نادیده گرفته شد.")
        print("=" * 60)
        return
    
    print(f"✅ چنل مجاز است! ادامه پردازش...")
    print("=" * 60)
    
    try:
        # استخراج اسم راننده
        driver_name = None
        
        for embed in message.embeds:
            if embed.author and embed.author.name:
                driver_name = embed.author.name
                break
        
        if not driver_name and message.webhook_id:
            webhook_name = message.author.name
            if webhook_name and "Webhook" not in webhook_name:
                driver_name = webhook_name
        
        if not driver_name and message.mentions:
            driver_name = message.mentions[0].display_name
        
        # ===== ارسال Embedها =====
        for embed in message.embeds:
            text = embed_to_text(embed, driver_name)
            if text:
                print(f"📤 ارسال به تلگرام: {text[:50]}...")
                await send_message(text)
        
        # ===== ارسال متن اصلی =====
        if message.content and not message.embeds:
            clean_content = convert_emoji(message.content)
            if driver_name:
                await send_message(f"👤 <b>{driver_name}</b>\n{clean_content}")
            else:
                await send_message(clean_content)
        
        # ===== فایل‌ها =====
        for attachment in message.attachments:
            if driver_name:
                caption = f"👤 <b>{driver_name}</b>\n📎 {attachment.filename}"
            else:
                caption = f"📎 {attachment.filename}"
            await send_message(caption)
    
    except Exception as e:
        print(f"❌ ERROR: {e}")

@client.event
async def on_ready():
    print("=" * 60)
    print(f"✅ ربات با موفقیت وارد شد: {client.user}")
    print(f"📋 چنل‌های مجاز:")
    for channel_id in ALLOWED_CHANNELS:
        try:
            channel = client.get_channel(channel_id)
            if channel:
                print(f"   ✅ {channel_id} - #{channel.name}")
            else:
                print(f"   ❌ {channel_id} - (ربات به این چنل دسترسی ندارد!)")
        except:
            print(f"   ❌ {channel_id} - (خطا در دریافت اطلاعات)")
    print("=" * 60)

# ===== اجرا =====
def run_bot():
    client.run(DISCORD_TOKEN)

if __name__ == "__main__":
    if not DISCORD_TOKEN or not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Environment Variables missing!")
        exit(1)
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
