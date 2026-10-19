import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from routes.discord_routes import router as discord_router
from services.discord_service import start_bot
from services.scheduler_service import schedule_test_task, scheduler


from psycopg import Connection
from database.db import pool, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    # 1. Launch Discord Bot in background task
    bot_task = asyncio.create_task(start_bot())
    print("FastAPI running... Discord listener active.")

    # 2. Schedule and start the background scheduler
    # schedule_test_task(1, "Test message")  # Add the 1-hour test job
    # scheduler.start()
    # print("Scheduler started!")
    
    # Pause execution here while FastAPI app runs

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT
                );
            """)
            conn.commit()
    yield

    pool.close()
    # --- SHUTDOWN LOGIC ---
    bot_task.cancel()
    scheduler.shutdown()
    print("Scheduler and Discord listener shut down.")


app = FastAPI(title="Discord Two-Way Gateway", lifespan=lifespan)

# Register routes
app.include_router(discord_router)