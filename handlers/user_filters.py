from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.db import get_filter
from utils.buttons import build_keyboard
from utils.series_db import search_series
from utils.group_db import search_groups, get_group_by_name
from handlers.series import send_series_card
from handlers.group import group_series_keyboard


def register_user_filter(app: Client):
    @app.on_message(filters.text & filters.private & ~filters.command([
        "start", "addseries", "listseries", "delseries", "editseries",
        "addgroup", "listgroups", "delgroup", "editgroup",
        "gfilter", "viewfilters", "delfilter", "request",
        "addkeyword", "delkeyword"
    ]))
    async def user_filter_handler(client, message: Message):
        keyword = message.text.strip().lower()

        # ── Check groups first ───────────────────────────────────────────────────
        group_results = await search_groups(keyword)
        if group_results:
            if len(group_results) == 1:
                group = group_results[0]
                keyboard = group_series_keyboard(group)
                caption = f"<b>📂 {group['name']}</b>"
                if group.get("description"):
                    caption += f"\n\n<i>{group['description']}</i>"
                caption += "\n\n<b>Select a series:</b>"
                if group.get("poster_file_id"):
                    await message.reply_photo(
                        photo=group["poster_file_id"],
                        caption=caption,
                        reply_markup=keyboard
                    )
                else:
                    await message.reply_text(caption, reply_markup=keyboard)
            else:
                buttons = []
                for g in group_results:
                    buttons.append([InlineKeyboardButton(
                        text=g["name"],
                        callback_data=f"showgroup:{g['name_lower']}"
                    )])
                await message.reply_text(
                    "<b>🔍 Multiple results found:</b>",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            return

        # ── Check individual series ──────────────────────────────────────────────
        series_results = await search_series(keyword)
        if series_results:
            bot_me = await client.get_me()
            if len(series_results) == 1:
                await send_series_card(message, series_results[0], bot_me.username)
            else:
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

        # ── Fall through to normal filters ───────────────────────────────────────
        data = await get_filter(keyword)
        if not data:
            return

        caption = data.get("caption", "")
        media_type = data.get("media_type")
        buttons = build_keyboard(data.get("buttons", []))
        file_id = data.get("file_id")

        if not caption.strip() and not file_id and not buttons:
            return await message.reply("❌ No content available for this filter.")

        safe_caption = caption if caption.strip() else "‎" if buttons else None

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

    # ── Callback: show a group when multiple group results ───────────────────────
    @app.on_callback_query(filters.regex(r"^showgroup:"))
    async def showgroup_callback(client, query):
        name_lower = query.data.split(":", 1)[1]
        group = await get_group_by_name(name_lower)
        if not group:
            return await query.answer("❌ Group not found.", show_alert=True)
        keyboard = group_series_keyboard(group)
        caption = f"<b>📂 {group['name']}</b>"
        if group.get("description"):
            caption += f"\n\n<i>{group['description']}</i>"
        caption += "\n\n<b>Select a series:</b>"
        if group.get("poster_file_id"):
            await query.message.reply_photo(
                photo=group["poster_file_id"],
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await query.message.reply_text(caption, reply_markup=keyboard)
        await query.answer()