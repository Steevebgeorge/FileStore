from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI

client = AsyncIOMotorClient(DB_URI)
db = client["filterbot"]
series_col = db["series"]

# Save or update a series
async def save_series(title, poster_file_id, description, seasons_data, keywords=None):
    """
    keywords: list of strings like ["game of thrones", "got", "gots"]
    Always includes title_lower as a keyword automatically.
    """
    title_lower = title.strip().lower()
    if keywords is None:
        keywords = []
    # Always include the title itself as a keyword
    all_keywords = list(set([title_lower] + [k.strip().lower() for k in keywords if k.strip()]))

    await series_col.update_one(
        {"title_lower": title_lower},
        {"$set": {
            "title": title.strip(),
            "title_lower": title_lower,
            "poster_file_id": poster_file_id,
            "description": description,
            "seasons": seasons_data,
            "keywords": all_keywords
        }},
        upsert=True
    )

# Search series by keyword (checks across all keywords)
async def search_series(keyword):
    keyword = keyword.strip().lower()
    cursor = series_col.find({
        "keywords": {"$regex": keyword, "$options": "i"}
    })
    return await cursor.to_list(length=10)

# Get one series by exact title_lower
async def get_series_by_title(title_lower):
    return await series_col.find_one({"title_lower": title_lower})

# List all series titles
async def list_all_series():
    cursor = series_col.find({}, {"title": 1, "keywords": 1})
    return [(doc["title"], doc.get("keywords", [])) async for doc in cursor]

# Add a keyword to existing series
async def add_keyword_to_series(title_lower, keyword):
    keyword = keyword.strip().lower()
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$addToSet": {"keywords": keyword}}
    )
    return result.modified_count > 0

# Remove a keyword from existing series
async def remove_keyword_from_series(title_lower, keyword):
    keyword = keyword.strip().lower()
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$pull": {"keywords": keyword}}
    )
    return result.modified_count > 0

# Delete a series
async def delete_series(title_lower):
    result = await series_col.delete_one({"title_lower": title_lower})
    return result.deleted_count > 0