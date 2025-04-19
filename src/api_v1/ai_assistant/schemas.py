from typing import List, Optional
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    text: str = Field(..., description="Message text content")


class MessageResponse(BaseModel):
    text: str = Field(..., description="Message text content")
    is_user: bool = Field(
        ..., description="True if message is from user, False if from assistant"
    )
    timestamp: str = Field(..., description="Message timestamp")


class ConversationResponse(BaseModel):
    messages: List[MessageResponse] = Field(
        ..., description="List of messages in the conversation"
    )


class AIChatRequest(BaseModel):
    message: str = Field(..., description="Message to send to the AI assistant")


class AIChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    conversation_id: Optional[str] = Field(
        None, description="Conversation identifier for continued context"
    )
