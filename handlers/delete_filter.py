from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMIN_IDS
from utils.db import delete_filter, delete_all_filters

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def register_delete_filter(app: Client):
    @app.on_message(filters.command("del") & filters.private)
    async def delete_filter_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized to use this command.")

        if len(message.command) < 2:
            return await message.reply_text("❗Usage: `/del <keyword>`", quote=True)

        keyword = message.command[1].lower().strip()

        deleted = await delete_filter(keyword)
        if deleted:
            await message.reply_text(f"🗑️ Filter for `{keyword}` deleted successfully.")
        else:
            await message.reply_text(f"⚠️ No filter found for `{keyword}`.")

    @app.on_message(filters.command("deleteall") & filters.private)
    async def delete_all_handler(_, message: Message):
        if not is_admin(message.from_user.id):
            return await message.reply_text("🚫 You are not authorized to use this command.")

        await delete_all_filters()
        await message.reply_text("🧹 All global filters have been deleted.")
