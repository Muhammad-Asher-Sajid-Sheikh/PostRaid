import logging
from fastapi import APIRouter, Request, Response, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.src.services import whatsapp_client
from backend.src.services import whatsapp_client
from src.services.database import get_db
from src.models.db import PublishLog
from src.services.storage import storage_service

logger = logging.getLogger(__name__)

# Re-using the router you created in Step 4
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

def process_inbound_message(payload: Dict[str, Any], db: Session):
    """
    Background worker that parses the Meta WhatsApp payload, extracts 
    triggers/images, and executes the core GenAI/Database logic.
    """
    try:
        # 1. Safely navigate the nested Meta JSON payload
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Check if this is a message event
                if "messages" in value:
                    for message in value["messages"]:
                        sender_phone = message.get("from")
                        message_id = message.get("id")
                        message_type = message.get("type")

                        logger.info(f"Received {message_type} from {sender_phone}")

                        # 2. Extract Text Triggers
                        if message_type == "text":
                            text_body = message.get("text", {}).get("body", "").strip()
                            
                            # Give the user immediate feedback
                            whatsapp_client.send_text_message(
                                to_phone=sender_phone, 
                                text=f"Agent received your command: '{text_body}'. Generating now..."
                            )
                            
                            # -> Run LangChain agent here <-

                        elif message_type == "image":
                            media_id = message.get("image", {}).get("id")
                            
                            # 1. Download file from Meta's servers
                            image_bytes = whatsapp_client.download_media(media_id)
                            
                            # 2. Upload to DigitalOcean Spaces
                            spaces_key, cdn_url = storage_service.upload_image(
                                file_data=image_bytes, 
                                filename=f"whatsapp_{media_id}.jpg"
                            )
                            
                            # 3. Inform the user
                            whatsapp_client.send_text_message(
                                to_phone=sender_phone, 
                                text=f"Image securely saved to CDN: {cdn_url}"
                            )
                        
                        # 4. Log the execution/receipt in PostgreSQL
                        log_entry = PublishLog(
                            platform="WHATSAPP_INBOUND",
                            whatsapp_message_id=message_id,
                            response_payload=message  # Store the raw message for auditing/debugging
                        )
                        db.add(log_entry)
                        db.commit()

                # Alternatively, handle outbound message status updates (Delivered/Read/Failed)
                elif "statuses" in value:
                    for status_update in value["statuses"]:
                        status_str = status_update.get("status")
                        msg_id = status_update.get("id")
                        logger.info(f"Message {msg_id} status changed to: {status_str}")

    except Exception as e:
        logger.error(f"Failed to process webhook payload: {str(e)}")
        # In a real app, you might want to use Sentry or rollback db transactions here
        db.rollback()


@router.post("/")
async def receive_whatsapp_webhook(
    request: Request, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Handles incoming POST requests from Meta Cloud API.
    Must return 200 OK immediately to prevent Meta from retrying.
    """
    try:
        # Parse the JSON payload
        payload = await request.json()
        
        # Verify it's a WhatsApp webhook payload
        if payload.get("object") == "whatsapp_business_account":
            # Hand the payload off to the background task
            background_tasks.add_task(process_inbound_message, payload, db)
            
            # Immediately acknowledge receipt
            return Response(status_code=status.HTTP_200_OK, content="EVENT_RECEIVED")
            
        else:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Webhook ingestion error: {str(e)}")
        # Even on ingestion error, returning 200 prevents Meta from spamming your broken endpoint
        return Response(status_code=status.HTTP_200_OK, content="ERROR_ACKNOWLEDGED")