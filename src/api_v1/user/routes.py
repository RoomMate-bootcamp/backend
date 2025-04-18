from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

users_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)
