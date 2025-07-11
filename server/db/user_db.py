import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.n8n_agent_db
user_collection = db.users

async def create_or_update_user(user_data:dict):
    email = user_data.get("email")
    check_if_user_exist = await user_collection.find_one({"email":email})
    if(check_if_user_exist):
        await user_collection.update_one(
            {"email":email},
            {
                "$set":{
                    "name":user_data.get("name"),
                    "last_login":datetime.utcnow(),
                    "is_active":True
                }
            }
        )
        return False
    else:
        insert_response = await user_collection.insert_one({
            "name":user_data.get("name"),
            "email":user_data.get("email"),
            "auth_provider":"google",
            "created_at":datetime.utcnow(),
            "last_login":datetime.utcnow(),
            "is_active":True
        })
        if insert_response.inserted_id:
            return True

async def set_user_inactive(email:str):
    update_response = await user_collection.update_one(
        {"email":email},
        {
            "$set":{
                "is_active":False
            }
        }
    )
    if update_response.did_upsert:
        return True
    return False
