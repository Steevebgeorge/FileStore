from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import ADMIN_IDS
from utils.series_db import (
    save_series, search_series, get_series_by_title,
    list_all_series, delete_series,
    update_series_title, update_series_description, update_series_poster,
    add_season_to_series, remove_season_from_series,
    add_quality_to_season, remove_quality_from_season,
    add_keyword_to_series, remove_keyword_from_series
)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def seasons_keyboard(seasons: dict, title_lower: str):
    buttons = []
    row = []
    for season in sorted(seasons.keys()):
        row.append(InlineKeyboardButton(
            text=season,
            callback_data=f"season:{title_lower}:{season}"
        ))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def quality_keyboard(qualities: dict, title_lower: str, season: str):
    buttons = []
    row = []
    for quality, link in qualities.items():
        row.append(InlineKeyboardButton(text=quality, url=link))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text="⬅️ Back",
        callback_data=f"backtoseasons:{title_lower}"
    )])
    return InlineKeyboardMarkup(buttons)

async def send_series_card(message: Message, series: dict, bot_username: str):
    title = series["title"]
    description = series.get("description", "")
    poster = series.get("poster_file_id")
    seasons = series.get("seasons", {})
    keyboard = seasons_keyboard(seasons, series["title_lower"])
    caption = f"<b>🎬 {title}</b>"
    if description:
        caption += f"\n\n<i>{description}</i>"
    caption += "\n\n<b>Select a season:</b>"
    if poster:
        await message.reply_photo(photo=poster, caption=caption, reply_markup=keyboard)
    else:
        await message.reply_text(caption, reply_markup=keyboard)

