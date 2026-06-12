from fastapi import APIRouter, UploadFile

router = APIRouter()

@router.post("/import")
async def import_file(file: UploadFile):
    return {"filename": file.filename}