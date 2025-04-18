from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.auth.schemas import Token, UserCreate, UserResponse
from src.api_v1.auth.crud import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    get_user,
)
from src.core.data import settings
from src.core.database import User, postgres_helper

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_create: UserCreate,
        session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    existing_user = await get_user(user_create.username, session)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    query = select(User).where(User.email == user_create.email)
    result = await session.execute(query)
    
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )


    hashed_password = get_password_hash(user_create.password)
    new_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@auth_router.post("/login", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[AsyncSession, Depends(postgres_helper.session_dependency)],
):
    user = await authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/me", response_model=UserResponse)
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user
