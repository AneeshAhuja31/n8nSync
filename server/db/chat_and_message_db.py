from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import List,Dict,Optional
import os   
from dotenv import load_dotenv
load_dotenv()
from bson import ObjectId

MONGODB_URL = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.n8n_agent_db
chats_collection = db.chats
messages_collection = db.messages

async def create_new_chat(user_email:str,title:str = "New Chat"):
    chat_doc = {
        "user_email": user_email,
        "title": title,
        "created_at": datetime.utcnow(),
        "last_accessed": datetime.utcnow()
    }
    result = await chats_collection.insert_one(chat_doc)
    if result.inserted_id:
        return {"success":True,"chat_id":str(result.inserted_id)}
    return {"success":False}

async def get_user_chats(user_email:str):
    cursor = chats_collection.find({"user_email":user_email}).sort("last_accessed",-1)

    chats = []
    async for chat in cursor:
        chats.append({
            "id": str(chat["_id"]),
            "title": chat["title"],
            "created_at": chat["created_at"],
            "last_accessed": chat["last_accessed"],
        })
    return chats

async def get_most_recent_chat(user_email: str) -> Optional[str]:
    chat = await chats_collection.find_one(
        {"user_email": user_email},
        sort=[("last_accessed", -1)]
    )
    return str(chat["_id"]) if chat else None

async def update_chat_access(chat_id: str):
    await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {
            "$set": {"last_accessed": datetime.utcnow()}
        }
    )

async def update_chat_title(chat_id: str, title: str):
    """Update chat title"""
    await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"title": title}}
    )

async def save_message(chat_id: str, role: str, content: str):
    """Save a message to MongoDB"""
    message_doc = {
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    }
    await messages_collection.insert_one(message_doc)
    
    

async def get_chat_messages(chat_id: str) -> List[Dict]:
    """Get all messages for a chat"""
    cursor = messages_collection.find(
        {"chat_id": chat_id}
    ).sort("timestamp", 1)
    
    messages = []
    async for message in cursor:
        messages.append({
            "role": message["role"],
            "content": message["content"],
            "timestamp": message["timestamp"]
        })
    return messages

async def delete_chat(chat_id: str):
    """Delete a chat and all its messages"""
    await messages_collection.delete_many({"chat_id": chat_id})
    await chats_collection.delete_one({"_id": ObjectId(chat_id)})