from pydantic import BaseModel
from typing import List,Dict,Any
class ChatMessage(BaseModel):
    message: str
    chat_id: str = "default"

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]

