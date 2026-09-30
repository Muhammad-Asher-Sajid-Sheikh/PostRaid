from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.discord_service import send_to_channel

# Use AsyncIOScheduler (not BlockingScheduler)
scheduler = AsyncIOScheduler()

async def sendMessage(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Executing scheduled job: {msg}")
    
    success = await send_to_channel(msg)
    
    if not success:
        print("❌ Failed to deliver message to Discord channel.")
        return
        
    print("✅ Message successfully sent to Discord channel!")

    

def schedule_test_task(waitForHours, message):
    run_time = datetime.now() + timedelta(hours = waitForHours)
    
    scheduler.add_job(
        sendMessage,
        'date',
        run_date=run_time,
        args=[message],
        id = "send_message_job"
    )
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️ Job scheduled for {waitForHours} hours from now ({run_time.strftime('%H:%M:%S')}).")