from pydantic import BaseModel, Field
from typing import Annotated, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Annotated[Optional[str], Field(default=None)]=None

class ChatResponse(BaseModel):
    reply: str
    session_id: Annotated[Optional[str], Field(default=None)]=None
    model: str