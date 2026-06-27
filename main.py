import os
import asyncio
import threading
import aiohttp
import discord
from discord import Intents
from flask import Flask
import json

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

# ===== دیباگ کامل پیام =====
def debug_message(message):
    print("\n" + "=" * 80)
    print("🔍 DEBUG - تمام اطلاعات پیام:")
    print("=" * 80)
    
    # اطلاعات پایه
    print(f"📌 ID: {message.id}")
    print(f"📌 نوع: {message.type}")
    print(f"📌 نویسنده: {message.author} (ID: {message.author.id})")
    print(f"📌 نام نویسنده: {message.author.name}")
    print(f"📌 نام نمایشی: {message.author.display_name}")
    print(f"📌 Webhook ID: {message.webhook_id}")
    print(f"📌 محتوای متن: {repr(message.content)}")
    print(f"📌 تعداد Embeds: {len(message.embeds)}")
    print(f"📌 تعداد فایل‌ها: {len(message.attachments)}")
    print(f"📌 تعداد منشن‌ها: {len(message.mentions)}")
    
    if message.mentions:
        for user in message.mentions:
            print(f"   👤 منشن: {user} (ID: {user.id}) - نام: {user.name} - نمایشی: {user.display_name}")
    
    # ===== بررسی کامل هر Embed =====
    for i, embed in enumerate(message.embeds):
        print(f"\n--- EMBED {i+1} ---")
        
        # تبدیل به دیکشنری برای نمایش
        embed_dict = embed.to_dict()
        print(json.dumps(embed_dict, indent=2, ensure_ascii=False))
        
        # بررسی جداگانه هر بخش
        print("\n📊 بررسی جداگانه:")
        
        if embed.author:
            print(f"  👤 AUTHOR:")
            print(f"     name: {repr(embed.author.name)}")
            print(f"     url: {repr(embed.author.url)}")
            print(f"     icon_url: {repr(embed.author.icon_url)}")
        else:
            print("  👤 AUTHOR: ندارد")
        
        if embed.title:
            print(f"  📌 TITLE: {repr(embed.title)}")
        else:
            print("  📌 TITLE: ندارد")
        
        if embed.description:
            print(f"  📝 DESCRIPTION: {repr(embed.description)}")
        else:
            print("  📝 DESCRIPTION: ندارد")
        
        if embed.fields:
            for j, field in enumerate(embed.fields):
                print(f"  📋 FIELD {j+1}:")
                print(f"     name: {repr(field.name)}")
                print(f"     value: {repr(field.value)}")
                print(f"     inline: {field.inline}")
        
        if embed.footer:
            print(f"  📌 FOOTER: {repr(embed.footer.text)}")
        else:
            print("  📌 FOOTER: ندارد")
        
        if embed.image:
            print(f"  🖼️ IMAGE: {repr(embed.image.url)}")
        else:
            print("  🖼️ IMAGE: ندارد")
        
        if embed.thumbnail:
            print(f"  🖼️ THUMBNAIL: {repr(embed.thumbnail.url)}")
        else:
            print("  🖼️ THUMBNAIL: ندارد")
    
    print("=" * 80 + "\n")

# ===== رویداد پیام =====
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    try:
        # ===== دیباگ =====
        debug_message(message)
        
        # ===== بعد از دیباگ، می‌تونیم پیام رو بفرستیم =====
        # اینجا کد ارسال به تلگرام رو می‌ذاریم
        
        for embed in message.embeds:
            # ساده‌ترین حالت: فقط محتوای Embed رو بفرست
            text = f"📨 پیام از دیسکورد\n"
            
            if embed.author and embed.author.name:
                text += f"👤 {embed.author.name}\n"
            
            if embed.title:
                text += f"📌 {embed.title}\n"
            
            if embed.description:
                text += f"{embed.description}\n"
            
            if embed.fields:
                for field in embed.fields:
                    text += f"{field.name}: {field.value}\n"
            
            if embed.footer and embed.footer.text:
                text += f"\n{embed.footer.text}"
            
            await send_message(text)
        
        # اگه Embed نبود، متن رو بفرست
        if message.content and not message.embeds:
            await send_message(f"📨 {message.author.name}:\n{message.content}")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")

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
