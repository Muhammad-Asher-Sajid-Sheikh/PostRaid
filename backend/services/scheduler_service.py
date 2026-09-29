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

def schedule_test_task():
    run_time = datetime.now() + timedelta(seconds=10)
    
    scheduler.add_job(
        sendMessage,
        'date',
        run_date=run_time,
        args=["acknowledge"]
    )
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️ Job scheduled for 10 seconds from now ({run_time.strftime('%H:%M:%S')}).")