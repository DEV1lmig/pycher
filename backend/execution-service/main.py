from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os
import signal
import time
from typing import Dict, Optional

app = FastAPI(title="Python Code Execution Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str
    input_data: Optional[str] = None # Add input_data field
    timeout: Optional[int] = 5  # Default timeout in seconds

class ExecutionResult(BaseModel):
    output: str
    error: str
    execution_time: float

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/execute", response_model=ExecutionResult)
async def execute_code(request: CodeRequest):
    start_time = time.time()

    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(request.code.encode())

    output = ""
    error = ""
    process_input = request.input_data.encode() if request.input_data is not None else None

    try:
        # Execute the Python code with resource limitations
        process = subprocess.Popen(
            ["python3", temp_file_path],
            stdin=subprocess.PIPE if process_input else None, # Provide stdin if input_data exists
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid  # Use process group for proper kill
        )

        try:
            # Wait for the process with timeout
            stdout, stderr = process.communicate(input=request.input_data, timeout=request.timeout) # Pass input to communicate
            output = stdout
            error = stderr
        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait() # Ensure process is reaped
            error = "Execution timed out. Your code took too long to run."
            output = stdout # Capture any output before timeout
            if process.stderr: # Capture any stderr before timeout
                 error += f"\nPartial stderr: {process.stderr.read()}"
    except Exception as e:
        error = f"Error executing code: {str(e)}"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    execution_time = time.time() - start_time

    return ExecutionResult(
        output=output,
        error=error,
        execution_time=execution_time
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
