from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMIN_IDS
from utils.db import list_all_filters


## code for viewing saved gfilterrs




def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def register_viewfilters(app: Client):
    @app.on_message(filters.command("viewfilters") & filters.private)
    async def viewfilters_handler(_, message: Message):
        print("[DEBUG] /viewfilters handler triggered")

        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized to use this command.")

        filters_list = await list_all_filters()

        if not filters_list:
            return await message.reply_text("⚠️ No global filters found.")

        text = "**📂 Saved Global Filters:**\n" + "\n".join(f"• `{f}`" for f in filters_list)
        await message.reply_text(text)
