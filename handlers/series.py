from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import ADMIN_IDS
from utils.series_db import (
    save_series, search_series,
    get_series_by_title, list_all_series, delete_series,
    add_keyword_to_series, remove_keyword_from_series
)

# ─── Helper ────────────────────────────────────────────────────────────────────

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
        row.append(InlineKeyboardButton(
            text=quality,
            url=link
        ))
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

# ─── Send series card to user ───────────────────────────────────────────────────

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
        await message.reply_photo(
            photo=poster,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await message.reply_text(caption, reply_markup=keyboard)

# ─── Register all series handlers ──────────────────────────────────────────────

def register_series(app: Client):

    # ── /addseries ──────────────────────────────────────────────────────────────
    @app.on_message(filters.command("addseries") & filters.private)
    async def addseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")

        # Step 1: Title
        await message.reply_text(
            "📝 <b>Step 1/5</b>\nSend the <b>title</b> of the series.\n\n"
            "Example: <code>Game of Thrones</code>"
        )
        title_msg = await app.listen(message.chat.id)
        title = title_msg.text.strip()

        # Step 2: Keywords
        await message.reply_text(
            "🔍 <b>Step 2/5</b>\nSend <b>search keywords</b> for this series.\n\n"
            "These are extra words users can type to find this series.\n"
            "Separate with commas. The title is already included automatically.\n\n"
            "Example: <code>GOT, game of thrones series, got series</code>\n\n"
            "Or send <code>skip</code> to only use the title as keyword."
        )
        keywords_msg = await app.listen(message.chat.id)
        if keywords_msg.text.strip().lower() == "skip":
            keywords = []
        else:
            keywords = [k.strip() for k in keywords_msg.text.split(",") if k.strip()]

        # Step 3: Poster
        await message.reply_text(
            "🖼 <b>Step 3/5</b>\nSend the <b>poster image</b> for this series.\n\n"
            "Just send a photo."
        )
        poster_msg = await app.listen(message.chat.id)
        if not poster_msg.photo:
            return await message.reply_text("❌ No photo received. Please start over with /addseries.")
        poster_file_id = poster_msg.photo.file_id

        # Step 4: Description
        await message.reply_text(
            "📄 <b>Step 4/5</b>\nSend a short <b>description</b>.\n\n"
            "Or send <code>skip</code> to skip."
        )
        desc_msg = await app.listen(message.chat.id)
        description = "" if desc_msg.text.strip().lower() == "skip" else desc_msg.text.strip()

        # Step 5: Seasons and links
        await message.reply_text(
            "🗂 <b>Step 5/5 — Seasons</b>\n"
            "How many seasons does this series have?\n\n"
            "Send a number, e.g. <code>3</code>"
        )
        count_msg = await app.listen(message.chat.id)
        try:
            season_count = int(count_msg.text.strip())
        except ValueError:
            return await message.reply_text("❌ Invalid number. Please start over with /addseries.")

        seasons_data = {}
        for i in range(1, season_count + 1):
            season_name = f"S{i}"
            await message.reply_text(
                f"📂 <b>{season_name}</b> — What qualities are available?\n\n"
                f"Send them comma-separated, e.g. <code>720p, 1080p, 2160p</code>"
            )
            qual_msg = await app.listen(message.chat.id)
            qualities = [q.strip() for q in qual_msg.text.split(",") if q.strip()]

            season_links = {}
            for quality in qualities:
                await message.reply_text(
                    f"🔗 Send the <b>full link</b> for <b>{season_name} — {quality}</b>\n\n"
                    f"Example: <code>https://t.me/Cinemacompanyfilebot?start=Z2V0LTEy...</code>"
                )
                link_msg = await app.listen(message.chat.id)
                season_links[quality] = link_msg.text.strip()
            seasons_data[season_name] = season_links

        await save_series(title, poster_file_id, description, seasons_data, keywords)

        all_keywords = [title.lower()] + keywords
        await message.reply_text(
            f"✅ <b>{title}</b> saved successfully!\n\n"
            f"🔍 Keywords: {', '.join(all_keywords)}\n"
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
            lines.append(f"• <b>{title}</b>\n  🔍 Keywords: <code>{', '.join(keywords)}</code>")
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
        deleted = await delete_series(title_lower)
        if deleted:
            await message.reply_text("✅ Series deleted.")
        else:
            await message.reply_text("❌ Series not found.")

    # ── /addkeyword — add keyword to existing series ─────────────────────────────
    @app.on_message(filters.command("addkeyword") & filters.private)
    async def addkeyword_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(
                "Usage: <code>/addkeyword Series Title | keyword1, keyword2</code>\n\n"
                "Example: <code>/addkeyword Game of Thrones | GOT, got series</code>"
            )
        try:
            title_part, keywords_part = parts[1].split("|", 1)
        except ValueError:
            return await message.reply_text(
                "❌ Wrong format. Use:\n"
                "<code>/addkeyword Series Title | keyword1, keyword2</code>"
            )
        title_lower = title_part.strip().lower()
        new_keywords = [k.strip() for k in keywords_part.split(",") if k.strip()]

        series = await get_series_by_title(title_lower)
        if not series:
            return await message.reply_text(
                f"❌ Series <b>{title_part.strip()}</b> not found.\n"
                f"Use /listseries to see exact titles."
            )

        added = []
        for kw in new_keywords:
            success = await add_keyword_to_series(title_lower, kw)
            if success:
                added.append(kw)

        if added:
            await message.reply_text(
                f"✅ Added keywords to <b>{series['title']}</b>:\n"
                f"<code>{', '.join(added)}</code>"
            )
        else:
            await message.reply_text("⚠️ Keywords already exist or nothing was added.")

    # ── /delkeyword — remove keyword from existing series ───────────────────────
    @app.on_message(filters.command("delkeyword") & filters.private)
    async def delkeyword_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(
                "Usage: <code>/delkeyword Series Title | keyword1, keyword2</code>\n\n"
                "Example: <code>/delkeyword Game of Thrones | GOT</code>"
            )
        try:
            title_part, keywords_part = parts[1].split("|", 1)
        except ValueError:
            return await message.reply_text(
                "❌ Wrong format. Use:\n"
                "<code>/delkeyword Series Title | keyword1, keyword2</code>"
            )
        title_lower = title_part.strip().lower()
        rm_keywords = [k.strip() for k in keywords_part.split(",") if k.strip()]

        series = await get_series_by_title(title_lower)
        if not series:
            return await message.reply_text(f"❌ Series not found. Use /listseries to check titles.")

        # Protect the title itself from being removed
        removed = []
        skipped = []
        for kw in rm_keywords:
            if kw.lower() == title_lower:
                skipped.append(kw)
                continue
            success = await remove_keyword_from_series(title_lower, kw)
            if success:
                removed.append(kw)
            else:
                skipped.append(kw)

        reply = f"<b>{series['title']}</b>\n"
        if removed:
            reply += f"✅ Removed: <code>{', '.join(removed)}</code>\n"
        if skipped:
            reply += f"⚠️ Not found or protected: <code>{', '.join(skipped)}</code>"
        await message.reply_text(reply)

    # ── Callback: season button tapped ──────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^season:"))
    async def season_callback(client, query: CallbackQuery):
        data = query.data
        parts = data.split(":", 2)
        if len(parts) < 3:
            return await query.answer("❌ Invalid data.", show_alert=True)

        title_lower = parts[1]
        season = parts[2]

        series = await get_series_by_title(title_lower)
        if not series:
            return await query.answer("❌ Series not found.", show_alert=True)

        qualities = series["seasons"].get(season, {})
        if not qualities:
            return await query.answer("❌ No qualities found for this season.", show_alert=True)

        keyboard = quality_keyboard(qualities, title_lower, season)
        new_caption = f"<b>🎬 {series['title']} — {season}</b>\n\n<b>Select quality:</b>"

        try:
            await query.message.edit_caption(caption=new_caption, reply_markup=keyboard)
        except Exception:
            try:
                await query.message.edit_text(text=new_caption, reply_markup=keyboard)
            except Exception:
                await query.message.reply_text(new_caption, reply_markup=keyboard)
        await query.answer()

    # ── Callback: back to seasons ────────────────────────────────────────────────
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

    # ── Callback: multiple results ───────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^showseries:(.+)$"))
    async def showseries_callback(client, query: CallbackQuery):
        title_lower = query.data.split(":", 1)[1]
        series = await get_series_by_title(title_lower)
        if not series:
            return await query.answer("❌ Not found.", show_alert=True)
        bot_me = await client.get_me()
        await send_series_card(query.message, series, bot_me.username)
        await query.answer()