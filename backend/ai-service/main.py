from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize the FastAPI app
app = FastAPI(title="AI Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
genai.configure(api_key=api_key)

# Set up the model
model = genai.GenerativeModel('gemini-pro')

# Define request/response models
class HintRequest(BaseModel):
    code: str
    error: Optional[str] = None
    instruction: Optional[str] = None
    difficulty: str = "beginner"  # beginner, intermediate, advanced

class SolutionEvaluationRequest(BaseModel):
    code: str
    expected_output: str
    actual_output: str
    description: Optional[str] = None

class CodeFeedbackRequest(BaseModel):
    code: str
    challenge_description: Optional[str] = None
    level: str = "beginner"  # beginner, intermediate, advanced

class AIResponse(BaseModel):
    content: str
    suggestions: Optional[List[str]] = None

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_ai_response(prompt: str) -> Dict[str, Any]:
    """Generate a response from the AI model with retry logic"""
    try:
        response = model.generate_content(prompt)
        return {"content": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/hint", response_model=AIResponse)
async def get_hint(request: HintRequest):
    # Build a prompt for the AI model based on the user's code and context
    prompt = f"""
    I am learning Python at the {request.difficulty} level and need help with my code.

    Here's my code:
    ```python
    {request.code}
    ```

    {f"I got this error: {request.error}" if request.error else ""}
    {f"The instruction was: {request.instruction}" if request.instruction else ""}

    Please provide a helpful hint that guides me in the right direction without giving me the complete solution.
    Focus on explaining concepts and suggesting approaches rather than providing actual code.
    """

    response = await generate_ai_response(prompt)
    return response

@app.post("/evaluate", response_model=AIResponse)
async def evaluate_solution(request: SolutionEvaluationRequest):
    # Build a prompt for the AI model to evaluate a solution
    prompt = f"""
    I need you to evaluate a Python solution.

    Code:
    ```python
    {request.code}
    ```

    Expected output:
    ```
    {request.expected_output}
    ```

    Actual output:
    ```
    {request.actual_output}
    ```

    {f"Challenge description: {request.description}" if request.description else ""}

    Please evaluate if the solution is correct. If not, provide clear feedback on what's wrong and how to fix it.
    Be educational in your response, explaining the concepts involved.
    """

    response = await generate_ai_response(prompt)
    return response

@app.post("/feedback", response_model=AIResponse)
async def get_code_feedback(request: CodeFeedbackRequest):
    # Build a prompt for the AI model to provide feedback on code quality
    prompt = f"""
    I am learning Python at the {request.level} level and would like feedback on my code.

    Here's my code:
    ```python
    {request.code}
    ```

    {f"This code is meant to: {request.challenge_description}" if request.challenge_description else ""}

    Please provide feedback on:
    1. Code readability and style
    2. Efficiency and best practices
    3. Potential improvements
    4. Any bugs or edge cases I should consider

    Given my {request.level} level, tailor your response to be educational while not overwhelming me.
    Include specific suggestions for improvement.
    """

    response = await generate_ai_response(prompt)

    # Add concrete suggestions
    suggestions = []
    if "beginner" in request.level.lower():
        if "print" in request.code and not request.code.strip().startswith("def"):
            suggestions.append("Consider wrapping your code in a function for reusability.")
        if len(request.code.split("\n")) > 10 and "def" not in request.code:
            suggestions.append("Your code is getting complex. Try breaking it into smaller functions.")

    if "intermediate" in request.level.lower() or "advanced" in request.level.lower():
        if "class" not in request.code and len(request.code.split("\n")) > 15:
            suggestions.append("Consider using classes to organize your code better.")
        if "with" not in request.code and ("open(" in request.code or "file" in request.code.lower()):
            suggestions.append("Use context managers (with statement) when working with files.")

    response["suggestions"] = suggestions
    return response

@app.post("/explain", response_model=AIResponse)
async def explain_code(request: CodeFeedbackRequest):
    # Build a prompt for the AI model to explain code
    prompt = f"""
    I'm a Python student at the {request.level} level and need help understanding this code:

    ```python
    {request.code}
    ```

    Please explain how this code works, line by line, in a way that's appropriate for my {request.level} level.
    Focus on helping me understand the concepts and programming patterns used.
    """

    response = await generate_ai_response(prompt)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
