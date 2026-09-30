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

GROUP_TAG = "⚡️@Caspiancboy⚡️"


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
# HTML Escape
# ============================================================

def escape_html(text):
    if text is None:
        return ""

    return html.escape(str(text), quote=False)


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
        data["caption"] = escape_html(caption)
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
        data["caption"] = escape_html(caption)
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
        str(text)
    )


# ============================================================
# Clean Text
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = convert_emoji(text)

    # Normalize Windows line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove trailing spaces from every line
    text = "\n".join(
        line.rstrip()
        for line in text.split("\n")
    )

    # Remove excessive spaces inside a line
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# Format Details
# ============================================================

def format_details(value):
    value = clean_text(value)

    if not value:
        return []

    raw_lines = value.splitlines()

    lines = []

    for line in raw_lines:
        line = line.strip()

        if not line:
            continue

        lines.append(line)

    if not lines:
        return []

    result = []

    first_line = lines[0]

    # First line of Details:
    # 📦 Details: Cargo: ...
    result.append(
        f"📦 Details: {escape_html(first_line)}"
    )

    # Remaining lines stay exactly in the same order.
    for line in lines[1:]:
        result.append(
            escape_html(line)
        )

    return result


# ============================================================
# Discord Embed -> Telegram Job Format
# ============================================================

def embed_to_text(embed: discord.Embed, driver=None):

    lines = []

    # ========================================================
    # Driver
    # ========================================================

    if driver:
        lines.append(
            f"👤 {escape_html(driver)}"
        )
        lines.append("")


    # ========================================================
    # Job Title
    # ========================================================

    if embed.title:
        title = clean_text(embed.title)

        if title:
            lines.append(
                f"📌 {escape_html(title)}"
            )


    # ========================================================
    # Job Description
    # ========================================================

    if embed.description:
        description = clean_text(embed.description)

        if description:
            lines.append(
                f"🎗 {escape_html(description)}"
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

        field_name = name.lower().strip()


        # ====================================================
        # FROM
        # ====================================================

        if field_name == "from":

            lines.append(
                f"🟢 From: {escape_html(value)}"
            )


        # ====================================================
        # TO
        # ====================================================

        elif field_name == "to":

            lines.append(
                f"🔴 To: {escape_html(value)}"
            )


        # ====================================================
        # DETAILS
        # ====================================================

        elif field_name == "details":

            details = format_details(value)

            lines.extend(details)


        # ====================================================
        # OTHER FIELDS
        # ====================================================

        else:

            escaped_name = escape_html(name)
            escaped_value = escape_html(value)

            lines.append(
                f"{escaped_name}: {escaped_value}"
            )


    # ========================================================
    # Footer
    # ========================================================

    footer_text = ""

    if embed.footer and embed.footer.text:
        footer_text = clean_text(
            embed.footer.text
        )

    if footer_text:
        lines.append("")
        lines.append(
            escape_html(footer_text)
        )

    # ========================================================
    # Group Tag
    # ========================================================

    if GROUP_TAG:
        lines.append("")
        lines.append(
            escape_html(GROUP_TAG)
        )


    # ========================================================
    # Final Cleanup
    # ========================================================

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
    # Ignore Own Messages
    # ========================================================

    if client.user and message.author.id == client.user.id:

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

            text = escape_html(text)

            if driver:

                text = (
                    f"👤 {escape_html(driver)}\n\n"
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

                print(
                    "Telegram text:"
                )

                print(text)

                await send_message(
                    text
                )

                print(
                    "✅ Formatted job sent"
                )


            # ================================================
            # Embed Image
            # ================================================

            if (
                embed.image
                and embed.image.url
            ):

                await send_photo(
                    embed.image.url,
                    driver
                )


            # ================================================
            # Embed Thumbnail
            # ================================================

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
