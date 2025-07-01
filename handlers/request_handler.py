from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import LOG_CHANNEL_ID, ADMIN_IDS
from utils.request_db import save_request, can_request, set_request_timestamp

def register_request_handler(app: Client):
    @app.on_message(filters.text & filters.private & filters.regex(r"^#request\s+(.+)"))
    async def handle_request(_, message: Message):
        keyword = message.text.split(None, 1)[1].strip()
        user = message.from_user
        user_id = user.id
        name = user.first_name or "No Name"
        username = f"@{user.username}" if user.username else "No Username"

        # 24-hour cooldown check
        if not await can_request(user_id):
            return await message.reply_text("⏳ You can only send 1 request every 24 hours. Please try again later.")

        # Mark this request time
        await set_request_timestamp(user_id)

        # Caption to send to admin log channel
        caption = (
            f"📥 **New Request:**\n"
            f"🔹 **Keyword:** `{keyword}`\n"
            f"👤 **From:** {name} ({username})\n"
            f"📌 **Status:** Pending"
        )

        # Admin-only buttons
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Add to Queue", callback_data=f"queue_{keyword}"),
                InlineKeyboardButton("📤 Uploaded", callback_data=f"uploaded_{keyword}"),
                InlineKeyboardButton("❌ Rejected", callback_data=f"rejected_{keyword}")
            ]
        ])

        # Send to log channel
        sent = await app.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=caption,
            reply_markup=buttons
        )

        # Save request to DB
        await save_request(
            keyword=keyword,
            user_id=user_id,
            name=name,
            username=username,
            message_id=sent.id,
            chat_id=sent.chat.id
        )

        # Acknowledge to user
        await message.reply_text("✅ Your request has been sent to the admin.")
