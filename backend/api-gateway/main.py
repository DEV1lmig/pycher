from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from fastapi.responses import JSONResponse, StreamingResponse, Response # Add Response
from fastapi.requests import Request
from fastapi import status
import json # Should already be there
import traceback # Add this import at the top of your

app = FastAPI(title="Python Learning Platform API Gateway")

ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Local development
    "http://16.171.239.251:5173",  # Production domain
    # Add other allowed origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Use specific origins in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "X-Request-ID"] # Added common headers
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

            if method == "get":
                response = await request_func(
                    url,
                    headers=headers,
                    params=request.query_params,
                    timeout=30.0
                )
            else:
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

@app.api_route("/api/v1/ai/chat/stream", methods=["POST"])
async def ai_chat_stream(request: Request):
    """Proxy streaming chat to the AI service."""
    service_name = "ai-service"
    if service_name not in SERVICE_URLS:
        raise HTTPException(status_code=503, detail=f"{service_name.replace('-', ' ').title()} not available")

    url = f"{SERVICE_URLS[service_name]}/chat/stream"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}
    body = await request.body()

    async def stream_response():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, headers=headers, content=body) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk

    return StreamingResponse(stream_response(), media_type="text/plain")

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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="User service not available")

    url = f"{SERVICE_URLS['user-service']}/api/v1/users/{path}"

    async with httpx.AsyncClient() as client:
        try:
            method_upper = request.method.upper()
            headers = {
                k: v for k, v in request.headers.items()
                if k.lower() not in ['host', 'content-length', 'connection', 'transfer-encoding', 'user-agent']
            }
            # For file downloads, a long timeout might be needed if generation is slow,
            # but user-service generates to BytesIO first, so this is for the transfer.
            req_kwargs = {
                "method": method_upper,
                "url": url,
                "headers": headers,
                "params": request.query_params,
                "timeout": 700.0
            }

            if method_upper not in ["GET", "HEAD"]:
                body_bytes = await request.body()
                req_kwargs["content"] = body_bytes

            # Make the request to the user-service
            response = await client.request(**req_kwargs)

            print(f"[{path}] Proxy: Upstream call to {url} made. Status: {response.status_code}")
            response.raise_for_status() # Check for HTTP errors from user-service

            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response(status_code=status.HTTP_204_NO_CONTENT)

            content_type_header = response.headers.get("content-type", "")
            content_type_lower = content_type_header.lower()

            excluded_headers = {
                "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
                "te", "trailers", "transfer-encoding", "upgrade",
                "content-encoding", # httpx handles decompression
                # "content-length" will be set by FastAPI's Response
            }
            forward_headers = {
                k: v for k, v in response.headers.items() if k.lower() not in excluded_headers
            }

            if "application/json" in content_type_lower:
                # For JSON, parse and return as JSONResponse
                # httpx's response.json() uses response.text which reads the content.
                try:
                    json_content = response.json()
                    return JSONResponse(content=json_content, status_code=response.status_code, headers=forward_headers)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid JSON response from user service.")
            else:
                # For PDF and other non-JSON, read the entire content then return as Response
                # This buffers the entire PDF in the API Gateway's memory.
                file_bytes = await response.aread() # Reads all bytes from the upstream response
                print(f"[{path}] Proxy: PDF/Non-JSON branch. Read {len(file_bytes)} bytes from upstream.")

                return Response(
                    content=file_bytes,
                    status_code=response.status_code,
                    headers=forward_headers,
                    media_type=content_type_header
                )

        except httpx.RequestError as e:
            print(f"!!!!!!!!!!!! HTTRequestError IN USER_SERVICE_PROXY FOR {url} !!!!!!!!!!!!")
            traceback.print_exc()
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Error connecting to user service: {str(e)}")
        except httpx.HTTPStatusError as e:
            print(f"!!!!!!!!!!!! HTTPStatusError IN USER_SERVICE_PROXY FOR {url} !!!!!!!!!!!!")
            traceback.print_exc()
            error_detail = "User service error"
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text if e.response.text else f"User service returned status {e.response.status_code}"
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
        except Exception as e:
            print(f"!!!!!!!!!!!! UNEXPECTED ERROR IN USER_SERVICE_PROXY (outer try-except) FOR {url} !!!!!!!!!!!!")
            traceback.print_exc()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while proxying to the user service.")

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"!!!!!!!!!!!! GENERIC EXCEPTION HANDLER CAUGHT !!!!!!!!!!!!") # Add this
    traceback.print_exc() # Add this
    # logger.error(f"Unhandled exception caught by generic_exception_handler: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Check API Gateway logs."}, # Modified detail
        headers={"Access-Control-Allow-Origin": "*"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