def register_series(app: Client):

    # ── /addseries ──────────────────────────────────────────────────────────────
    @app.on_message(filters.command("addseries") & filters.private)
    async def addseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")

        await message.reply_text(
            "📝 <b>Step 1/5 — Title</b>\n\n"
            "Send the title of the series.\n"
            "Example: <code>Game of Thrones</code>"
        )
        title_msg = await app.listen(message.chat.id)
        title = title_msg.text.strip()

        await message.reply_text(
            "🔍 <b>Step 2/5 — Keywords</b>\n\n"
            "Send extra search keywords separated by commas.\n"
            "The title is already included automatically.\n\n"
            "Example: <code>GOT, got series, game of thrones hbo</code>\n\n"
            "Or send <code>skip</code> to use only the title."
        )
        keywords_msg = await app.listen(message.chat.id)
        keywords = [] if keywords_msg.text.strip().lower() == "skip" else [
            k.strip() for k in keywords_msg.text.split(",") if k.strip()
        ]

        await message.reply_text(
            "🖼 <b>Step 3/5 — Poster</b>\n\nSend the poster image."
        )
        poster_msg = await app.listen(message.chat.id)
        if not poster_msg.photo:
            return await message.reply_text("❌ No photo received. Start over with /addseries.")
        poster_file_id = poster_msg.photo.file_id

        await message.reply_text(
            "📄 <b>Step 4/5 — Description</b>\n\n"
            "Send a short description or send <code>skip</code>."
        )
        desc_msg = await app.listen(message.chat.id)
        description = "" if desc_msg.text.strip().lower() == "skip" else desc_msg.text.strip()

        await message.reply_text(
            "🗂 <b>Step 5/5 — Seasons</b>\n\nHow many seasons? Send a number."
        )
        count_msg = await app.listen(message.chat.id)
        try:
            season_count = int(count_msg.text.strip())
        except ValueError:
            return await message.reply_text("❌ Invalid number. Start over with /addseries.")

        seasons_data = {}
        for i in range(1, season_count + 1):
            season_name = f"S{i}"
            await message.reply_text(
                f"📂 <b>{season_name}</b> — Qualities available?\n\n"
                f"Comma-separated: <code>720p, 1080p, 2160p</code>"
            )
            qual_msg = await app.listen(message.chat.id)
            qualities = [q.strip() for q in qual_msg.text.split(",") if q.strip()]
            season_links = {}
            for quality in qualities:
                await message.reply_text(
                    f"🔗 Full link for <b>{season_name} — {quality}</b>\n\n"
                    f"Example: <code>https://t.me/Cinemacompanyfilebot?start=Z2V0...</code>"
                )
                link_msg = await app.listen(message.chat.id)
                season_links[quality] = link_msg.text.strip()
            seasons_data[season_name] = season_links

        await save_series(title, poster_file_id, description, seasons_data, keywords)
        all_kw = [title.lower()] + keywords
        await message.reply_text(
            f"✅ <b>{title}</b> saved!\n\n"
            f"🔍 Keywords: <code>{', '.join(all_kw)}</code>\n"
            f"📂 Seasons: {', '.join(seasons_data.keys())}"
        )

    # ── /listseries ─────────────────────────────────────────────────────────────
    @app.on_message(filters.command("listseries") & filters.private)
    async def listseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        all_series = await list_all_series()
        if not all_series:
            return await message.reply_text("⚠️ No series saved yet.")
        lines = []
        for title, keywords in all_series:
            lines.append(f"• <b>{title}</b>\n  🔍 <code>{', '.join(keywords)}</code>")
        await message.reply_text("<b>📺 Saved Series:</b>\n\n" + "\n\n".join(lines))

    # ── /delseries ──────────────────────────────────────────────────────────────
    @app.on_message(filters.command("delseries") & filters.private)
    async def delseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text("Usage: <code>/delseries Game of Thrones</code>")
        title_lower = parts[1].strip().lower()
        if await delete_series(title_lower):
            await message.reply_text("✅ Series deleted.")
        else:
            await message.reply_text("❌ Series not found. Use /listseries to check exact titles.")

    # ── /editseries ─────────────────────────────────────────────────────────────
    # Usage examples:
    # /editseries Dexter | settitle | Dexter (2006)
    # /editseries Dexter | setdesc | A serial killer drama
    # /editseries Dexter | setposter        (then send photo)
    # /editseries Dexter | addseason | S5 | 720p, 1080p
    # /editseries Dexter | delseason | S5
    # /editseries Dexter | addquality | S1 | 2160p | https://t.me/...
    # /editseries Dexter | delquality | S1 | 720p
    # /editseries Dexter | addkeyword | dexter morgan, serial killer show
    # /editseries Dexter | delkeyword | dexter morgan
    @app.on_message(filters.command("editseries") & filters.private)
    async def editseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")

        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(
                "<b>📝 /editseries usage:</b>\n\n"
                "<code>/editseries Title | action | value</code>\n\n"
                "<b>Actions:</b>\n"
                "• <code>settitle | New Title</code>\n"
                "• <code>setdesc | New description</code>\n"
                "• <code>setposter</code> (then send photo)\n"
                "• <code>addseason | S5 | 720p, 1080p</code>\n"
                "• <code>delseason | S5</code>\n"
                "• <code>addquality | S1 | 2160p | https://t.me/...</code>\n"
                "• <code>delquality | S1 | 720p</code>\n"
                "• <code>addkeyword | keyword1, keyword2</code>\n"
                "• <code>delkeyword | keyword1</code>"
            )

        raw = parts[1]
        segments = [s.strip() for s in raw.split("|")]

        if len(segments) < 2:
            return await message.reply_text("❌ Wrong format. See /editseries for usage.")

        title_lower = segments[0].lower()
        action = segments[1].lower()

        series = await get_series_by_title(title_lower)
        if not series:
            return await message.reply_text(
                f"❌ Series <b>{segments[0]}</b> not found.\n"
                f"Use /listseries to check exact titles."
            )

        # settitle
        if action == "settitle":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editseries Title | settitle | New Title</code>")
            await update_series_title(title_lower, segments[2])
            await message.reply_text(f"✅ Title updated to <b>{segments[2]}</b>.")

        # setdesc
        elif action == "setdesc":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editseries Title | setdesc | New description</code>")
            await update_series_description(title_lower, segments[2])
            await message.reply_text("✅ Description updated.")

        # setposter
        elif action == "setposter":
            await message.reply_text("🖼 Send the new poster image now.")
            poster_msg = await app.listen(message.chat.id)
            if not poster_msg.photo:
                return await message.reply_text("❌ No photo received.")
            await update_series_poster(title_lower, poster_msg.photo.file_id)
            await message.reply_text("✅ Poster updated.")

        # addseason
        elif action == "addseason":
            if len(segments) < 3:
                return await message.reply_text(
                    "Usage: <code>/editseries Title | addseason | S5 | 720p, 1080p</code>"
                )
            season_name = segments[2].upper()
            qualities = [q.strip() for q in (segments[3].split(",") if len(segments) > 3 else [])]
            if not qualities:
                return await message.reply_text(
                    "Usage: <code>/editseries Title | addseason | S5 | 720p, 1080p</code>"
                )
            season_links = {}
            for quality in qualities:
                await message.reply_text(
                    f"🔗 Send the full link for <b>{season_name} — {quality}</b>"
                )
                link_msg = await app.listen(message.chat.id)
                season_links[quality] = link_msg.text.strip()
            await add_season_to_series(title_lower, season_name, season_links)
            await message.reply_text(f"✅ <b>{season_name}</b> added to {series['title']}.")

        # delseason
        elif action == "delseason":
            if len(segments) < 3:
                return await message.reply_text(
                    "Usage: <code>/editseries Title | delseason | S5</code>"
                )
            season_name = segments[2].upper()
            await remove_season_from_series(title_lower, season_name)
            await message.reply_text(f"✅ <b>{season_name}</b> removed from {series['title']}.")

        # addquality
        elif action == "addquality":
            if len(segments) < 5:
                return await message.reply_text(
                    "Usage: <code>/editseries Title | addquality | S1 | 2160p | https://t.me/...</code>"
                )
            season_name = segments[2].upper()
            quality = segments[3]
            link = segments[4]
            await add_quality_to_season(title_lower, season_name, quality, link)
            await message.reply_text(
                f"✅ <b>{quality}</b> added to {series['title']} — {season_name}."
            )

        # delquality
        elif action == "delquality":
            if len(segments) < 4:
                return await message.reply_text(
                    "Usage: <code>/editseries Title | delquality | S1 | 720p</code>"
                )
            season_name = segments[2].upper()
            quality = segments[3]
            await remove_quality_from_season(title_lower, season_name, quality)
            await message.reply_text(
                f"✅ <b>{quality}</b> removed from {series['title']} — {season_name}."
            )

        # addkeyword
        elif action == "addkeyword":
            if len(segments) < 3:
                return await message.reply_text(
                    "Usage: <code>/editseries Title | addkeyword | kw1, kw2</code>"
                )
            new_kws = [k.strip() for k in segments[2].split(",") if k.strip()]
            added = []
            for kw in new_kws:
                if await add_keyword_to_series(title_lower, kw):
                    added.append(kw)
            await message.reply_text(
                f"✅ Keywords added: <code>{', '.join(added)}</code>" if added
                else "⚠️ Keywords already exist."
            )

        # delkeyword
        elif action == "delkeyword":
            if len(segments) < 3:
                return await message.reply_text(
                    "Usage: <code>/editseries Title | delkeyword | kw1, kw2</code>"
                )
            rm_kws = [k.strip() for k in segments[2].split(",") if k.strip()]
            removed = []
            skipped = []
            for kw in rm_kws:
                if kw == title_lower:
                    skipped.append(kw)
                    continue
                if await remove_keyword_from_series(title_lower, kw):
                    removed.append(kw)
                else:
                    skipped.append(kw)
            reply = ""
            if removed:
                reply += f"✅ Removed: <code>{', '.join(removed)}</code>\n"
            if skipped:
                reply += f"⚠️ Not found or protected: <code>{', '.join(skipped)}</code>"
            await message.reply_text(reply or "⚠️ Nothing changed.")

        else:
            await message.reply_text(f"❌ Unknown action <code>{action}</code>. See /editseries for usage.")

    # ── Callbacks ────────────────────────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^season:"))
    async def season_callback(client, query: CallbackQuery):
        parts = query.data.split(":", 2)
        if len(parts) < 3:
            return await query.answer("❌ Invalid data.", show_alert=True)
        title_lower, season = parts[1], parts[2]
        series = await get_series_by_title(title_lower)
        if not series:
            return await query.answer("❌ Series not found.", show_alert=True)
        qualities = series["seasons"].get(season, {})
        if not qualities:
            return await query.answer("❌ No qualities found.", show_alert=True)
        keyboard = quality_keyboard(qualities, title_lower, season)
        caption = f"<b>🎬 {series['title']} — {season}</b>\n\n<b>Select quality:</b>"
        try:
            await query.message.edit_caption(caption=caption, reply_markup=keyboard)
        except Exception:
            try:
                await query.message.edit_text(text=caption, reply_markup=keyboard)
            except Exception:
                await query.message.reply_text(caption, reply_markup=keyboard)
        await query.answer()

    @app.on_callback_query(filters.regex(r"^backtoseasons:"))
    async def backtoseasons_callback(client, query: CallbackQuery):
        title_lower = query.data.split(":", 1)[1]
        series = await get_series_by_title(title_lower)
        if not series:
            return await query.answer("❌ Series not found.", show_alert=True)
        keyboard = seasons_keyboard(series["seasons"], title_lower)
        caption = f"<b>🎬 {series['title']}</b>"
        if series.get("description"):
            caption += f"\n\n<i>{series['description']}</i>"
        caption += "\n\n<b>Select a season:</b>"
        try:
            await query.message.edit_caption(caption=caption, reply_markup=keyboard)
        except Exception:
            try:
                await query.message.edit_text(text=caption, reply_markup=keyboard)
            except Exception:
                await query.message.reply_text(caption, reply_markup=keyboard)
        await query.answer()

    @app.on_callback_query(filters.regex(r"^showseries:"))
    async def showseries_callback(client, query: CallbackQuery):
        title_lower = query.data.split(":", 1)[1]
        series = await get_series_by_title(title_lower)
        if not series:
            return await query.answer("❌ Not found.", show_alert=True)
        bot_me = await client.get_me()
        await send_series_card(query.message, series, bot_me.username)
        await query.answer()