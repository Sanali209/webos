from src.core.models import CoreDocument
from pydantic import Field

class HelloMessage(CoreDocument):
    content: str = Field(..., description="The hello message content")
    
    class Settings:
        name = "hello_messages"
