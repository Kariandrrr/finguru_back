from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.config import settings
from core.models import db_helper

from .authorisation import router as authorisation_router
from .api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("dispose engine")
    await db_helper.dispose()



main_app = FastAPI(
    lifespan=lifespan,
)

origins = {
    "https://miniapp-5a40e.web.app",  # твой Firebase Hosting URL
    "http://localhost:5173",  # для локальной разработки (Vite)
    "http://localhost:3000",  # если create-react-app
}

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
main_app.include_router(api_router, prefix=settings.api.prefix)
main_app.include_router(authorisation_router, prefix=settings.authorisation.prefix)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app", reload=True, host=settings.run.host, port=settings.run.port
    )
