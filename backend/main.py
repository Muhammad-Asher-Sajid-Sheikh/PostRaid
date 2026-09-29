import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.discord_routes import router as discord_router
from services.discord_service import start_bot
from services.scheduler_service import schedule_test_task, scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    # 1. Launch Discord Bot in background task
    bot_task = asyncio.create_task(start_bot())
    print("FastAPI running... Discord listener active.")

    # 2. Schedule and start the background scheduler
    schedule_test_task()  # Add the 10-second test job
    scheduler.start()
    print("Scheduler started!")
    
    # Pause execution here while FastAPI app runs
    yield
    
    # --- SHUTDOWN LOGIC ---
    bot_task.cancel()
    scheduler.shutdown()
    print("Scheduler and Discord listener shut down.")


app = FastAPI(title="Discord Two-Way Gateway", lifespan=lifespan)

# Register routes
app.include_router(discord_router)