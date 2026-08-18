from fastapi import APIRouter, UploadFile, File, HTTPException
from src.services.storage import storage_service

router = APIRouter()

@router.post("/upload")
async def upload_post_media(file: UploadFile = File(...)):
    # Validate MIME type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        # Upload directly from memory stream
        spaces_key, cdn_url = storage_service.upload_image(
            file_data=file.file,
            filename=file.filename,
            folder="events"
        )
        return {
            "spaces_key": spaces_key,
            "image_url": cdn_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))