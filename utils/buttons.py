from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def parse_buttons_for_db(lines):
    """
    Parses custom button text and returns serializable button dicts for DB.
    Supports:
    - urlbutton - Label : "https://link"
    - alertbutton - Label : Alert message
    Rows are separated by newlines, columns by '|'.
    """
    keyboard = []

    for line in lines:
        row_buttons = []
        parts = line.strip().split("|")
        for part in parts:
            part = part.strip()

            if part.lower().startswith("urlbutton"):
                try:
                    label, url = part.split(":", 1)
                    label = label.split("-", 1)[1].strip()
                    url = url.strip().strip('"').strip("'")
                    row_buttons.append({
                        "type": "url",
                        "text": label,
                        "url": url
                    })
                except Exception:
                    continue

            elif part.lower().startswith("alertbutton"):
                try:
                    label, alert = part.split(":", 1)
                    label = label.split("-", 1)[1].strip()
                    alert = alert.strip()
                    row_buttons.append({
                        "type": "alert",
                        "text": label,
                        "alert": alert
                    })
                except Exception:
                    continue

        if row_buttons:
            keyboard.append(row_buttons)

    return keyboard


def build_keyboard(button_data):
    """
    Converts stored button dicts from DB into InlineKeyboardMarkup.
    Supports:
    - URL buttons
    - Alert buttons (callback-based)
    """
    keyboard = []

    for row in button_data:
        buttons = []
        for btn in row:
            if btn.get("type") == "url":
                buttons.append(
                    InlineKeyboardButton(
                        text=btn["text"],
                        url=btn["url"]
                    )
                )
            elif btn.get("type") == "alert":
                # Ensure callback_data is within Telegram's 64-byte limit
                alert_data = btn["alert"][:60]
                buttons.append(
                    InlineKeyboardButton(
                        text=btn["text"],
                        callback_data=f"alert:{alert_data}"
                    )
                )
        if buttons:
            keyboard.append(buttons)

    return InlineKeyboardMarkup(keyboard) if keyboard else None
