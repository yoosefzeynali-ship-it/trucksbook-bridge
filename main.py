```python
import os
import re
import html
import threading

import aiohttp
import discord
from discord import Intents
from flask import Flask


# ============================================================
# Environment Variables
# ============================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN not found")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN not found")

if not CHAT_ID:
    raise RuntimeError("CHAT_ID not found")


# ============================================================
# Configuration
# ============================================================

ALLOWED_CHANNELS = {
    1119726229621321819,
    1087132698096705726
}


# ============================================================
# Discord Client
# ============================================================

intents = Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# ============================================================
# Telegram HTTP Session
# ============================================================

session = None


async def get_session():

    global session

    if session is None or session.closed:
        session = aiohttp.ClientSession()

    return session


# ============================================================
# Telegram API
# ============================================================

async def telegram(method: str, data: dict):

    s = await get_session()

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"

    async with s.post(url, data=data) as resp:

        result = await resp.text()

        if resp.status != 200:

            print("=" * 60)
            print("❌ TELEGRAM ERROR")
            print("Status:", resp.status)
            print(result)
            print("=" * 60)

        return result


# ============================================================
# Send Telegram Message
# ============================================================

async def send_message(text):

    if not text:
        return

    await telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
    )


# ============================================================
# Send Telegram Photo
# ============================================================

async def send_photo(url, caption=None):

    data = {
        "chat_id": CHAT_ID,
        "photo": url
    }

    if caption:

        data["caption"] = html.escape(caption)
        data["parse_mode"] = "HTML"

    await telegram(
        "sendPhoto",
        data
    )


# ============================================================
# Send Telegram Document
# ============================================================

async def send_document(url, caption=None):

    data = {
        "chat_id": CHAT_ID,
        "document": url
    }

    if caption:

        data["caption"] = html.escape(caption)
        data["parse_mode"] = "HTML"

    await telegram(
        "sendDocument",
        data
    )


# ============================================================
# Emoji Conversion
# ============================================================

EMOJI_MAP = {

    ":flag_ir:": "🇮🇷",
    ":flag_us:": "🇺🇸",
    ":flag_gb:": "🇬🇧",
    ":flag_uk:": "🇬🇧",
    ":flag_de:": "🇩🇪",
    ":flag_fr:": "🇫🇷",
    ":flag_it:": "🇮🇹",
    ":flag_es:": "🇪🇸",
    ":flag_pl:": "🇵🇱",
    ":flag_nl:": "🇳🇱",
    ":flag_be:": "🇧🇪",
    ":flag_tr:": "🇹🇷",
    ":flag_ru:": "🇷🇺",

    ":arrow_up:": "⬆️",
    ":arrow_double_up:": "⏫",

    ":white_check_mark:": "✅",
    ":x:": "❌",
    ":warning:": "⚠️"
}


emoji_pattern = re.compile(
    "|".join(
        re.escape(x)
        for x in EMOJI_MAP.keys()
    )
)


def convert_emoji(text):

    if not text:
        return ""

    return emoji_pattern.sub(
        lambda m: EMOJI_MAP[m.group(0)],
        text
    )


# ============================================================
# Clean Text
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = convert_emoji(text)

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# Format Job Details
# ============================================================

def format_details(value):

    value = clean_text(value)

    if not value:
        return []

    lines = [
        line.strip()
        for line in value.splitlines()
        if line.strip()
    ]

    result = []

    for line in lines:

        # ----------------------------------------------------
        # Cargo
        # ----------------------------------------------------

        if line.lower().startswith("cargo:"):

            result.append(
                f"📦 <b>Details:</b> {html.escape(line)}"
            )

        else:

            result.append(
                html.escape(line)
            )

    return result


# ============================================================
# Discord Embed → Telegram Job Format
# ============================================================

def embed_to_text(embed: discord.Embed, driver=None):

    lines = []


    # ========================================================
    # Driver
    # ========================================================

    if driver:

        lines.append(
            f"👤 {html.escape(driver)}"
        )

        lines.append("")


    # ========================================================
    # Job Title
    # ========================================================

    if embed.title:

        title = clean_text(embed.title)

        lines.append(
            f"📌 {html.escape(title)}"
        )


    # ========================================================
    # Job Description
    # ========================================================

    if embed.description:

        description = clean_text(
            embed.description
        )

        if description:

            lines.append(
                f"🎗 {html.escape(description)}"
            )


    # ========================================================
    # Embed Fields
    # ========================================================

    for field in embed.fields:

        name = clean_text(
            field.name or ""
        )

        value = clean_text(
            field.value or ""
        )

        if not value:
            continue


        # ====================================================
        # FROM
        # ====================================================

        if name.lower() == "from":

            lines.append(
                f"🟢 <b>From:</b> {html.escape(value)}"
            )


        # ====================================================
        # TO
        # ====================================================

        elif name.lower() == "to":

            lines.append(
                f"🔴 <b>To:</b> {html.escape(value)}"
            )


        # ====================================================
        # DETAILS
        # ====================================================

        elif name.lower() == "details":

            details = format_details(value)

            lines.extend(details)


        # ====================================================
        # Other Fields
        # ====================================================

        else:

            escaped_name = html.escape(name)

            escaped_value = html.escape(value)

            lines.append(
                f"<b>{escaped_name}:</b> {escaped_value}"
            )


    # ========================================================
    # Footer
    # ========================================================

    if embed.footer and embed.footer.text:

        footer = clean_text(
            embed.footer.text
        )

        if footer:

            lines.append("")
            lines.append(
                "--------------------"
            )
            lines.append(
                html.escape(footer)
            )


    return "\n".join(lines).strip()


# ============================================================
# Detect Driver Name
# ============================================================

def get_driver_name(message):

    for embed in message.embeds:

        if embed.author and embed.author.name:

            return embed.author.name


    if message.author and message.author.name:

        name = message.author.name

        if "webhook" not in name.lower():

            return name


    return None


# ============================================================
# Discord Ready Event
# ============================================================

@client.event
async def on_ready():

    print()
    print("=" * 60)
    print("✅ DISCORD BOT ONLINE")
    print(f"Bot     : {client.user}")
    print(f"Guilds  : {len(client.guilds)}")
    print("=" * 60)

    print("Allowed channels:")

    for channel_id in ALLOWED_CHANNELS:

        channel = client.get_channel(
            channel_id
        )

        if channel:

            print(
                f"✅ {channel.guild.name} "
                f"-> #{channel.name} "
                f"-> {channel.id}"
            )

        else:

            print(
                f"❌ Cannot access channel "
                f"{channel_id}"
            )

    print("=" * 60)


# ============================================================
# Discord Message Event
# ============================================================

@client.event
async def on_message(message):

    print()
    print("=" * 60)
    print("📨 DISCORD MESSAGE EVENT RECEIVED")
    print("=" * 60)

    print(
        f"Author       : {message.author}"
    )

    print(
        f"Author ID    : {message.author.id}"
    )

    print(
        f"Channel      : {message.channel}"
    )

    print(
        f"Channel ID   : {message.channel.id}"
    )

    print(
        f"Content      : {message.content}"
    )

    print(
        f"Bot Message  : {message.author.bot}"
    )

    print(
        f"Webhook ID   : {message.webhook_id}"
    )

    print(
        f"Embeds       : {len(message.embeds)}"
    )

    print(
        f"Attachments  : {len(message.attachments)}"
    )

    print("=" * 60)


    # ========================================================
    # Ignore own messages
    # ========================================================

    if message.author.id == client.user.id:

        print(
            "⏭️ Ignored: message sent by this bot"
        )

        return


    # ========================================================
    # Allowed Channel
    # ========================================================

    if message.channel.id not in ALLOWED_CHANNELS:

        print(
            "⏭️ Ignored: channel is not allowed"
        )

        return


    print(
        "✅ TARGET CHANNEL MATCHED"
    )


    driver = get_driver_name(
        message
    )


    try:

        # ====================================================
        # Normal Discord Message
        # ====================================================

        if message.content.strip():

            text = convert_emoji(
                message.content
            )

            text = html.escape(text)

            if driver:

                text = (
                    f"👤 {html.escape(driver)}\n\n"
                    f"{text}"
                )

            await send_message(
                text
            )


        # ====================================================
        # Discord Embeds
        # ====================================================

        for embed in message.embeds:

            text = embed_to_text(
                embed,
                driver
            )

            if text:

                print(
                    "➡️ Sending formatted job to Telegram..."
                )

                await send_message(
                    text
                )

                print(
                    "✅ Formatted job sent"
                )


            # ------------------------------------------------
            # Embed Image
            # ------------------------------------------------

            if (
                embed.image
                and embed.image.url
            ):

                await send_photo(
                    embed.image.url,
                    driver
                )


            # ------------------------------------------------
            # Embed Thumbnail
            # ------------------------------------------------

            elif (
                embed.thumbnail
                and embed.thumbnail.url
            ):

                await send_photo(
                    embed.thumbnail.url,
                    driver
                )


        # ====================================================
        # Attachments
        # ====================================================

        for attachment in message.attachments:

            ctype = (
                attachment.content_type
                or ""
            )

            print(
                f"📎 Attachment: "
                f"{attachment.filename}"
            )


            if ctype.startswith("image"):

                await send_photo(
                    attachment.url,
                    attachment.filename
                )

            else:

                await send_document(
                    attachment.url,
                    attachment.filename
                )


        print(
            "✅ MESSAGE PROCESSING COMPLETED"
        )


    except Exception as e:

        print()
        print("=" * 60)
        print("❌ MESSAGE PROCESSING ERROR")
        print("=" * 60)

        print(
            "Error type:",
            type(e).__name__
        )

        print(
            "Error:",
            e
        )

        print("=" * 60)


# ============================================================
# Flask Web Server
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():

    return (
        "HaulMP Bridge is running",
        200
    )


@app.route("/health")
def health():

    return (
        "OK",
        200
    )


# ============================================================
# Start Flask
# ============================================================

def run_web_server():

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    print()
    print("=" * 60)
    print("🌐 STARTING RENDER WEB SERVER")
    print(
        f"Port: {port}"
    )
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# ============================================================
# Start Everything
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🚀 STARTING HAULMP BRIDGE")
    print("=" * 60)


    # ========================================================
    # Start Flask
    # ========================================================

    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()


    # ========================================================
    # Start Discord Bot
    # ========================================================

    client.run(
        DISCORD_TOKEN
    )
```

با Embed مشابه پیام اول، خروجی باید به این فرم نزدیک شود:

```text
👤 yoosef

📌 Job delivery #67719722
🎗 [Real] - 41 km
🟢 From: 🇺🇸 Bakersfield
🔴 To: 🇺🇸 Bakersfield
📦 Details: Cargo: Product Samples
Accepted distance: 41 km
Profit: 254 $
Truck: Ford F150_23
Statistics: Real
Rank within company: 1st

--------------------
TrucksBook
```

و اگر Footer خود Discord شامل `⚡️@Caspiancboy⚡️` باشد، همان را نگه می‌دارد.

**یک نکته مهم:** در نمونه‌ای که دادی `From`، `To` و `Details` را دیگر به‌صورت خطوط جداگانه نمی‌خواهیم؛ منطق جدید دقیقاً این سه Field را شناسایی و به قالب تک‌خطی تبدیل می‌کند. در کد قبلی این Fieldها به‌صورت جداگانه `<b>نام فیلد</b>` و سپس مقدارشان ارسال می‌شد، که دلیل اصلی تفاوت خروجی بود.
