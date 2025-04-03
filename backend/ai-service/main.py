import os
import logging
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # Added Field for default values
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions as google_exceptions # Import specific exceptions
import google.generativeai as genai
# Removed: from google.generativeai import GenerativeModel (covered by genai.*)

# --- Configuration ---

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API Key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it.")

# Configure the Gemini client globally
genai.configure(api_key=GEMINI_API_KEY)

# Choose a standard model name
# Examples: "gemini-1.5-flash-latest", "gemini-1.0-pro"
MODEL_NAME = "gemini-2.5-pro-exp-03-25"

# --- Pydantic Models ---

class HintRequest(BaseModel):
    code: str
    error: Optional[str] = None
    instruction: Optional[str] = None
    difficulty: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")

class SolutionEvaluationRequest(BaseModel):
    code: str
    expected_output: str
    actual_output: str
    description: Optional[str] = None

class CodeFeedbackRequest(BaseModel):
    code: str
    challenge_description: Optional[str] = None
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")

class AIResponse(BaseModel):
    content: str
    suggestions: Optional[List[str]] = None

# --- AI Interaction Logic ---

# Define retry strategy for API calls
# Retry on specific transient errors if needed, or general exceptions
retry_decorator = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    # Example: Add specific retryable exceptions if known
    # retry=retry_if_exception_type((google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable))
    retry=retry_if_exception_type(Exception) # Retrying on general exception for now
)

@retry_decorator
async def generate_ai_response(prompt: str) -> Dict[str, Any]:
    """
    Generates a response from the Gemini model asynchronously with retry logic.
    """
    try:
        logger.info(f"Sending prompt to Gemini model ({MODEL_NAME})...")
        response = await genai.generate_text_async(prompt=prompt, model=MODEL_NAME)
        if not response or not response.text:
            logger.error("AI response generation failed or returned no text.")
            raise HTTPException(
                status_code=500,
                detail="Unable to get AI assistance right now. Please try again later."
            )
        logger.info("Successfully received response from Gemini.")
        return {"content": response.text}

    except google_exceptions.GoogleAPIError as e:
        logger.exception(f"Gemini API Error: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Gemini API Error: {str(e)}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during AI generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI model interaction failed: {str(e)}")


# --- FastAPI Application ---

app = FastAPI(
    title="AI Code Assistant Service",
    description="Provides hints, evaluation, feedback, and explanations for Python code using Gemini.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/health", tags=["Infrastructure"])
async def health_check():
    """Checks if the service is running."""
    return {"status": "healthy"}

@app.post("/hint", response_model=AIResponse, tags=["Code Assistance"])
async def get_hint(request: HintRequest):
    """Provides a hint for the given Python code and context."""
    prompt = f"""
    Act as a helpful AI programming tutor.
    I am learning Python at the {request.difficulty} level and need help with my code.

    My code:
    ```python
    {request.code}
    ```

    {f"I encountered this error: {request.error}" if request.error else ""}
    {f"The task instruction was: {request.instruction}" if request.instruction else ""}

    Please provide a concise, helpful hint to guide me toward solving the problem.
    Focus on explaining the underlying concepts or suggesting specific areas to check.
    Do NOT provide the corrected code or the full solution. Keep the hint focused and actionable for a {request.difficulty} learner.
    """
    response_data = await generate_ai_response(prompt)
    return AIResponse(**response_data) # Unpack dict into the model

@app.post("/evaluate", response_model=AIResponse, tags=["Code Assistance"])
async def evaluate_solution(request: SolutionEvaluationRequest):
    """Evaluates a Python code solution against expected output."""
    prompt = f"""
    Act as an AI code evaluator.
    Evaluate the following Python code solution based on its output compared to the expected output.

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

    {f"The challenge description was: {request.description}" if request.description else ""}

    1. State clearly whether the actual output matches the expected output (Correct/Incorrect).
    2. If Incorrect:
        - Explain *why* the actual output is different from the expected output.
        - Provide specific, constructive feedback on what might be wrong in the code logic.
        - Explain the relevant programming concepts needed to fix the issue.
        - Do NOT provide the corrected code directly, but guide the user towards the fix.
    3. If Correct: Briefly confirm correctness and perhaps offer a small note on good practices if applicable.
    Keep the explanation clear and educational.
    """
    response_data = await generate_ai_response(prompt)
    return AIResponse(**response_data)

