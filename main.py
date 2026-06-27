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

# ===== استخراج اسم راننده با روش‌های مختلف =====
def extract_driver_name(message):
    """
    استخراج اسم راننده از پیام با روش‌های مختلف
    """
    driver_names = []
    
    # ===== روش ۱: از message.mentions =====
    for user in message.mentions:
        driver_names.append(user.display_name)
        print(f"✅ روش ۱ - منشن: {user.display_name}")
    
    # ===== روش ۲: از محتوای متن با Regex =====
    if not driver_names and message.content:
        # الگوی منشن: <@!USER_ID> یا <@USER_ID>
        user_mention_pattern = r'<@!?(\d+)>'
        matches = re.findall(user_mention_pattern, message.content)
        
        for user_id in matches:
            user = client.get_user(int(user_id))
            if user:
                driver_names.append(user.display_name)
                print(f"✅ روش ۲ - Regex منشن: {user.display_name}")
    
    # ===== روش ۳: از Embed =====
    if not driver_names:
        for embed in message.embeds:
            # بررسی عنوان
            if embed.title:
                # الگوی [نام](لینک)
                link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
                link_matches = re.findall(link_pattern, embed.title)
                if link_matches:
                    driver_names.extend(link_matches)
                    print(f"✅ روش ۳ - لینک در عنوان: {link_matches}")
            
            # بررسی توضیحات
            if embed.description:
                link_matches = re.findall(r'\[([^\]]+)\]\([^\)]+\)', embed.description)
                if link_matches:
                    driver_names.extend(link_matches)
                    print(f"✅ روش ۳ - لینک در توضیحات: {link_matches}")
            
            # بررسی فیلدها
            for field in embed.fields:
                link_matches = re.findall(r'\[([^\]]+)\]\([^\)]+\)', field.value)
                if link_matches:
                    driver_names.extend(link_matches)
                    print(f"✅ روش ۳ - لینک در فیلد: {link_matches}")
    
    # ===== روش ۴: از Webhook نام =====
    if not driver_names and message.webhook_id:
        webhook_name = message.author.name
        if webhook_name and "Webhook" not in webhook_name:
            driver_names.append(webhook_name)
            print(f"✅ روش ۴ - اسم Webhook: {webhook_name}")
    
    # ===== روش ۵: از محتوای متن (آخرین کلمه قبل از Embed) =====
    if not driver_names and message.content:
        # اگه متن قبل از Embed باشه
        parts = message.content.split()
        if parts:
            # ممکنه آخرین کلمه اسم باشه
            last_word = parts[-1]
            if last_word and not last_word.startswith('<'):
                driver_names.append(last_word)
                print(f"✅ روش ۵ - آخرین کلمه: {last_word}")
    
    return driver_names

# ===== تبدیل Embed به متن =====
def embed_to_text(embed, driver_names=None):
    parts = []
    
    # ===== اضافه کردن اسم راننده =====
    if driver_names:
        for name in driver_names:
            parts.append(f"<b>👤 {name}</b>")
            parts.append("")
    
    # ===== محتوای اصلی =====
    if embed.title:
        # پاک کردن لینک‌ها از عنوان
        clean_title = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', embed.title)
        parts.append(f"<b>{clean_title}</b>")
    
    if embed.description:
        clean_desc = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', embed.description)
        parts.append(clean_desc)
    
    # فیلدها
    if embed.fields:
        for field in embed.fields:
            if field.name and field.value:
                clean_value = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', field.value)
                parts.append(f"<b>{field.name}:</b> {clean_value}")
    
    # Footer
    if embed.footer and embed.footer.text:
        clean_footer = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', embed.footer.text)
        parts.append(f"\n{clean_footer}")
    
    return "\n".join(parts) if parts else None

# ===== رویداد پیام =====
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    try:
        # ===== دیباگ کامل =====
        print("\n" + "=" * 60)
        print(f"📨 نویسنده: {message.author} (ID: {message.author.id})")
        print(f"📝 محتوای خام: {repr(message.content)}")
        print(f"🔗 Webhook ID: {message.webhook_id}")
        print(f"📊 تعداد Embeds: {len(message.embeds)}")
        
        # نمایش همه Embedها
        for i, embed in enumerate(message.embeds):
            print(f"\n--- Embed {i+1} ---")
            print(f"عنوان: {repr(embed.title)}")
            print(f"توضیحات: {repr(embed.description)}")
            if embed.fields:
                for field in embed.fields:
                    print(f"فیلد: {repr(field.name)} = {repr(field.value)}")
            print(f"فوتر: {repr(embed.footer.text) if embed.footer else None}")
        
        print(f"👥 منشن‌ها: {[user.display_name for user in message.mentions]}")
        print("=" * 60 + "\n")
        
        # ===== استخراج اسم راننده =====
        driver_names = extract_driver_name(message)
        
        # ===== اگر اسم پیدا نشد، از مقدار پیش‌فرض استفاده کن =====
        if not driver_names:
            driver_names = ["راننده"]
            print("⚠️ اسمی پیدا نشد، از پیش‌فرض استفاده شد")
        
        # ===== Embedها =====
        for embed in message.embeds:
            text = embed_to_text(embed, driver_names)
            if text:
                await send_message(text)
        
        # ===== متن اصلی =====
        if message.content and not message.embeds:
            # پاک کردن منشن‌ها از متن
            clean_content = re.sub(r'<@!?(\d+)>', '', message.content).strip()
            name_text = "، ".join(driver_names)
            await send_message(f"<b>👤 {name_text}</b>\n{clean_content}")
        
        # ===== فایل‌ها =====
        for attachment in message.attachments:
            name_text = "، ".join(driver_names)
            caption = f"<b>👤 {name_text}</b>\n📎 {attachment.filename}"
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
