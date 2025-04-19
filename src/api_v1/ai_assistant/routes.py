from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.crud import get_current_active_user
from src.api_v1.ai_assistant.schemas import AIChatRequest, AIChatResponse
from src.core.database import User, postgres_helper
from src.core.utils.AIAssistantService import ai_assistant_service

ai_assistant_router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


@ai_assistant_router.post("/chat", response_model=AIChatResponse)
async def chat_with_ai(
    request: AIChatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    """
    Chat with the AI assistant. The assistant will provide personalized responses
    based on the user's profile data.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Construct user profile for personalization
    user_profile = {
        "name": current_user.name,
        "age": current_user.age,
        "gender": current_user.gender,
        "occupation": current_user.occupation,
        "bio": current_user.bio,
        "interests": current_user.interests or [],
        "cleanliness_level": current_user.cleanliness_level,
        "sleep_habits": current_user.sleep_habits,
        "rent_budget": current_user.rent_budget,
        "location": current_user.location,
        "smoking_preference": current_user.smoking_preference,
        "pet_preference": current_user.pet_preference,
        "study_location": current_user.study_location,
        "study_program": current_user.study_program,
        "accommodation_preference": current_user.accommodation_preference,
    }

    try:
        response = await ai_assistant_service.get_assistant_response(
            user_id=current_user.id, query=request.message, user_profile=user_profile
        )

        return AIChatResponse(
            response=response,
            conversation_id=str(
                current_user.id
            ),  # Using user ID as conversation ID for simplicity
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI response: {str(e)}",
        )