@app.post("/feedback", response_model=AIResponse, tags=["Code Assistance"])
async def get_code_feedback(request: CodeFeedbackRequest):
    """Provides feedback on Python code quality, style, and potential improvements."""
    prompt = f"""
    Act as an AI code reviewer providing feedback to a Python learner at the {request.level} level.

    Analyze the following Python code:
    ```python
    {request.code}
    ```

    {f"The code is intended to solve this challenge: {request.challenge_description}" if request.challenge_description else ""}

    Provide constructive feedback focusing on these areas, tailored for a {request.level} learner:
    1.  **Correctness & Logic:** Are there potential bugs, logical errors, or edge cases missed?
    2.  **Readability & Style:** Is the code easy to understand? Comment on naming, formatting (PEP 8), and structure.
    3.  **Efficiency & Best Practices:** Are there significantly more efficient ways to achieve the same result (considering the {request.level} level)? Are Pythonic idioms used appropriately?
    4.  **Potential Improvements:** Suggest specific, actionable improvements.

    Format your feedback clearly. Be encouraging and educational. Avoid overwhelming the learner with overly advanced concepts unless directly relevant and explained simply.
    """
    response_data = await generate_ai_response(prompt)

    # --- Rule-based Suggestions (kept from original, can be refined) ---
    # These are simple examples; more sophisticated static analysis or
    # asking the LLM for suggestions could be alternatives.
    suggestions = []
    code_lines = request.code.strip().split('\n')
    is_beginner = "beginner" in request.level.lower()
    is_intermediate_or_advanced = not is_beginner

    # Beginner suggestions
    if is_beginner:
        has_print = any("print(" in line for line in code_lines)
        has_def = any(line.strip().startswith("def ") for line in code_lines)
        if has_print and not has_def and len(code_lines) > 3:
             suggestions.append("Consider wrapping your main logic in a function (e.g., `def main(): ...`) for better organization and reusability.")
        if len(code_lines) > 10 and not has_def:
             suggestions.append("As your code grows, think about breaking it down into smaller, manageable functions.")

    # Intermediate/Advanced suggestions
    if is_intermediate_or_advanced:
        has_class = any(line.strip().startswith("class ") for line in code_lines)
        if not has_class and len(code_lines) > 20: # Threshold adjusted
             suggestions.append("For more complex logic or data structures, consider using classes to organize related data and functions (Object-Oriented Programming).")
        has_open = any("open(" in line for line in code_lines)
        has_with = any("with open(" in line for line in code_lines)
        if has_open and not has_with:
             suggestions.append("When working with files (`open()`), it's best practice to use a `with` statement to ensure the file is automatically closed, even if errors occur.")

    # Add suggestions to the response
    response_data["suggestions"] = suggestions
    # Ensure the AIResponse model can handle the data
    return AIResponse(**response_data)


@app.post("/explain", response_model=AIResponse, tags=["Code Assistance"])
async def explain_code(request: CodeFeedbackRequest):
    """Explains a piece of Python code line by line or concept by concept."""
    prompt = f"""
    Act as an AI programming tutor.
    Explain the following Python code to a student learning at the {request.level} level.

    Code:
    ```python
    {request.code}
    ```

    Provide a clear explanation of how this code works. You can go line-by-line or explain major blocks/concepts.
    Focus on:
    - What each part of the code does.
    - The purpose of the syntax and keywords used.
    - Any relevant programming concepts demonstrated (e.g., loops, functions, data types, specific library usage).
    - Keep the explanation appropriate for a {request.level} understanding. Avoid jargon where possible or explain it clearly.
    """
    response_data = await generate_ai_response(prompt)
    return AIResponse(**response_data)


# --- Run the Application ---
# Note: Changed port slightly to 8005 to avoid potential conflicts if 8004 is stuck
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AI Code Assistant Service...")
    # Consider using environment variables for host and port in production
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info") # Match uvicorn log level
