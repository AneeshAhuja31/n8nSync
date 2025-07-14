from pydantic import BaseModel
from typing import List,Dict,Any
class ChatMessage(BaseModel):
    message: str
    chat_id: str = "default"
    gemini_api_key: str  
    n8n_api_key: str 

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]

