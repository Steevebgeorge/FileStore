from pyrogram import Client, filters
from pyrogram.types import CallbackQuery


## code for alert buttons


def register_alert_handler(app: Client):
    @app.on_callback_query(filters.regex(r"^alert:(.+)"))
    async def alert_button_handler(_, query: CallbackQuery):
        alert_text = query.data.split("alert:", 1)[1]
        await query.answer(alert_text, show_alert=True)
