import os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mawthooq:mawthooq_dev@localhost:5432/mawthooq",
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
