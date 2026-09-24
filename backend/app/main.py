from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.coffee.routes import router as coffee_router
from app.routes import router


app = FastAPI(
    title="Homebase API",
    version="0.1.0",
    description="The API for a personal homebase.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(coffee_router, prefix="/api")
