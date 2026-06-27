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

# ===== استخراج منشن‌ها از پیام =====
def extract_mentions(message):
    """
    استخراج اسم کاربرانی که منشن شدن در پیام
    """
    mentions = []
    
    # از خود message.mentions استفاده کن (بهترین روش)
    for user in message.mentions:
        mentions.append(user.display_name)
    
    # اگه کسی منشن نشده بود، از message.content با Regex استفاده کن
    if not mentions:
        # الگوی منشن: <@!USER_ID> یا <@USER_ID>
        pattern = r'<@!?(\d+)>'
        matches = re.findall(pattern, message.content)
        
        for user_id in matches:
            try:
                user = client.get_user(int(user_id))
                if user:
                    mentions.append(user.display_name)
            except:
                pass
    
    return mentions

# ===== تبدیل Embed به متن =====
def embed_to_text(embed, author_name=None, mention_names=None):
    parts = []
    
    # ===== اضافه کردن اسم راننده (از منشن‌ها) =====
    if mention_names:
        for name in mention_names:
            parts.append(f"<b>👤 {name}</b>")
            parts.append("")
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
        # ===== استخراج منشن‌ها =====
        mention_names = extract_mentions(message)
        
        # ===== گرفتن اسم نویسنده =====
        if message.webhook_id:
            author_name = message.author.name
        else:
            author_name = message.author.display_name
        
        # ===== لاگ برای دیباگ =====
        print(f"📨 Author: {author_name}")
        print(f"👥 Mentions: {mention_names}")
        print(f"🔍 Webhook ID: {message.webhook_id}")
        
        # ===== Embedها =====
        for embed in message.embeds:
            text = embed_to_text(embed, author_name, mention_names)
            if text:
                await send_message(text)
        
        # ===== متن اصلی =====
        if message.content and not message.embeds:
            # پاک کردن منشن‌ها از متن (چون جدا نشونشون میدیم)
            clean_content = re.sub(r'<@!?(\d+)>', '', message.content).strip()
            
            if mention_names:
                name_text = "، ".join(mention_names)
                await send_message(f"<b>👤 {name_text}</b>\n{clean_content}")
            else:
                await send_message(f"<b>👤 {author_name}</b>\n{clean_content}")
        
        # ===== فایل‌ها =====
        for attachment in message.attachments:
            if mention_names:
                name_text = "، ".join(mention_names)
                caption = f"<b>👤 {name_text}</b>\n📎 {attachment.filename}"
            else:
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
