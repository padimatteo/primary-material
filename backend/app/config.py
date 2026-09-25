import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://homebase:homebase@localhost:5432/homebase",
)

