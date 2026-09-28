import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes.discord_routes import router as discord_router
from services.discord_service import start_bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch Discord Bot in background task
    bot_task = asyncio.create_task(start_bot())
    print("FastAPI running... Discord listener active.")
    yield
    # Shutdown: Cancel background listener
    bot_task.cancel()


app = FastAPI(title="Discord Two-Way Gateway", lifespan=lifespan)

# Register routes
app.include_router(discord_router)