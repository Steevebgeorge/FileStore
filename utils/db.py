from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI

# Mongo client setup
client = AsyncIOMotorClient(DB_URI)
db = client["filterbot"]

filters_col = db["filters"]

# --- FILTER FUNCTIONS ---

# Save a global filter
async def save_filter(keyword, caption, media_type, message, buttons):
    filter_data = {
        "keyword": keyword,
        "caption": caption,
        "media_type": media_type,
        "file_id": None,
        "buttons": buttons,
    }

    if media_type:
        media_obj = getattr(message, media_type, None)
        if media_obj:
            filter_data["file_id"] = media_obj.file_id

    await filters_col.update_one(
        {"keyword": keyword},
        {"$set": filter_data},
        upsert=True
    )

# Fetch a global filter by keyword
async def get_filter(keyword):
    return await filters_col.find_one({"keyword": keyword})

# Fetch all saved filters
async def list_all_filters():
    cursor = filters_col.find({}, {"keyword": 1})
    return [doc["keyword"] async for doc in cursor]

# Delete a filter by keyword
async def delete_filter(keyword):
    result = await filters_col.delete_one({"keyword": keyword})
    return result.deleted_count > 0

# Delete all filters
async def delete_all_filters():
    await filters_col.delete_many({})
