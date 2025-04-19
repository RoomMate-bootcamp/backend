from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import postgres_helper


async def get_session() -> AsyncSession:
    async with postgres_helper.session_factory() as session:
        yield session
