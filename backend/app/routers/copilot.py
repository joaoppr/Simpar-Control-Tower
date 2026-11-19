from fastapi import APIRouter
from pydantic import BaseModel

from ..config import settings
from ..services.copilot import answer

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


class Msg(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    message: str
    history: list[Msg] = []


@router.post("/chat")
def chat(body: ChatIn):
    return answer(body.message, [m.model_dump() for m in body.history])


@router.get("/status")
def status():
    return {"mode": "openai" if settings.openai_api_key else "offline", "model": settings.openai_model if settings.openai_api_key else None}
