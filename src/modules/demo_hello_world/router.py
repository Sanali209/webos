from fastapi import APIRouter
from .models import HelloMessage

router = APIRouter(prefix="/hello", tags=["demo"])

@router.get("/")
async def say_hello():
    return {"message": "Hello from the WebOS Module System!"}

@router.post("/message")
async def create_message(content: str):
    msg = HelloMessage(content=content)
    await msg.create()
    return msg
