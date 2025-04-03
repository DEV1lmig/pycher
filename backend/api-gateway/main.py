from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="Python Learning Platform API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs - in production, these would be environment variables
SERVICE_URLS = {
    "execution-service": "http://execution-service:8001",
    "content-service": "http://content-service:8002",
    "ai-service": "http://ai-service:8004",
    "user-service": "http://user-service:8003",
    # Add other services as they're implemented
}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/services")
async def list_services():
    return {
        "services": list(SERVICE_URLS.keys())
    }

@app.post("/api/v1/execute")
async def execute_code(request: Request):
    """Route code execution requests to the execution service"""
    if "execution-service" not in SERVICE_URLS:
        raise HTTPException(status_code=503, detail="Execution service not available")

    # Get the raw request body
    body = await request.json()

    # Forward the request to the execution service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['execution-service']}/execute",
                json=body,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            return {"error": f"Error: {str(e)}", "output": "", "execution_time": 0}

@app.get("/api/v1/content/{path:path}")
async def content_service(request: Request, path: str):
    """Route content requests to the content service"""
    if "content-service" not in SERVICE_URLS:
        raise HTTPException(status_code=503, detail="Content service not available")

    # Forward the request to the content service
    url = f"{SERVICE_URLS['content-service']}/api/v1/content/{path}"

    async with httpx.AsyncClient() as client:
        try:
            # Forward the request method (GET, POST, etc)
            method = request.method.lower()
            request_func = getattr(client, method)

            # Get headers and query parameters
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}

            # Get body for non-GET requests
            content = await request.body() if method != "get" else None

            response = await request_func(
                url,
                headers=headers,
                params=request.query_params,
                content=content,
                timeout=30.0
            )

            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Error: {str(e)}")

@app.post("/api/v1/ai/{endpoint}")
async def ai_service(endpoint: str, request: Request):
    url = f"{SERVICE_URLS['ai-service']}/{endpoint}"
    body = await request.json()
    # Forward to AI service and return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
