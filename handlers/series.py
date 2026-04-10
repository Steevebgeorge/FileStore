from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import ADMIN_IDS
from utils.series_db import (
    save_series, search_series,
    get_series_by_title, list_all_series, delete_series
)

# ─── Helper ────────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def seasons_keyboard(seasons: dict, title_lower: str):
    """Build inline keyboard rows of season buttons."""
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

def quality_keyboard(qualities: dict, title_lower: str, season: str, bot_username: str):
    """Build inline keyboard of quality buttons with deep links."""
    buttons = []
    row = []
    for quality, file_id in qualities.items():
        deep_link = f"https://t.me/{bot_username}?start={file_id}"
        row.append(InlineKeyboardButton(
            text=quality,
            url=deep_link
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
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

    # ── /addseries — admin command to add a new series ──────────────────────────
    @app.on_message(filters.command("addseries") & filters.private)
    async def addseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")

        # Step 1: Title
        await message.reply_text(
            "📝 <b>Step 1/4</b>\nSend the <b>title</b> of the series.\n\n"
            "Example: <code>Game of Thrones</code>"
        )
        title_msg = await app.listen(message.chat.id)
        title = title_msg.text.strip()

        # Step 2: Poster
        await message.reply_text(
            "🖼 <b>Step 2/4</b>\nSend the <b>poster image</b> for this series.\n\n"
            "Just send a photo."
        )
        poster_msg = await app.listen(message.chat.id)
        if not poster_msg.photo:
            return await message.reply_text("❌ No photo received. Please start over with /addseries.")
        poster_file_id = poster_msg.photo.file_id

        # Step 3: Description
        await message.reply_text(
            "📄 <b>Step 3/4</b>\nSend a short <b>description</b>.\n\n"
            "Or send <code>skip</code> to skip."
        )
        desc_msg = await app.listen(message.chat.id)
        description = "" if desc_msg.text.strip().lower() == "skip" else desc_msg.text.strip()

        # Step 4: Seasons and links
        await message.reply_text(
            "🗂 <b>Step 4/4 — Seasons</b>\n"
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
                    f"🔗 Send the <b>File ID</b> for <b>{season_name} — {quality}</b>\n\n"
                    f"This is the file ID you get from /genlink or /batch.\n"
                    f"Example: <code>BQACAgUAAxkBAAI...</code>"
                )
                link_msg = await app.listen(message.chat.id)
                season_links[quality] = link_msg.text.strip()

            seasons_data[season_name] = season_links

        await save_series(title, poster_file_id, description, seasons_data)
        await message.reply_text(
            f"✅ <b>{title}</b> has been saved successfully!\n\n"
            f"Seasons: {', '.join(seasons_data.keys())}"
        )

    # ── /listseries — admin can view all saved series ───────────────────────────
    @app.on_message(filters.command("listseries") & filters.private)
    async def listseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        all_series = await list_all_series()
        if not all_series:
            return await message.reply_text("⚠️ No series saved yet.")
        text = "<b>📺 Saved Series:</b>\n" + "\n".join(f"• {s}" for s in all_series)
        await message.reply_text(text)

    # ── /delseries — admin can delete a series ──────────────────────────────────
    @app.on_message(filters.command("delseries") & filters.private)
    async def delseries_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(
                "Usage: <code>/delseries Game of Thrones</code>"
            )
        title_lower = parts[1].strip().lower()
        deleted = await delete_series(title_lower)
        if deleted:
            await message.reply_text("✅ Series deleted.")
        else:
            await message.reply_text("❌ Series not found.")

    # ── Callback: season button tapped ──────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^season:"))
    async def season_callback(client, query: CallbackQuery):
        print(f"[DEBUG] season_callback triggered: {query.data}")
        data = query.data
        parts = data.split(":", 2)

        if len(parts) < 3:
            print(f"[DEBUG] not enough parts: {parts}")
            return await query.answer("❌ Invalid data.", show_alert=True)

        title_lower = parts[1]
        season = parts[2]
        print(f"[DEBUG] title_lower={title_lower}, season={season}")

        series = await get_series_by_title(title_lower)
        if not series:
            print(f"[DEBUG] series not found for title_lower={title_lower}")
            return await query.answer("❌ Series not found.", show_alert=True)

        qualities = series["seasons"].get(season, {})
        print(f"[DEBUG] qualities={qualities}")

        if not qualities:
            return await query.answer("❌ No qualities found for this season.", show_alert=True)

        bot_username = (await client.get_me()).username
        keyboard = quality_keyboard(qualities, title_lower, season, bot_username)
        new_caption = f"<b>🎬 {series['title']} — {season}</b>\n\n<b>Select quality:</b>"

        try:
            await query.message.edit_caption(
                caption=new_caption,
                reply_markup=keyboard
            )
            print("[DEBUG] edit_caption succeeded")
        except Exception as e1:
            print(f"[DEBUG] edit_caption failed: {e1}")
            try:
                await query.message.edit_text(
                    text=new_caption,
                    reply_markup=keyboard
                )
                print("[DEBUG] edit_text succeeded")
            except Exception as e2:
                print(f"[DEBUG] edit_text failed: {e2}")
                await query.message.reply_text(new_caption, reply_markup=keyboard)
                print("[DEBUG] reply_text sent as fallback")

        await query.answer()

    # ── Callback: multiple results — user picks a series ────────────────────────
    @app.on_callback_query(filters.regex(r"^showseries:(.+)$"))
    async def showseries_callback(client, query: CallbackQuery):
        title_lower = query.data.split(":", 1)[1]
        series = await get_series_by_title(title_lower)
        if not series:
            return await query.answer("❌ Not found.", show_alert=True)
        bot_me = await client.get_me()
        await send_series_card(query.message, series, bot_me.username)
        await query.answer()