from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI

client = AsyncIOMotorClient(DB_URI)
db = client["filterbot"]
groups_col = db["series_groups"]

# ── Save a new group ───────────────────────────────────────────────────────────
async def save_group(name, poster_file_id, description, series_titles, keywords=None):
    name_lower = name.strip().lower()
    if keywords is None:
        keywords = []
    all_keywords = list(set([name_lower] + [k.strip().lower() for k in keywords if k.strip()]))
    await groups_col.update_one(
        {"name_lower": name_lower},
        {"$set": {
            "name": name.strip(),
            "name_lower": name_lower,
            "poster_file_id": poster_file_id,
            "description": description,
            "series": series_titles,   # list of title_lower strings
            "keywords": all_keywords
        }},
        upsert=True
    )

# ── Search groups by keyword ───────────────────────────────────────────────────
async def search_groups(keyword):
    keyword = keyword.strip().lower()
    cursor = groups_col.find({
        "$or": [
            {"keywords": {"$regex": keyword, "$options": "i"}},
            {"name_lower": {"$regex": keyword, "$options": "i"}}
        ]
    })
    return await cursor.to_list(length=10)

# ── Get one group by name_lower ────────────────────────────────────────────────
async def get_group_by_name(name_lower):
    return await groups_col.find_one({"name_lower": name_lower.strip().lower()})

# ── List all groups ────────────────────────────────────────────────────────────
async def list_all_groups():
    cursor = groups_col.find({}, {"name": 1, "series": 1, "keywords": 1})
    return [(doc["name"], doc.get("series", []), doc.get("keywords", [])) async for doc in cursor]

# ── Delete a group ─────────────────────────────────────────────────────────────
async def delete_group(name_lower):
    result = await groups_col.delete_one({"name_lower": name_lower.strip().lower()})
    return result.deleted_count > 0

# ── Edit: add a series to group ────────────────────────────────────────────────
async def add_series_to_group(name_lower, series_title_lower):
    result = await groups_col.update_one(
        {"name_lower": name_lower},
        {"$addToSet": {"series": series_title_lower}}
    )
    return result.modified_count > 0

# ── Edit: remove a series from group ──────────────────────────────────────────
async def remove_series_from_group(name_lower, series_title_lower):
    result = await groups_col.update_one(
        {"name_lower": name_lower},
        {"$pull": {"series": series_title_lower}}
    )
    return result.modified_count > 0

# ── Edit: update group name ────────────────────────────────────────────────────
async def update_group_name(name_lower, new_name):
    result = await groups_col.update_one(
        {"name_lower": name_lower},
        {"$set": {"name": new_name.strip(), "name_lower": new_name.strip().lower()}}
    )
    return result.modified_count > 0

# ── Edit: update group description ────────────────────────────────────────────
async def update_group_description(name_lower, new_desc):
    result = await groups_col.update_one(
        {"name_lower": name_lower},
        {"$set": {"description": new_desc}}
    )
    return result.modified_count > 0

# ── Edit: update group poster ──────────────────────────────────────────────────
async def update_group_poster(name_lower, new_file_id):
    result = await groups_col.update_one(
        {"name_lower": name_lower},
        {"$set": {"poster_file_id": new_file_id}}
    )
    return result.modified_count > 0

# ── Edit: add keyword to group ─────────────────────────────────────────────────
async def add_keyword_to_group(name_lower, keyword):
    result = await groups_col.update_one(
        {"name_lower": name_lower},
        {"$addToSet": {"keywords": keyword.strip().lower()}}
    )
    return result.modified_count > 0

# ── Edit: remove keyword from group ───────────────────────────────────────────
async def remove_keyword_from_group(name_lower, keyword):
    result = await groups_col.update_one(
        {"name_lower": name_lower},
        {"$pull": {"keywords": keyword.strip().lower()}}
    )
    return result.modified_count > 0