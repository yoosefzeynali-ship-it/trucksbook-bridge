import os
import asyncio
import threading
import aiohttp
import discord
from discord import Intents
from flask import Flask

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

# ===== استخراج اسم واقعی از Embed =====
def extract_real_name_from_embed(embed):
    """
    اسم واقعی رو از داخل Embed استخراج میکنه
    """
    # روش اول: از عنوان یا توضیحات
    if embed.title and "TrucksBook" in embed.title:
        # اگه عنوان فقط "Trucksbook" هست، از اون استفاده نکن
        pass
    
    # روش دوم: از فیلدها
    if embed.fields:
        for field in embed.fields:
            # اگه فیلدی اسم کاربر رو داشته باشه
            if field.name and ("کاربر" in field.name or "player" in field.name.lower() or "driver" in field.name.lower()):
                return field.value
    
    # روش سوم: از متن footer
    if embed.footer and embed.footer.text:
        # اگه footer شامل اسم باشه
        footer_text = embed.footer.text
        if "TrucksBook" not in footer_text and len(footer_text) < 30:
            return footer_text
    
    return None

# ===== تبدیل Embed به متن =====
def embed_to_text(embed, author_name=None):
    parts = []
    
    # ===== استخراج اسم واقعی =====
    real_name = extract_real_name_from_embed(embed)
    
    # اگه اسم واقعی پیدا شد، از اون استفاده کن
    if real_name:
        parts.append(f"<b>👤 {real_name}</b>")
        parts.append("")
    # در غیر این صورت از اسم فرستنده استفاده کن (اگه Webhook نباشه)
    elif author_name and "Webhook" not in author_name:
        parts.append(f"<b>👤 {author_name}</b>")
        parts.append("")
    
    # ===== محتوای اصلی =====
    if embed.title:
        parts.append(f"<b>{embed.title}</b>")
    
    if embed.description:
        parts.append(embed.description)
    
    # فیلدها
    if embed.fields:
        for field in embed.fields:
            if field.name and field.value:
                # اگه فیلد اسم کاربره، از قبل اضافه کردیم پس دوباره اضافه نکن
                if field.name and ("کاربر" in field.name or "player" in field.name.lower() or "driver" in field.name.lower()):
                    continue
                parts.append(f"<b>{field.name}:</b> {field.value}")
    
    # Footer
    if embed.footer and embed.footer.text:
        footer_text = embed.footer.text
        # اگه footer اسم کاربره، از قبل اضافه کردیم
        if real_name and real_name in footer_text:
            pass
        elif "TrucksBook" not in footer_text:
            parts.append(f"\n{footer_text}")
        else:
            parts.append(f"\n{footer_text}")
    
    return "\n".join(parts) if parts else None

# ===== رویداد پیام =====
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    try:
        # ===== Embedها =====
        for embed in message.embeds:
            text = embed_to_text(embed, message.author.display_name)
            if text:
                await send_message(text)
        
        # ===== متن اصلی =====
        if message.content and not message.embeds:
            # اگه Webhook نباشه
            if "Webhook" not in message.author.display_name:
                await send_message(f"<b>👤 {message.author.display_name}</b>\n{message.content}")
            else:
                await send_message(message.content)
        
        # ===== فایل‌ها =====
        for attachment in message.attachments:
            if "Webhook" not in message.author.display_name:
                caption = f"<b>👤 {message.author.display_name}</b>\n📎 {attachment.filename}"
            else:
                caption = f"📎 {attachment.filename}"
            await send_message(caption)
    
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
