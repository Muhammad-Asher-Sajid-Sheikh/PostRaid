import os
import httpx
import logging
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    WHATSAPP_PHONE_ID: str
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_API_VERSION: str = "v20.0"
    
    class Config:
        env_file = ".env"

settings = Settings()

class WhatsAppClient:
    def __init__(self):
        self.phone_id = settings.WHATSAPP_PHONE_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.base_url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
        
        # Standard headers for all API requests
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def send_text_message(self, to_phone: str, text: str) -> Dict[str, Any]:
        """
        Sends a standard text message back to the WhatsApp user.
        """
        url = f"{self.base_url}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }

        with httpx.Client() as client:
            response = client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def send_image_message(self, to_phone: str, image_url: str, caption: str = "") -> Dict[str, Any]:
        """
        Sends an image to the WhatsApp user using your public DigitalOcean Spaces URL.
        """
        url = f"{self.base_url}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }

        with httpx.Client() as client:
            response = client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def download_media(self, media_id: str) -> Optional[bytes]:
        """
        Downloads a media file sent by a user to your webhook.
        This requires a 2-step process in the Graph API:
        1. Fetch the media metadata to get the download URL.
        2. Download the actual binary using the token.
        """
        metadata_url = f"{self.base_url}/{media_id}"
        
        with httpx.Client() as client:
            # Step 1: Get the download URL
            meta_response = client.get(metadata_url, headers=self.headers)
            meta_response.raise_for_status()
            
            media_url = meta_response.json().get("url")
            if not media_url:
                logger.error(f"Failed to find URL for media_id: {media_id}")
                return None
                
            # Step 2: Download the binary file using the Authorization header
            # Note: Do not send 'Content-Type: application/json' for file downloads
            download_headers = {"Authorization": f"Bearer {self.access_token}"}
            file_response = client.get(media_url, headers=download_headers)
            file_response.raise_for_status()
            
            return file_response.content


# Instantiate for global use
whatsapp_client = WhatsAppClient()