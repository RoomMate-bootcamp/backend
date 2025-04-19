import os
import json
from typing import List, Dict, Any, Tuple

from yandex_cloud_ml_sdk import YCloudML

from src.core.data import settings
from src.core.database.alchemy_models.user import User


class AIMatchingService:
    def __init__(self):
        self.sdk = YCloudML(
            folder_id=settings.yandex_folder_id,
            auth=settings.yandex_api_key,
        )
        self.model = self.sdk.models.completions('yandexgpt-lite')
        self.model.configure(
            temperature=0.3,
            max_tokens=2000,
        )

    def calculate_compatibility_score(self, user1: User, user2: User) -> Tuple[float, str]:
        system_prompt = (
            "You are an expert roommate matching algorithm. Analyze two potential roommates' "
            "profiles and calculate a compatibility score from 0-100 based on their preferences. "
            "Return a JSON object with 'score' (number) and 'explanation' (string) fields."
        )

        user_data = {
            "user1": {
                "age": user1.age,
                "gender": user1.gender,
                "occupation": user1.occupation,
                "bio": user1.bio,
                "interests": user1.interests or [],
                "cleanliness_level": user1.cleanliness_level,
                "sleep_habits": user1.sleep_habits,
                "rent_budget": user1.rent_budget,
                "location": user1.location,
                "smoking_preference": user1.smoking_preference,
                "pet_preference": user1.pet_preference
            },
            "user2": {
                "age": user2.age,
                "gender": user2.gender,
                "occupation": user2.occupation,
                "bio": user2.bio,
                "interests": user2.interests or [],
                "cleanliness_level": user2.cleanliness_level,
                "sleep_habits": user2.sleep_habits,
                "rent_budget": user2.rent_budget,
                "location": user2.location,
                "smoking_preference": user2.smoking_preference,
                "pet_preference": user2.pet_preference
            }
        }

        user_prompt = f"Analyze these two potential roommates for compatibility:\n{json.dumps(user_data, indent=2)}"

        messages = [
            {'role': 'system', 'text': system_prompt},
            {'role': 'user', 'text': user_prompt},
        ]

        operation = self.model.run_deferred(messages)
        result = operation.wait()

        try:
            ai_response = json.loads(result.text)
            score = float(ai_response.get('score', 50))
            explanation = ai_response.get('explanation', "No explanation provided")
            return (score, explanation)
        except (json.JSONDecodeError, ValueError):
            return (50, "Could not analyze compatibility - using default score")

    def get_top_matches(self, current_user: User, potential_matches: List[User], limit: int = 10) -> list[
        dict[str, Any]]:
        matches = []

        for potential_match in potential_matches:
            if potential_match.id == current_user.id:
                continue

            score, explanation = self.calculate_compatibility_score(current_user, potential_match)

            matches.append({
                "user": potential_match,
                "compatibility_score": score,
                "compatibility_explanation": explanation
            })

        matches.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return matches[:limit]


ai_matching_service = AIMatchingService()