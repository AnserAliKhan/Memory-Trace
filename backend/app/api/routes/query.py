from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def query():
    return {"message": "not implemented"}