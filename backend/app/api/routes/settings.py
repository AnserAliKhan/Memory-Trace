from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def settings():
    return {"message": "not implemented"}