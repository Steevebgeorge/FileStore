from pyrogram import Client, filters
from pyrogram.types import Message
from utils.db import get_filter
from utils.buttons import build_keyboard
from utils.series_db import search_series
from handlers.series import send_series_card


# ✅ Code for showing global filter to users
def register_user_filter(app: Client):
    @app.on_message(filters.text & filters.private & ~filters.command("start"))
    async def user_filter_handler(client, message: Message):
        keyword = message.text.strip().lower()
        series_results = await search_series(keyword)
        if series_results:
            bot_me = await client.get_me()
            if len(series_results) == 1:
                # Only one match — show it directly
                await send_series_card(message, series_results[0], bot_me.username)
            else:
                # Multiple matches — list them with buttons to pick
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                buttons = []
                for s in series_results:
                    buttons.append([InlineKeyboardButton(
                        text=s["title"],
                        callback_data=f"showseries:{s['title_lower']}"
                    )])
                await message.reply_text(
                    "<b>🔍 Multiple results found:</b>",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            return
        # ── Fall through to normal filters ───────────────────────────────

        data = await get_filter(keyword)
        if not data:
            return

        caption = data.get("caption", "")
        media_type = data.get("media_type")
        buttons = build_keyboard(data.get("buttons", []))
        file_id = data.get("file_id")

        # 🛡️ Protect against Telegram's [400 MESSAGE_EMPTY]
        if not caption.strip() and not file_id and not buttons:
            return await message.reply("❌ No content available for this filter.")

        # 🧠 If no media and no caption, but buttons are present, use invisible char
        safe_caption = caption if caption.strip() else "‎" if buttons else None

        # 📤 Send appropriate message
        if media_type == "photo":
            await message.reply_photo(photo=file_id, caption=safe_caption, reply_markup=buttons)
        elif media_type == "video":
            await message.reply_video(video=file_id, caption=safe_caption, reply_markup=buttons)
        elif media_type == "document":
            await message.reply_document(document=file_id, caption=safe_caption, reply_markup=buttons)
        elif media_type == "animation":
            await message.reply_animation(animation=file_id, caption=safe_caption, reply_markup=buttons)
        elif media_type == "sticker":
            await message.reply_sticker(sticker=file_id)
        elif media_type == "voice":
            await message.reply_voice(voice=file_id, caption=safe_caption)
        elif media_type == "audio":
            await message.reply_audio(audio=file_id, caption=safe_caption)
        else:
            if safe_caption:
                await message.reply_text(safe_caption, reply_markup=buttons)
