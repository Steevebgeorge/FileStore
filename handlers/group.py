from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import ADMIN_IDS
from utils.group_db import (
    save_group, search_groups, get_group_by_name,
    list_all_groups, delete_group,
    add_series_to_group, remove_series_from_group,
    update_group_name, update_group_description, update_group_poster,
    add_keyword_to_group, remove_keyword_from_group
)
from utils.series_db import get_series_by_title
from handlers.series import send_series_card

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def group_series_keyboard(group: dict):
    """Show all series in a group as buttons."""
    buttons = []
    for title_lower in group.get("series", []):
        buttons.append([InlineKeyboardButton(
            text=title_lower.title(),
            callback_data=f"groupseries:{title_lower}"
        )])
    return InlineKeyboardMarkup(buttons) if buttons else None

def register_group(app: Client):

    # ── /addgroup ────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("addgroup") & filters.private)
    async def addgroup_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")

        await message.reply_text(
            "📝 <b>Step 1/5 — Group Name</b>\n\n"
            "Send the name for this group.\n"
            "Example: <code>Dexter</code>"
        )
        name_msg = await app.listen(message.chat.id)
        name = name_msg.text.strip()

        await message.reply_text(
            "🔍 <b>Step 2/5 — Keywords</b>\n\n"
            "Extra search keywords, comma-separated.\n"
            "The group name is already included.\n\n"
            "Or send <code>skip</code>."
        )
        kw_msg = await app.listen(message.chat.id)
        keywords = [] if kw_msg.text.strip().lower() == "skip" else [
            k.strip() for k in kw_msg.text.split(",") if k.strip()
        ]

        await message.reply_text(
            "🖼 <b>Step 3/5 — Poster</b>\n\nSend the group poster image."
        )
        poster_msg = await app.listen(message.chat.id)
        if not poster_msg.photo:
            return await message.reply_text("❌ No photo received. Start over with /addgroup.")
        poster_file_id = poster_msg.photo.file_id

        await message.reply_text(
            "📄 <b>Step 4/5 — Description</b>\n\n"
            "Send a short description or send <code>skip</code>."
        )
        desc_msg = await app.listen(message.chat.id)
        description = "" if desc_msg.text.strip().lower() == "skip" else desc_msg.text.strip()

        await message.reply_text(
            "📺 <b>Step 5/5 — Series</b>\n\n"
            "Send the exact titles of series to include, one per line.\n"
            "These must already be added with /addseries.\n\n"
            "Example:\n<code>Dexter\nDexter: New Blood\nDexter: Resurrection</code>"
        )
        series_msg = await app.listen(message.chat.id)
        series_titles = [
            s.strip().lower()
            for s in series_msg.text.strip().splitlines()
            if s.strip()
        ]

        # Validate each series exists
        not_found = []
        for t in series_titles:
            if not await get_series_by_title(t):
                not_found.append(t)

        if not_found:
            return await message.reply_text(
                f"❌ These series were not found:\n"
                f"<code>{chr(10).join(not_found)}</code>\n\n"
                f"Add them first with /addseries, then try /addgroup again."
            )

        await save_group(name, poster_file_id, description, series_titles, keywords)
        await message.reply_text(
            f"✅ Group <b>{name}</b> saved!\n\n"
            f"📺 Series: {', '.join(series_titles)}\n"
            f"🔍 Keywords: {', '.join([name.lower()] + keywords)}"
        )

    # ── /listgroups ──────────────────────────────────────────────────────────────
    @app.on_message(filters.command("listgroups") & filters.private)
    async def listgroups_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        all_groups = await list_all_groups()
        if not all_groups:
            return await message.reply_text("⚠️ No groups saved yet.")
        lines = []
        for name, series, keywords in all_groups:
            lines.append(
                f"• <b>{name}</b>\n"
                f"  📺 Series: <code>{', '.join(series)}</code>\n"
                f"  🔍 Keywords: <code>{', '.join(keywords)}</code>"
            )
        await message.reply_text("<b>📂 Saved Groups:</b>\n\n" + "\n\n".join(lines))

    # ── /delgroup ────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("delgroup") & filters.private)
    async def delgroup_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text("Usage: <code>/delgroup Dexter</code>")
        if await delete_group(parts[1].strip().lower()):
            await message.reply_text("✅ Group deleted.")
        else:
            await message.reply_text("❌ Group not found. Use /listgroups to check.")

    # ── /editgroup ───────────────────────────────────────────────────────────────
    # /editgroup Dexter | setname | Dexter Universe
    # /editgroup Dexter | setdesc | All Dexter series
    # /editgroup Dexter | setposter
    # /editgroup Dexter | addseries | Dexter: Resurrection
    # /editgroup Dexter | delseries | Dexter: New Blood
    # /editgroup Dexter | addkeyword | dexter show, dexter serial killer
    # /editgroup Dexter | delkeyword | dexter show
    @app.on_message(filters.command("editgroup") & filters.private)
    async def editgroup_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized.")

        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(
                "<b>📝 /editgroup usage:</b>\n\n"
                "<code>/editgroup Name | action | value</code>\n\n"
                "<b>Actions:</b>\n"
                "• <code>setname | New Name</code>\n"
                "• <code>setdesc | New description</code>\n"
                "• <code>setposter</code> (then send photo)\n"
                "• <code>addseries | Series Title</code>\n"
                "• <code>delseries | Series Title</code>\n"
                "• <code>addkeyword | kw1, kw2</code>\n"
                "• <code>delkeyword | kw1</code>"
            )

        segments = [s.strip() for s in parts[1].split("|")]
        if len(segments) < 2:
            return await message.reply_text("❌ Wrong format. See /editgroup for usage.")

        name_lower = segments[0].lower()
        action = segments[1].lower()

        group = await get_group_by_name(name_lower)
        if not group:
            return await message.reply_text(
                f"❌ Group <b>{segments[0]}</b> not found.\n"
                f"Use /listgroups to check exact names."
            )

        if action == "setname":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editgroup Name | setname | New Name</code>")
            await update_group_name(name_lower, segments[2])
            await message.reply_text(f"✅ Name updated to <b>{segments[2]}</b>.")

        elif action == "setdesc":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editgroup Name | setdesc | Description</code>")
            await update_group_description(name_lower, segments[2])
            await message.reply_text("✅ Description updated.")

        elif action == "setposter":
            await message.reply_text("🖼 Send the new poster image now.")
            poster_msg = await app.listen(message.chat.id)
            if not poster_msg.photo:
                return await message.reply_text("❌ No photo received.")
            await update_group_poster(name_lower, poster_msg.photo.file_id)
            await message.reply_text("✅ Poster updated.")

        elif action == "addseries":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editgroup Name | addseries | Series Title</code>")
            s_lower = segments[2].lower()
            if not await get_series_by_title(s_lower):
                return await message.reply_text(
                    f"❌ Series <b>{segments[2]}</b> not found. Add it first with /addseries."
                )
            await add_series_to_group(name_lower, s_lower)
            await message.reply_text(f"✅ <b>{segments[2]}</b> added to group.")

        elif action == "delseries":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editgroup Name | delseries | Series Title</code>")
            await remove_series_from_group(name_lower, segments[2].lower())
            await message.reply_text(f"✅ <b>{segments[2]}</b> removed from group.")

        elif action == "addkeyword":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editgroup Name | addkeyword | kw1, kw2</code>")
            kws = [k.strip() for k in segments[2].split(",") if k.strip()]
            added = [kw for kw in kws if await add_keyword_to_group(name_lower, kw)]
            await message.reply_text(
                f"✅ Added: <code>{', '.join(added)}</code>" if added
                else "⚠️ Keywords already exist."
            )

        elif action == "delkeyword":
            if len(segments) < 3:
                return await message.reply_text("Usage: <code>/editgroup Name | delkeyword | kw1</code>")
            kws = [k.strip() for k in segments[2].split(",") if k.strip()]
            removed = []
            skipped = []
            for kw in kws:
                if kw == name_lower:
                    skipped.append(kw)
                    continue
                if await remove_keyword_from_group(name_lower, kw):
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
            await message.reply_text(f"❌ Unknown action <code>{action}</code>. See /editgroup.")

    # ── Callback: user taps a series inside a group ──────────────────────────────
    @app.on_callback_query(filters.regex(r"^groupseries:"))
    async def groupseries_callback(client, query: CallbackQuery):
        title_lower = query.data.split(":", 1)[1]
        series = await get_series_by_title(title_lower)
        if not series:
            return await query.answer("❌ Series not found.", show_alert=True)
        bot_me = await client.get_me()
        await send_series_card(query.message, series, bot_me.username)
        await query.answer()