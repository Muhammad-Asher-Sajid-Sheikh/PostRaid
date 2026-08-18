from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from src.services.database import get_db
from src.models.db import Post, PostStatus
from src.services.storage import storage_service

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_post(
    title: str = Form(...),
    caption: Optional[str] = Form(None),
    event_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Creates a new Post record. If an image file is provided, 
    uploads it to DigitalOcean Spaces and stores the public CDN URL.
    """
    image_url = None
    spaces_key = None

    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

        # Upload file directly to DigitalOcean Spaces
        spaces_key, image_url = storage_service.upload_image(
            file_data=image.file,
            filename=image.filename,
            folder="posts"
        )

    new_post = Post(
        title=title,
        caption=caption,
        event_id=event_id,
        image_url=image_url,
        spaces_key=spaces_key,
        status=PostStatus.PENDING
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Fetches a single post by ID."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Deletes a post record and cleans up its file from DigitalOcean Spaces."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    # Remove asset from DigitalOcean Spaces if present
    if post.spaces_key:
        try:
            storage_service.delete_image(post.spaces_key)
        except Exception as e:
            # Log error if needed, but continue deleting DB record
            pass

    db.delete(post)
    db.commit()
    return None