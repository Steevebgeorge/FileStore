import os
import logging
from logging.handlers import RotatingFileHandler

# Credits (Do Not Remove)
# @CodeFlix_Bots | @rohit_1888
# Telegram Support: @CodeflixSupport
# GitHub: https://github.com/Codeflix-Bots/FileStore

# =============== ENV VARIABLES ===============

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8154426339")  # Old bot token (used as default)
BOT_TOKEN = TG_BOT_TOKEN  # new style alias

APP_ID = int(os.environ.get("APP_ID", "0"))  # From my.telegram.org
API_ID = APP_ID  # alias for new format

API_HASH = os.environ.get("API_HASH", "")  # From my.telegram.org
DB_URI = os.environ.get("DATABASE_URL", "")  # alias for new format
DATABASE_URL = DB_URI  # backwards compatible alias

DB_NAME = os.environ.get("DATABASE_NAME", "Cluooo")

# New variables (set in Koyeb)
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "0"))

try:
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
except Exception:
    ADMIN_IDS = []

# =============== OTHER CONFIGS ===============

CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002170811388"))
OWNER = os.environ.get("OWNER", "sewxiy")
OWNER_ID = int(os.environ.get("OWNER_ID", "776376926"))

PORT = os.environ.get("PORT", "8001")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))

FSUB_LINK_EXPIRY = int(os.getenv("FSUB_LINK_EXPIRY", "10"))
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", "https://t.me/S_B_G01")

START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/39d6cde9bc4d7cfc0d266.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/39d6cde9bc4d7cfc0d266.jpg")

START_MSG = os.environ.get("START_MESSAGE", "<b>ʜᴇʟʟᴏ {first}\n\n<blockquote> you can use me for accessing series, Join <a href=https://t.me/seriescc>Cinema Company Series</a> for series </blockquote></b>")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {first}\n\n<b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b>")

HELP_TXT = "<b>This is a file sharing bot created for cinema company</b>"
ABOUT_TXT = "<b><blockquote>◈ ᴄʀᴇᴀᴛᴏʀ: <a href=https://t.me/S_B_G01>Steeve</a>\n◈ Series ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/seriescc>Cinema Company Series</a></blockquote></b>"

CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>
<b>›› /dlt_time :</b> sᴇᴛ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /check_dlt_time :</b> ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /ban :</b> ʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /unban :</b> ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /banlist :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀs
<b>›› /addchnl :</b> ᴀᴅᴅ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /delchnl :</b> ʀᴇᴍᴏᴠᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /listchnl :</b> ᴠɪᴇᴡ ᴀᴅᴅᴇᴅ ᴄʜᴀɴɴᴇʟs
<b>›› /fsub_mode :</b> ᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴍᴏᴅᴇ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀs
<b>›› /add_admin :</b> ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /deladmin :</b> ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /admins :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ᴀᴅᴍɪɴs
"""

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• ʙʏ @nova_flix</b>")
PROTECT_CONTENT = True if os.environ.get("PROTECT_CONTENT", "False") == "True" else False
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "").lower() == "true"

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "ʙᴀᴋᴋᴀ ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ꜱᴇɴᴘᴀɪ!!"

# =============== LOGGING ===============

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50_000_000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
