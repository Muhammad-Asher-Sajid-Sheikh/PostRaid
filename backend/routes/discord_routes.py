from services.scheduler_service import schedule_test_task, scheduler

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.discord_service import send_to_channel

router = APIRouter(tags=["Discord Messaging"])


# Request model for sending outbound messages
class SendMessageRequest(BaseModel):
    content: str


# Request model for receiving inbound messages
class ReceiveMessageRequest(BaseModel):
    author: str
    content: str
    channel_id: str


# -------------------------------------------------------------------
# ENDPOINT 1: Send a message to your private Discord channel
# -------------------------------------------------------------------
@router.post("/send-message")
async def send_message(payload: SendMessageRequest):
    """Hits Discord API to post a message into your private channel."""
    success = await send_to_channel(payload.content)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to deliver message to Discord channel.")

    # Schedule the next job for 1 hour later
    schedule_test_task(2, "Kindly Reply to this message.")  # Add the 1-hour test job
    scheduler.start()
    print("Scheduler started!")

    return {"status": "success", "message_sent": payload.content}


# -------------------------------------------------------------------
# ENDPOINT 2: Triggered whenever a user sends a message in Discord
# -------------------------------------------------------------------
@router.post("/receive-message")
async def receive_message(payload: ReceiveMessageRequest):
    """Triggered automatically when an inbound Discord message is received."""
    print(f"\n📩 NEW INBOUND DISCORD MESSAGE!")
    print(f"From: {payload.author}")
    print(f"Content: {payload.content}")
    print(f"Channel ID: {payload.channel_id}\n")

    if scheduler.get_job("send_message_job"):
        print("✅ Cancelling the scheduled job since a reply was received.")
        scheduler.remove_job("send_message_job")

    # Put your business logic here (e.g., database logging, command processing, AI triggers)

    return {"status": "received", "content": payload.content}