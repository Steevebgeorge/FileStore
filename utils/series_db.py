from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI

client = AsyncIOMotorClient(DB_URI)
db = client["filterbot"]
series_col = db["series"]

# ── Save a new series ──────────────────────────────────────────────────────────
async def save_series(title, poster_file_id, description, seasons_data, keywords=None):
    title_lower = title.strip().lower()
    if keywords is None:
        keywords = []
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

# ── Search series by keyword ───────────────────────────────────────────────────
async def search_series(keyword):
    keyword = keyword.strip().lower()
    cursor = series_col.find({
        "$or": [
            {"keywords": {"$regex": keyword, "$options": "i"}},
            {"title_lower": {"$regex": keyword, "$options": "i"}}
        ]
    })
    return await cursor.to_list(length=10)

# ── Get one series by title_lower ──────────────────────────────────────────────
async def get_series_by_title(title_lower):
    return await series_col.find_one({"title_lower": title_lower.strip().lower()})

# ── List all series ────────────────────────────────────────────────────────────
async def list_all_series():
    cursor = series_col.find({}, {"title": 1, "keywords": 1})
    return [(doc["title"], doc.get("keywords", [])) async for doc in cursor]

# ── Delete a series ────────────────────────────────────────────────────────────
async def delete_series(title_lower):
    result = await series_col.delete_one({"title_lower": title_lower.strip().lower()})
    return result.deleted_count > 0

# ── Edit: update title ─────────────────────────────────────────────────────────
async def update_series_title(title_lower, new_title):
    new_lower = new_title.strip().lower()
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$set": {"title": new_title.strip(), "title_lower": new_lower}}
    )
    return result.modified_count > 0

# ── Edit: update description ───────────────────────────────────────────────────
async def update_series_description(title_lower, new_desc):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$set": {"description": new_desc}}
    )
    return result.modified_count > 0

# ── Edit: update poster ────────────────────────────────────────────────────────
async def update_series_poster(title_lower, new_file_id):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$set": {"poster_file_id": new_file_id}}
    )
    return result.modified_count > 0

# ── Edit: add a season ─────────────────────────────────────────────────────────
async def add_season_to_series(title_lower, season_name, qualities_dict):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$set": {f"seasons.{season_name}": qualities_dict}}
    )
    return result.modified_count > 0

# ── Edit: remove a season ──────────────────────────────────────────────────────
async def remove_season_from_series(title_lower, season_name):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$unset": {f"seasons.{season_name}": ""}}
    )
    return result.modified_count > 0

# ── Edit: add a quality to a season ───────────────────────────────────────────
async def add_quality_to_season(title_lower, season_name, quality, link):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$set": {f"seasons.{season_name}.{quality}": link}}
    )
    return result.modified_count > 0

# ── Edit: remove a quality from a season ──────────────────────────────────────
async def remove_quality_from_season(title_lower, season_name, quality):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$unset": {f"seasons.{season_name}.{quality}": ""}}
    )
    return result.modified_count > 0

# ── Edit: add keyword ──────────────────────────────────────────────────────────
async def add_keyword_to_series(title_lower, keyword):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$addToSet": {"keywords": keyword.strip().lower()}}
    )
    return result.modified_count > 0

# ── Edit: remove keyword ───────────────────────────────────────────────────────
async def remove_keyword_from_series(title_lower, keyword):
    result = await series_col.update_one(
        {"title_lower": title_lower},
        {"$pull": {"keywords": keyword.strip().lower()}}
    )
    return result.modified_count > 0