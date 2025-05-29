from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routes import router as user_router
from models import Base, engine

from redis import Redis

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_user = os.getenv("REDIS_USER")
redis_password = os.getenv("REDIS_PASSWORD")

redis_client = Redis(
    host=redis_host,
    port=redis_port,
    username=redis_user,
    password=redis_password,
    db=0,
    decode_responses=True
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Python Learning Platform - User Service")

@app.on_event("startup")
def clear_tokens_on_startup():
    # Remove all access and refresh tokens on server restart
    for key in redis_client.scan_iter("token:*"):
        redis_client.delete(key)
    for key in redis_client.scan_iter("refresh_token:*"):
        redis_client.delete(key)
    print("All tokens cleared on startup.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api/v1/users", tags=["users"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
