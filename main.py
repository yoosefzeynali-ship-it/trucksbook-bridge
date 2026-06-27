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

def convert_emoji(text):
    """تبدیل کدهای ایموجی دیسکورد به یونیکد"""
    if not text:
        return text
    
    # تبدیل پرچم‌ها
    for code, emoji in FLAG_MAP.items():
        text = text.replace(code, emoji)
    
    return text

# ===== توابع تلگرام =====
async def telegram(method, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            return await response.json()

async def send_message(text):
    await telegram("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

# ===== تبدیل Embed به متن =====
def embed_to_text(embed, author_name=None):
    parts = []
    
    if author_name:
        parts.append(f"<b>👤 {author_name}</b>")
        parts.append("")
    
    if embed.title:
        parts.append(f"<b>{convert_emoji(embed.title)}</b>")
    
    if embed.description:
        parts.append(convert_emoji(embed.description))
    
    if embed.fields:
        for field in embed.fields:
            if field.name and field.value:
                parts.append(f"<b>{convert_emoji(field.name)}:</b> {convert_emoji(field.value)}")
    
    if embed.footer and embed.footer.text:
        parts.append(f"\n{convert_emoji(embed.footer.text)}")
    
    return "\n".join(parts) if parts else None

# ===== رویداد پیام =====
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
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
        
        # ارسال Embedها
        for embed in message.embeds:
            text = embed_to_text(embed, driver_name)
            if text:
                await send_message(text)
        
        # ارسال متن اصلی
        if message.content and not message.embeds:
            clean_content = convert_emoji(message.content)
            if driver_name:
                await send_message(f"<b>👤 {driver_name}</b>\n{clean_content}")
            else:
                await send_message(clean_content)
    
    except Exception as e:
        print("ERROR:", e)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

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
