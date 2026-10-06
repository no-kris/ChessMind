from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/analyze")
async def analyze():
    return {"message": "Frontend can talk to backend."}
