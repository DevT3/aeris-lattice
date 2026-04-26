from pydantic import BaseModel
from typing import Optional

class AskRequest(BaseModel):
    prompt: str
    arbiter_url: Optional[str] = None
    arbiter_model: Optional[str] = None