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

# ===== استخراج اسم از Webhook =====
def get_author_name(message):
    """
    اسم نویسنده رو از Webhook یا کاربر عادی استخراج میکنه
    """
    # اگه Webhook باشه
    if message.webhook_id:
        # اسم Webhook رو برمیگردونه (همون اسم راننده)
        return message.author.display_name
    
    # اگه کاربر عادی باشه
    return message.author.display_name

# ===== تبدیل Embed به متن =====
def embed_to_text(embed, author_name=None):
    parts = []
    
    # ===== اضافه کردن اسم راننده =====
    if author_name:
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
                parts.append(f"<b>{field.name}:</b> {field.value}")
    
    # Footer
    if embed.footer and embed.footer.text:
        parts.append(f"\n{embed.footer.text}")
    
    return "\n".join(parts) if parts else None

# ===== رویداد پیام =====
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    try:
        # ===== گرفتن اسم راننده =====
        author_name = get_author_name(message)
        
        # ===== Embedها =====
        for embed in message.embeds:
            text = embed_to_text(embed, author_name)
            if text:
                await send_message(text)
        
        # ===== متن اصلی =====
        if message.content and not message.embeds:
            await send_message(f"<b>👤 {author_name}</b>\n{message.content}")
        
        # ===== فایل‌ها =====
        for attachment in message.attachments:
            caption = f"<b>👤 {author_name}</b>\n📎 {attachment.filename}"
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
