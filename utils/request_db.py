from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI
from datetime import datetime, timedelta

# Mongo client setup
client = AsyncIOMotorClient(DB_URI)
db = client["filterbot"]
requests_col = db["requests"]

# Save a new request
async def save_request(keyword, user_id, name, username, message_id, chat_id):
    await requests_col.insert_one({
        "keyword": keyword,
        "user_id": user_id,
        "name": name,
        "username": username,
        "message_id": message_id,
        "chat_id": chat_id,
        "status": "Pending",
        "timestamp": datetime.utcnow()  # Required for cooldown logic
    })

# Update request status (Queue, Uploaded, Rejected)
async def update_request_status(message_id, new_status):
    await requests_col.update_one(
        {"message_id": message_id},
        {"$set": {"status": new_status}}
    )


    # Get latest request by user ID
async def get_request_by_user_id(user_id):
    return await requests_col.find_one({"user_id": user_id})


# Get request by message ID (used in callback handling)
async def get_request_by_msg_id(message_id):
    return await requests_col.find_one({"message_id": message_id})

# Delete a request by message ID
async def delete_request(message_id):
    await requests_col.delete_one({"message_id": message_id})

# Cooldown check: Can user send a new request?
async def can_request(user_id):
    doc = await requests_col.find_one({"user_id": user_id})
    if not doc:
        return True
    last_time = doc.get("timestamp")
    if not last_time:
        return True
    return datetime.utcnow() - last_time > timedelta(hours=24)

# Set/update user's last request timestamp
async def set_request_timestamp(user_id):
    await requests_col.update_one(
        {"user_id": user_id},
        {"$set": {"timestamp": datetime.utcnow()}},
        upsert=True
    )
