from fastapi import FastAPI
from src.routes.post import router as posts_router

app = FastAPI(title="PostRaid Core Engine", version="1.0.0")

app = FastAPI(title="PostRaid API")
app.include_router(posts_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "engine": "FastAPI + SQLAlchemy"}