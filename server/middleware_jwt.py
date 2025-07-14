import jwt
import os
from datetime import datetime,timedelta
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from dotenv import load_dotenv
import secrets
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY",secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def create_jwt_token(user_data:dict) -> str:
    payload = {
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),  # Fixed: use datetime.utcnow()
        "iat": datetime.utcnow()  # issued at time
    }
    return jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)

def verify_jwt_token(token:str) -> dict:
    try:
        payload = jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

async def get_user_from_token(request: Request):
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    payload = verify_jwt_token(token)
    return {
        "name": payload.get("name"),
        "email": payload.get("email")
    }
    