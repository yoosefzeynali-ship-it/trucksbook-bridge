import os
import discord
from telegram import Bot

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
CHANNEL_ID = 1087132698096705726

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

bot = Bot(token=TELEGRAM_TOKEN)


async def send_embed(embed):
    text = ""

    if embed.title:
        text += f"📦 {embed.title}\n\n"

    if embed.description:
        text += embed.description + "\n\n"

    for field in embed.fields:
        text += f"**{field.name}**\n{field.value}\n\n"

    if embed.footer:
        text += f"\n{embed.footer.text}"

    if text.strip():
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode="Markdown"
        )

    if embed.image.url:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=embed.image.url
        )

    elif embed.thumbnail.url:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=embed.thumbnail.url
        )
      @client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):

    if message.channel.id != CHANNEL_ID:
        return

    # فقط پیام‌های Webhook
    if message.webhook_id is None:
        return

    try:

        # اگر متن معمولی داشت
        if message.content:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message.content
            )

        # فایل‌ها
        for attachment in message.attachments:

            if attachment.content_type and attachment.content_type.startswith("image"):

                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=attachment.url
                )

            else:

                await bot.send_document(
                    chat_id=CHAT_ID,
                    document=attachment.url
                )

        # Embedها
        for embed in message.embeds:
            await send_embed(embed)

    except Exception as e:
        print(e)
      client.run(DISCORD_TOKEN)
