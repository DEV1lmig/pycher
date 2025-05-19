from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import routes
from database import engine, Base
import logging

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Content Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1/content")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8002)
