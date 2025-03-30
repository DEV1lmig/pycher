from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routes import router as user_router
from models import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Python Learning Platform - User Service")

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
    uvicorn.run(app, host="0.0.0.0", port=8002)
