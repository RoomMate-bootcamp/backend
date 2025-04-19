import aiohttp
from typing import Dict, Any, List, Tuple, Optional

BASE_URL = "http://127.0.0.1:8000/api/v1"


async def get_potential_roommates(token: str) -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(
                f"{BASE_URL}/users/roommates", headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception:
            return []


async def get_smart_matches(token: str, limit: int = 10) -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(
                f"{BASE_URL}/ai-matching/smart-matches?limit={limit}", headers=headers
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data.get("matches", [])
                return []
        except Exception:
            return []


async def get_compatibility_score(token: str, user_id: int) -> Tuple[float, str]:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(
                f"{BASE_URL}/ai-matching/{user_id}/compatibility", headers=headers
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data.get("score", 0), response_data.get(
                        "explanation", ""
                    )
                return 0, "Не удалось получить информацию о совместимости"
        except Exception:
            return 0, "Произошла ошибка при запросе информации о совместимости"


async def like_roommate(token: str, liked_id: int) -> Tuple[bool, bool]:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.post(
                f"{BASE_URL}/likes", headers=headers, json={"liked_id": liked_id}
            ) as response:
                if response.status == 201:
                    response_data = await response.json()
                    is_match = response_data.get("status") == "accepted"
                    return True, is_match
                return False, False
        except Exception:
            return False, False


async def get_matches(token: str) -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{BASE_URL}/matches/", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception:
            return []


async def get_likes_received(token: str, status=None) -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{BASE_URL}/likes/received"
            if status:
                url += f"?status={status}"

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception:
            return []


async def respond_to_like(token: str, like_id: int, accept: bool) -> bool:
    action = "accept" if accept else "decline"

    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.post(
                f"{BASE_URL}/likes/{like_id}/respond",
                headers=headers,
                json={"action": action},
            ) as response:
                return response.status == 200
        except Exception:
            return False
