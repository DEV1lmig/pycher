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
    "ai-service": "http://ai-service:8005", # Verify hostname is 'ai-service' and port is '8005'
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
    """Route AI requests to the AI service"""
    service_name = "ai-service" # Define service name
    if service_name not in SERVICE_URLS:
        raise HTTPException(status_code=503, detail=f"{service_name.replace('-', ' ').title()} not available")

    url = f"{SERVICE_URLS[service_name]}/{endpoint}"
    try:
        body = await request.json()
    except Exception:
         # Handle cases where body might not be JSON or is empty if needed
        body = None

    # Forward the request to the AI service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                # Use json=body only if body is not None, otherwise use content=await request.body()
                # Or handle based on expected content type
                json=body,
                timeout=60.0 # Increased timeout for potentially long AI calls
            )
            # Check if the AI service itself returned an error
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            return response.json()
        except httpx.RequestError as e:
            # Error connecting to the AI service
            raise HTTPException(status_code=503, detail=f"Error connecting to AI service: {str(e)}")
        except httpx.HTTPStatusError as e:
             # AI service returned an error status code (e.g., 4xx, 5xx)
            # Log the error and forward a generic or specific error
            # logger.error(f"AI service returned error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json() if e.response.content else "AI service error")

@app.api_route("/api/v1/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def user_service_proxy(request: Request, path: str):
    """Proxy requests to the user service"""
    if "user-service" not in SERVICE_URLS:
        raise HTTPException(status_code=503, detail="User service not available")

    url = f"{SERVICE_URLS['user-service']}/api/v1/users/{path}"

    async with httpx.AsyncClient() as client:
        try:
            method = request.method.lower()
            request_func = getattr(client, method)
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}
            content = await request.body() if method != "get" else None

            response = await request_func(
                url,
                headers=headers,
                params=request.query_params,
                content=content,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Error: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json() if e.response.content else "User service error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
