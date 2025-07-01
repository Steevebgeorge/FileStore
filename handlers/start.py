from pyrogram import Client, filters
from pyrogram.types import Message

def register_start(app: Client):
    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(_, message: Message):
        await message.reply_text(
            f"👋 Hello {message.from_user.mention},\n\nWelcome to the bot!"
        )
