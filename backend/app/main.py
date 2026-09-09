from contextlib import asynccontextmanager
import os

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai_provider import analyze_case_update


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mawthooq:mawthooq_dev@localhost:5432/mawthooq",
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    yield


app = FastAPI(
    title="Mawthooq API",
    description="Backend foundation for AI-powered legal case intelligence.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mawthooq-api"}


@app.get("/health/database")
def database_health() -> dict[str, str]:
    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            database_name = cursor.fetchone()[0]
    return {"status": "ok", "database": database_name}


@app.post("/ai/feasibility")
def ai_feasibility(payload: dict[str, str]) -> dict[str, object]:
    update_text = payload.get("update_text", "").strip()
    if not update_text:
        return {
            "status": "invalid_input",
            "message": "update_text is required",
            "requires_human_review": True,
        }
    return analyze_case_update(update_text)
