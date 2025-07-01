from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, ForceReply
from config import ADMIN_IDS
from utils.request_db import (
    update_request_status,
    get_request_by_msg_id,
    delete_request
)

# Temporary in-memory store for rejection reasons
pending_rejections = {}

def register_request_callback(app: Client):
    
    @app.on_callback_query(filters.regex(r"^(queue|uploaded|rejected)_(.+)"))
    async def handle_status_change(_, query: CallbackQuery):
        if query.from_user.id not in ADMIN_IDS:
            return await query.answer("🚫 You are not authorized!", show_alert=True)

        action, keyword = query.data.split("_", 1)
        message = query.message
        message_id = message.id

        status_map = {
            "queue": "⏳ In Queue",
            "uploaded": "✅ Uploaded",
            "rejected": "❌ Rejected"
        }
        status = status_map.get(action)

        # Fetch request data
        req = await get_request_by_msg_id(message_id)
        if not req:
            return await query.answer("❌ Request not found.", show_alert=True)

        name = req["name"]
        username = req["username"]
        user_id = req["user_id"]

        # Prepare status update
        new_caption = (
            f"📥 **New Request:**\n"
            f"🔹 **Keyword:** `{keyword}`\n"
            f"👤 **From:** {name} ({username})\n"
            f"📌 **Status:** {status}"
        )

        # Edit message in log channel
        await message.edit_text(new_caption, reply_markup=query.message.reply_markup)
        await update_request_status(message_id, status)

        # Handle rejection (reason comes separately)
        if action == "rejected":
            pending_rejections[query.from_user.id] = {
                "user_id": user_id,
                "keyword": keyword,
                "message_id": message_id
            }
            await query.message.reply(
                f"❓ Please reply with a reason for rejecting `{keyword}`.",
                reply_markup=ForceReply(selective=True)
            )
            return await query.answer("Waiting for rejection reason...")

        # Handle other status (queue / uploaded)
        try:
            await app.send_message(
                user_id,
                f"📢 Your request for `{keyword}` has been **{status}** by the admin."
            )
        except:
            pass

        if action == "uploaded":
            await delete_request(message_id)

        await query.answer(f"✅ Status changed to {status}")

    @app.on_message(filters.private & filters.reply & filters.user(ADMIN_IDS))
    async def receive_rejection_reason(_, message: Message):
        admin_id = message.from_user.id
        if admin_id not in pending_rejections:
            return  # No pending rejection for this admin

        # Extract saved context
        reason_data = pending_rejections.pop(admin_id)
        user_id = reason_data["user_id"]
        keyword = reason_data["keyword"]
        message_id = reason_data["message_id"]
        reason = message.text.strip()

        # Update request message in log channel
        req = await get_request_by_msg_id(message_id)
        if req:
            name = req["name"]
            username = req["username"]

            updated_text = (
                f"📥 **New Request:**\n"
                f"🔹 **Keyword:** `{keyword}`\n"
                f"👤 **From:** {name} ({username})\n"
                f"📌 **Status:** ❌ Rejected\n"
                f"📝 **Reason:** {reason}"
            )

            try:
                await app.edit_message_text(
                    chat_id=req["chat_id"],
                    message_id=message_id,
                    text=updated_text
                )
            except:
                pass

        # Notify user
        try:
            await app.send_message(
                user_id,
                f"❌ Your request for `{keyword}` was rejected.\n\n📝 **Reason:** {reason}"
            )
        except:
            pass

        await delete_request(message_id)
        await message.reply("✅ Rejection reason sent and request deleted.")
