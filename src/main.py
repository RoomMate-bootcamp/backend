from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from starlette.middleware.sessions import SessionMiddleware

from src.api_v1.user.routes import users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(root_path="/api/v1", lifespan=lifespan, debug=True)
app.include_router(
    users_router,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


app.add_middleware(SessionMiddleware, secret_key="123")
