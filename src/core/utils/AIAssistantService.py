import json
from typing import Dict, Any, Optional, List

from yandex_cloud_ml_sdk import YCloudML

from src.core.data import settings


class AIAssistantService:
    def __init__(self):
        self.sdk = YCloudML(
            folder_id=settings.yandex_folder_id,
            auth=settings.yandex_api_key,
        )
        self.model = self.sdk.models.completions("yandexgpt-lite")
        self.model.configure(
            temperature=0.7,  # More creative/diverse responses
            max_tokens=2000,
        )

        # Simple in-memory storage for user conversation history
        # In a production environment, this should be stored in a database
        self._conversation_history = {}

    async def get_assistant_response(
        self, user_id: int, query: str, user_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get a response from the AI assistant tailored to the user's query and profile.

        Args:
            user_id: The user's ID for maintaining conversation history
            query: The user's message/query
            user_profile: Optional dictionary containing user profile data for personalization

        Returns:
            str: The AI assistant's response
        """
        system_prompt = """
        You are a helpful personal assistant for people looking for roommates or dealing with roommate situations.
        You provide personalized advice based on the user's profile and preferences.
        Your advice should be practical, respectful, and considerate of the user's situation.
        You can help with:
        - Roommate conflict resolution
        - Apartment/dorm organization tips
        - Cleaning and maintenance advice
        - Budget planning for shared living
        - Communication strategies
        - Study habits and productivity
        - Social dynamics in shared living

        Personalize your responses based on the user's profile information when relevant.
        Be friendly, empathetic, and conversational in your tone. Ты универсальный помозник для студента и помогаешь ему во всем, в рецптах и вообще.
        """

        # Initialize conversation history for this user if it doesn't exist
        if user_id not in self._conversation_history:
            self._conversation_history[user_id] = []

        # Add the current query to history (limit history to last 10 messages)
        self._conversation_history[user_id].append({"role": "user", "text": query})
        if len(self._conversation_history[user_id]) > 10:
            self._conversation_history[user_id] = self._conversation_history[user_id][
                -10:
            ]

        # Create a context with user profile information
        user_context = ""
        if user_profile:
            user_context = "User Profile Information:\n"

            if user_profile.get("name"):
                user_context += f"- Name: {user_profile.get('name')}\n"

            if user_profile.get("age"):
                user_context += f"- Age: {user_profile.get('age')}\n"

            if user_profile.get("gender"):
                user_context += f"- Gender: {user_profile.get('gender')}\n"

            if user_profile.get("occupation"):
                user_context += f"- Occupation: {user_profile.get('occupation')}\n"

            if user_profile.get("study_location"):
                user_context += f"- Study Location/Institution: {user_profile.get('study_location')}\n"

            if user_profile.get("study_program"):
                user_context += (
                    f"- Study Program: {user_profile.get('study_program')}\n"
                )

            if user_profile.get("cleanliness_level"):
                user_context += f"- Cleanliness Level (1-5): {user_profile.get('cleanliness_level')}\n"

            if user_profile.get("sleep_habits"):
                user_context += f"- Sleep Habits: {user_profile.get('sleep_habits')}\n"

            if user_profile.get("rent_budget"):
                user_context += f"- Rent Budget: {user_profile.get('rent_budget')}\n"

            if user_profile.get("location"):
                user_context += (
                    f"- Preferred Location: {user_profile.get('location')}\n"
                )

            if user_profile.get("smoking_preference"):
                user_context += (
                    f"- Smoking Preference: {user_profile.get('smoking_preference')}\n"
                )

            if user_profile.get("pet_preference"):
                user_context += (
                    f"- Pet Preference: {user_profile.get('pet_preference')}\n"
                )

            if user_profile.get("accommodation_preference"):
                pref = user_profile.get("accommodation_preference")
                accommodation_text = {
                    "apartment": "Apartment",
                    "dormitory": "Dormitory",
                    "no_preference": "No strong preference",
                }.get(pref, pref)
                user_context += f"- Accommodation Preference: {accommodation_text}\n"

            if user_profile.get("interests") and isinstance(
                user_profile.get("interests"), list
            ):
                interests = user_profile.get("interests")
                if interests:
                    user_context += f"- Interests: {', '.join(interests)}\n"

            if user_profile.get("bio"):
                user_context += f"- Bio: {user_profile.get('bio')}\n"

        # Prepare the conversation messages
        messages = [
            {"role": "system", "text": system_prompt},
        ]

        # Add user context as a system message if available
        if user_context:
            messages.append(
                {
                    "role": "system",
                    "text": f"Here is information about the user that might be helpful for personalization:\n\n{user_context}",
                }
            )

        # Add conversation history
        for msg in self._conversation_history[user_id]:
            messages.append(msg)

        try:
            # Call the Yandex GPT model
            operation = self.model.run_deferred(messages)
            result = operation.wait()
            response_text = result.text

            # Save the assistant's response to history
            self._conversation_history[user_id].append(
                {"role": "assistant", "text": response_text}
            )

            return response_text
        except Exception as e:
            return f"I apologize, but I encountered an error processing your request: {str(e)}"


# Instantiate the service
ai_assistant_service = AIAssistantService()
