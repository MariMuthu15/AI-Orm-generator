from fastapi import FastAPI
from .api import router

app = FastAPI(title="AI ORM Generator API")
app.include_router(router, prefix="/api")
