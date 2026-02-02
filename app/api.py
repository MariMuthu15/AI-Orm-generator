from fastapi import APIRouter, Header, HTTPException
from .schemas import QueryRequest, QueryResponse
from .ai_orm import generate_filters_with_ai
import os

router = APIRouter()
SECRET = os.getenv("BACKEND_SECRET")


@router.post("/generate", response_model=QueryResponse)
def generate(req: QueryRequest, backend_secret: str = Header(None)):
    if not backend_secret or backend_secret != SECRET:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    orm = generate_filters_with_ai(req.query)
    return QueryResponse(orm=orm)
