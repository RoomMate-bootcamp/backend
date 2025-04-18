import aiohttp
import json
from typing import Dict, Any, Tuple, Optional

BASE_URL = "http://127.0.0.1:8000/api/v1"  # Or your actual API URL


async def check_user_exists(username: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                    f"{BASE_URL}/auth/register",
                    json={"username": username, "email": "temp@example.com", "password": "temppass"}
            ) as response:
                return response.status == 400
        except Exception:
            return False


async def register_user(username: str, email: str, password: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                    f"{BASE_URL}/auth/register",
                    json={"username": username, "email": email, "password": password}
            ) as response:
                return response.status == 201
        except Exception:
            return False


async def login_user(username: str, password: str) -> Tuple[bool, Optional[str]]:
    async with aiohttp.ClientSession() as session:
        try:
            # Using form data for OAuth2 login
            data = {"username": username, "password": password}
            async with session.post(f"{BASE_URL}/auth/login", data=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return True, response_data.get("access_token")
                return False, None
        except Exception:
            return False, None


async def get_user_profile(token: str) -> Optional[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(f"{BASE_URL}/users/me", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception:
            return None


async def update_user_profile(token: str, profile_data: Dict[str, Any]) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.put(
                    f"{BASE_URL}/users/me",
                    headers=headers,
                    json=profile_data
            ) as response:
                return response.status == 200
        except Exception:
            return False
