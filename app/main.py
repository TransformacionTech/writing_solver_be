from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, pipeline, rag, topics
from app.routers import curation


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    from pathlib import Path
    Path(settings.chroma_persist_path).mkdir(parents=True, exist_ok=True)

    from app.scheduler import start_scheduler
    start_scheduler()

    yield

    # Shutdown
    from app.services.pipeline_service import _executor
    _executor.shutdown(wait=False)

    from app.scheduler import stop_scheduler
    stop_scheduler()


app = FastAPI(
    title="Writing Solver API",
    description="API for orchestrating CrewAI agents for LinkedIn post generation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],
)

app.include_router(pipeline.router)
app.include_router(topics.router)
app.include_router(rag.router)
app.include_router(auth.router)
app.include_router(curation.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
