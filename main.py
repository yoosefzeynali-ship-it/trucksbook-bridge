@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    try:
        # ===== دیباگ برای دیدن ساختار کامل =====
        print("\n" + "=" * 60)
        print(f"📨 نویسنده پیام: {message.author}")
        print(f"📝 محتوای خام: {repr(message.content)}")
        print(f"🔗 Webhook ID: {message.webhook_id}")
        print(f"📊 تعداد Embeds: {len(message.embeds)}")
        
        for i, embed in enumerate(message.embeds):
            print(f"\n--- Embed {i+1} ---")
            print(f"عنوان: {repr(embed.title)}")
            print(f"توضیحات: {repr(embed.description)}")
            
            # ===== بررسی Author =====
            if embed.author:
                print(f"👤 نویسنده Embed:")
                print(f"  - نام: {repr(embed.author.name)}")
                print(f"  - لینک: {repr(embed.author.url)}")
                print(f"  - آیکون: {repr(embed.author.icon_url)}")
            else:
                print("👤 نویسنده Embed: ندارد")
            
            # فیلدها
            if embed.fields:
                for field in embed.fields:
                    print(f"فیلد: {repr(field.name)} = {repr(field.value)}")
            
            print(f"فوتر: {repr(embed.footer.text) if embed.footer else None}")
        
        print("=" * 60 + "\n")
        
        # ===== استخراج اسم از Embed Author =====
        driver_names = []
        
        for embed in message.embeds:
            # روش ۱: از Author Embed
            if embed.author and embed.author.name:
                author_name = embed.author.name
                # پاک کردن لینک‌ها از اسم
                clean_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', author_name)
                if clean_name and "Webhook" not in clean_name:
                    driver_names.append(clean_name)
                    print(f"✅ اسم از Embed Author: {clean_name}")
            
            # روش ۲: از Title (اگر Author نبود)
            if not driver_names and embed.title:
                # ممکنه اسم توی عنوان باشه
                clean_title = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', embed.title)
                if clean_title and "TrucksBook" not in clean_title:
                    driver_names.append(clean_title)
                    print(f"✅ اسم از Title: {clean_title}")
        
        # روش ۳: از Webhook Name
        if not driver_names and message.webhook_id:
            webhook_name = message.author.name
            if webhook_name and "Webhook" not in webhook_name:
                driver_names.append(webhook_name)
                print(f"✅ اسم از Webhook: {webhook_name}")
        
        # روش ۴: از Mentions
        if not driver_names:
            for user in message.mentions:
                driver_names.append(user.display_name)
                print(f"✅ اسم از Mention: {user.display_name}")
        
        # اگر هیچ اسمی پیدا نشد
        if not driver_names:
            driver_names = ["راننده"]
            print("⚠️ اسمی پیدا نشد، از پیش‌فرض استفاده شد")
        
        # ===== ارسال به تلگرام =====
        for embed in message.embeds:
            # ساخت متن با استفاده از Embed
            parts = []
            
            # اسم راننده
            name_text = "، ".join(driver_names)
            parts.append(f"<b>👤 {name_text}</b>")
            parts.append("")
            
            # عنوان
            if embed.title:
                clean_title = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', embed.title)
                parts.append(f"<b>{clean_title}</b>")
            
            # توضیحات
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
            
            text = "\n".join(parts)
            if text:
                await send_message(text)
        
        # ===== متن اصلی =====
        if message.content and not message.embeds:
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
