import json
from typing import List, Dict, Any, Tuple

from yandex_cloud_ml_sdk import YCloudML

from src.core.data import settings
from src.core.database.alchemy_models.user import User


class AIMatchingService:
    """Service for matching roommates using AI and analyzing their compatibility"""

    def __init__(self):
        self.sdk = YCloudML(
            folder_id=settings.yandex_folder_id,
            auth=settings.yandex_api_key,
        )
        self.model = self.sdk.models.completions("yandexgpt-lite")
        self.model.configure(
            temperature=0.3,  # Lower temperature for more deterministic results
            max_tokens=2000,
        )

    def calculate_compatibility_score(
        self, user1: User, user2: User
    ) -> Tuple[float, str]:
        """
        Calculate compatibility score between two users with detailed analysis

        Args:
            user1: First user
            user2: Second user

        Returns:
            Tuple containing:
                - Compatibility score (0-100)
                - Detailed explanation with potential matches and conflicts
        """
        system_prompt = """
        You are an expert roommate matching algorithm that provides detailed compatibility analyses.

        Analyze two potential roommates' profiles and:
        1. Calculate a compatibility score from 0-100
        2. Provide a detailed explanation that highlights:
           - Areas where interests, habits, and preferences align
           - Potential conflict areas based on lifestyle differences
           - Specific compatibility considerations for shared living

        Format your response as a JSON object with:
        - 'score': number between 0-100
        - 'explanation': detailed analysis with specific insights

        Be specific and realistic in your assessment. Consider how their habits, schedules,
        cleanliness levels, and lifestyle preferences would interact in a shared living space.
        Highlight both potential areas of harmony and possible friction points.
        """

        # Prepare user data for analysis
        user_data = {
            "user1": {
                "name": user1.name,
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
                "pet_preference": user1.pet_preference,
                "study_location": user1.study_location,
                "study_program": user1.study_program,
                "accommodation_preference": user1.accommodation_preference,
            },
            "user2": {
                "name": user2.name,
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
                "pet_preference": user2.pet_preference,
                "study_location": user2.study_location,
                "study_program": user2.study_program,
                "accommodation_preference": user2.accommodation_preference,
            },
        }

        user_prompt = (
            "Analyze these two potential roommates for compatibility, highlighting specific "
            "points of alignment and potential conflicts:\n"
            f"{json.dumps(user_data, indent=2, ensure_ascii=False)}"
        )

        messages = [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt},
        ]

        try:
            # Call the AI model
            operation = self.model.run_deferred(messages)
            result = operation.wait()

            # Parse the response
            ai_response = json.loads(result.text)
            score = float(ai_response.get("score", 50))

            # Generate a structured explanation with clearly separated matches and conflicts
            explanation = self._format_compatibility_explanation(
                ai_response.get("explanation", ""), user1.name, user2.name
            )

            return (score, explanation)
        except (json.JSONDecodeError, ValueError, Exception) as e:
            # Fallback in case of errors
            return (50, f"Не удалось проанализировать совместимость: {str(e)}")

    def _format_compatibility_explanation(
        self, raw_explanation: str, user1_name: str, user2_name: str
    ) -> str:
        """Format the compatibility explanation to highlight matches and conflicts more clearly"""
        if not raw_explanation:
            return "Информация о совместимости недоступна."

        # Ensure names are available for personalization
        user1_name = user1_name or "Первый пользователь"
        user2_name = user2_name or "Второй пользователь"

        # Replace generic references with actual names for more personalized analysis
        formatted_explanation = raw_explanation.replace("User 1", user1_name)
        formatted_explanation = formatted_explanation.replace("User 2", user2_name)
        formatted_explanation = formatted_explanation.replace("user1", user1_name)
        formatted_explanation = formatted_explanation.replace("user2", user2_name)

        return formatted_explanation

    def get_top_matches(
        self, current_user: User, potential_matches: List[User], limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find the top compatible matches for a user

        Args:
            current_user: The user seeking matches
            potential_matches: List of potential matches to analyze
            limit: Maximum number of matches to return

        Returns:
            List of dictionaries containing user, score and explanation
        """
        import random

        matches = []

        # Create a copy and shuffle to ensure randomization
        shuffled_matches = list(potential_matches)
        random.shuffle(shuffled_matches)

        for potential_match in shuffled_matches:
            if potential_match.id == current_user.id:
                continue

            score, explanation = self.calculate_compatibility_score(
                current_user, potential_match
            )

            matches.append(
                {
                    "user": potential_match,
                    "compatibility_score": score,
                    "compatibility_explanation": explanation,
                }
            )

        # Include a mix of high and medium compatibility matches
        # to increase variety (70% sorted by score, 30% random)
        if len(matches) > limit:
            # Sort by score
            matches.sort(key=lambda x: x["compatibility_score"], reverse=True)

            # Take a portion of the top matches
            top_portion = int(limit * 0.7)
            top_matches = matches[:top_portion]

            # Take some random matches from the remaining pool
            remaining_matches = matches[top_portion:]
            random_matches = random.sample(
                remaining_matches, min(limit - top_portion, len(remaining_matches))
            )

            return top_matches + random_matches

        return matches[:limit]


# Singleton instance
ai_matching_service = AIMatchingService()
