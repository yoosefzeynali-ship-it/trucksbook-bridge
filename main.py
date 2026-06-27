import os
import aiohttp
import discord

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

CHANNEL_ID = 1087132698096705726

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


async def telegram(method, data=None):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"

    async with aiohttp.ClientSession() as session:

        async with session.post(url, data=data) as r:
            return await r.text()


async def send_message(text):

    await telegram(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": text
        }
    )


async def send_photo(url):

    await telegram(
        "sendPhoto",
        {
            "chat_id": CHAT_ID,
            "photo": url
        }
    )
    def embed_to_text(embed: discord.Embed):

    text = ""

    if embed.title:
        text += f"📦 {embed.title}\n\n"

    if embed.description:
        text += embed.description + "\n\n"

    for field in embed.fields:
        text += f"🔹 {field.name}\n{field.value}\n\n"

    if embed.footer and embed.footer.text:
        text += f"\n{embed.footer.text}"

    return text.strip()


@client.event
async def on_ready():
    print("=" * 50)
    print(f"Logged in as {client.user}")
    print("TrucksBook Bridge Started")
    print("=" * 50)


@client.event
async def on_message(message):

    # فقط کانال موردنظر
    if message.channel.id != CHANNEL_ID:
        return

    # فقط Webhook
    if message.webhook_id is None:
        return

    print(f"Webhook Message: {message.id}")

    try:

        # اگر متن داشت
        if message.content:
            await send_message(message.content)
                    # ===== Embedها =====
        for embed in message.embeds:

            text = embed_to_text(embed)

            if text:
                await send_message(text)

            # عکس اصلی Embed
            if embed.image and embed.image.url:
                await send_photo(embed.image.url)

            # Thumbnail
            elif embed.thumbnail and embed.thumbnail.url:
                await send_photo(embed.thumbnail.url)

        # ===== فایل‌ها =====
        for attachment in message.attachments:

            if attachment.content_type:

                if attachment.content_type.startswith("image"):

                    await send_photo(attachment.url)

                else:

                    await telegram(
                        "sendDocument",
                        {
                            "chat_id": CHAT_ID,
                            "document": attachment.url
                        }
                    )

    except Exception as e:

        print("ERROR:", e)


client.run(DISCORD_TOKEN)
