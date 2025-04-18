from beanie import init_beanie, Document, UnionDoc
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app import MONGO_DSN, ENVIRONMENT, projectConfig
from app.routers import system

if ENVIRONMENT == "prod":
    app = FastAPI(
        title=projectConfig.__projname__,
        version=projectConfig.__version__,
        description=projectConfig.__description__,
        docs_url=None
    )

else:
    app = FastAPI(
        title=projectConfig.__projname__,
        version=projectConfig.__version__,
        description=projectConfig.__description__
    )

app.include_router(system.router)

@app.on_event('startup')
async def startup_event():
    client = AsyncIOMotorClient(MONGO_DSN)

    await init_beanie(
        database=client.get_default_database(),
        document_models=Document.__subclasses__() + UnionDoc.__subclasses__()
    )