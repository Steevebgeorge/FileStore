from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI

client = AsyncIOMotorClient(DB_URI)
db = client["filterbot"]
series_col = db["series"]

# Save or update a series
async def save_series(title, poster_file_id, description, seasons_data):
    """
    seasons_data format:
    {
        "S1": {"720p": "FILEID_1", "1080p": "FILEID_2"},
        "S2": {"720p": "FILEID_3"},
    }
    """
    await series_col.update_one(
        {"title_lower": title.strip().lower()},
        {"$set": {
            "title": title.strip(),
            "title_lower": title.strip().lower(),
            "poster_file_id": poster_file_id,
            "description": description,
            "seasons": seasons_data
        }},
        upsert=True
    )

# Search series by keyword (fuzzy — checks if keyword is inside title)
async def search_series(keyword):
    keyword = keyword.strip().lower()
    cursor = series_col.find({
        "title_lower": {"$regex": keyword, "$options": "i"}
    })
    return await cursor.to_list(length=10)

# Get one series by exact title_lower
async def get_series_by_title(title_lower):
    return await series_col.find_one({"title_lower": title_lower})

# List all series titles (for admin)
async def list_all_series():
    cursor = series_col.find({}, {"title": 1})
    return [doc["title"] async for doc in cursor]

# Delete a series
async def delete_series(title_lower):
    result = await series_col.delete_one({"title_lower": title_lower})
    return result.deleted_count > 0