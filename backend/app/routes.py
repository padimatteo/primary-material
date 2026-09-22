from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine


router = APIRouter()


class Message(BaseModel):
    message: str


class Health(BaseModel):
    status: str
    database: str


@router.get("/hello", response_model=Message, tags=["general"])
def hello() -> Message:
    return Message(message="Hello from Homebase!")


@router.get("/health", response_model=Health, tags=["general"])
def health() -> Health:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from error

    return Health(status="ok", database="connected")

