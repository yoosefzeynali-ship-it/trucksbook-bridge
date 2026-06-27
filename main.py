import os
import asyncio
import aiohttp
import discord
from discord import Intents

# ===== Environment Variables =====
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ===== کلاینت دیسکورد =====
intents = Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ===== تابع ارسال به تلگرام =====
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

async def send_photo(url):
    await telegram("sendPhoto", {
        "chat_id": CHAT_ID,
        "photo": url
    })

# ===== تبدیل Embed به متن =====
def embed_to_text(embed):
    parts = []
    
    if embed.title:
        parts.append(f"<b>{embed.title}</b>")
    
    if embed.description:
        parts.append(embed.description)
    
    if embed.fields:
        for field in embed.fields:
            if field.name and field.value:
                parts.append(f"<b>{field.name}:</b> {field.value}")
    
    if embed.footer and embed.footer.text:
        parts.append(f"\n{embed.footer.text}")
    
    return "\n".join(parts) if parts else None

# ===== رویداد پیام =====
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    try:
        # ===== متن اصلی =====
        if message.content:
            await send_message(message.content)
        
        # ===== Embedها =====
        for embed in message.embeds:
            text = embed_to_text(embed)
            if text:
                await send_message(text)
            
            if embed.image and embed.image.url:
                await send_photo(embed.image.url)
            elif embed.thumbnail and embed.thumbnail.url:
                await send_photo(embed.thumbnail.url)
        
        # ===== فایل‌ها =====
        for attachment in message.attachments:
            if attachment.content_type:
                if attachment.content_type.startswith("image"):
                    await send_photo(attachment.url)
                else:
                    await telegram("sendDocument", {
                        "chat_id": CHAT_ID,
                        "document": attachment.url
                    })
    
    except Exception as e:
        print("ERROR:", e)

# ===== اجرا =====
if __name__ == "__main__":
    if not DISCORD_TOKEN or not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Environment Variables missing!")
        exit(1)
    
    print("✅ Bot is running...")
    client.run(DISCORD_TOKEN)
