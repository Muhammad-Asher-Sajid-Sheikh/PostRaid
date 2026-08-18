import uuid
import mimetypes
from typing import Tuple, Union, BinaryIO
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic_settings import BaseSettings

# Configuration Settings
class Settings(BaseSettings):
    SPACES_ACCESS_KEY: str
    SPACES_SECRET_KEY: str
    SPACES_REGION: str = "nyc3"
    SPACES_BUCKET: str
    SPACES_ENDPOINT: str
    SPACES_CDN_URL: str  # Custom domain or standard DO CDN endpoint

    class Config:
        env_file = ".env"

settings = Settings()

class SpacesStorageService:
    def __init__(self):
        # Initialize boto3 client pointed at DigitalOcean Spaces endpoint
        self.session = boto3.session.Session()
        self.client = self.session.client(
            "s3",
            region_name=settings.SPACES_REGION,
            endpoint_url=settings.SPACES_ENDPOINT,
            aws_access_key_id=settings.SPACES_ACCESS_KEY,
            aws_secret_access_key=settings.SPACES_SECRET_KEY,
        )
        self.bucket = settings.SPACES_BUCKET

    def upload_image(
        self,
        file_data: Union[BinaryIO, bytes],
        filename: str,
        folder: str = "posts"
    ) -> Tuple[str, str]:
        """
        Uploads an image file to DigitalOcean Spaces with public-read permissions.

        :param file_data: File-like object or bytes to upload.
        :param filename: Original filename to extract extension and MIME type.
        :param folder: Subfolder inside the bucket (default: "posts").
        :return: A tuple of (spaces_key, cdn_url).
        """
        # Determine content type (defaulting to image/jpeg if unknown)
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "image/jpeg"

        # Extract extension and create a unique object key to prevent overwrites
        file_ext = filename.split(".")[-1] if "." in filename else "jpg"
        unique_id = uuid.uuid4().hex
        spaces_key = f"{folder}/{unique_id}.{file_ext}"

        try:
            # Upload to DigitalOcean Spaces with Public Access
            self.client.upload_fileobj(
                Fileobj=file_data,
                Bucket=self.bucket,
                Key=spaces_key,
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": content_type,
                },
            )

            # Construct public CDN URL for fast delivery (e.g., via WhatsApp)
            cdn_url = f"{settings.SPACES_CDN_URL.rstrip('/')}/{spaces_key}"
            return spaces_key, cdn_url

        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Failed to upload image to DigitalOcean Spaces: {str(e)}") from e

    def delete_image(self, spaces_key: str) -> bool:
        """
        Deletes an object from DigitalOcean Spaces using its key.

        :param spaces_key: Key/path of the file in the bucket.
        :return: True if successful.
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=spaces_key)
            return True
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Failed to delete image from DigitalOcean Spaces: {str(e)}") from e

# Instantiate a single service instance
storage_service = SpacesStorageService()