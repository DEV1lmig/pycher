from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import logging
from typing import Dict, Optional, List, Any
import json

# Import from the new validators module
# Assuming validators.py is in the same directory as main.py
from validators import VALIDATOR_MAP, DynamicValidationResult

app = FastAPI(title="Python Code Execution and Validation Service")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class CodeRequest(BaseModel):
    exercise_id: int
    code: str
    input_data: Optional[str] = None # Default input for the first/only scenario if not specified in rules
    timeout: Optional[int] = 10  # Default timeout in seconds

class ValidationResultModel(BaseModel):
    output: Optional[str] = None # Output from the user's code if relevant
    error: Optional[str] = None  # Validation errors or runtime errors
    execution_time: float
    passed: bool               # Did the code pass validation?

# --- Global Exercise Data ---
EXERCISES_FILE_PATH = os.path.join(os.path.dirname(__file__), 'shared', 'seed_data', 'seed_exercises.json')
EXERCISES_DATA: Dict[int, Dict[str, Any]] = {}

def load_exercises_on_startup():
    global EXERCISES_DATA
    try:
        with open(EXERCISES_FILE_PATH, 'r', encoding='utf-8') as f:
            exercises_list = json.load(f)
            for exercise in exercises_list:
                if "id" in exercise: # Ensure exercise has an ID
                    EXERCISES_DATA[int(exercise["id"])] = exercise
                else:
                    # Log a warning for exercises missing an ID
                    print(f"Warning: Exercise found without an 'id' field: {exercise.get('title', 'Untitled Exercise')}")
        print(f"Successfully loaded {len(EXERCISES_DATA)} exercises.")
    except FileNotFoundError:
        print(f"ERROR: Exercises file not found at {EXERCISES_FILE_PATH}")
        # Potentially raise an error or exit if exercises are critical for startup
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {EXERCISES_FILE_PATH}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading exercises: {e}")

@app.on_event("startup")
async def startup_event():
    load_exercises_on_startup()

# Validation logic (DynamicValidationResult, run_user_code_sandboxed, specific validators)
# has been moved to validators.py

# --- API Endpoints ---
@app.get("/health")
async def health_check():
    return {"status": "healthy", "loaded_exercises": len(EXERCISES_DATA)}

@app.post("/execute", response_model=ValidationResultModel)
async def execute_and_validate_code(request: CodeRequest):
    start_time = time.time()

    exercise_config = EXERCISES_DATA.get(request.exercise_id)
    if not exercise_config:
        # Log the error and return a structured error response
        logging.error(f"Exercise ID {request.exercise_id} not found in EXERCISES_DATA.")
        return ValidationResultModel(
            output=None,
            error=f"Exercise with ID {request.exercise_id} not found.",
            execution_time=time.time() - start_time,
            passed=False
        )

    validation_type = exercise_config.get("validation_type")
    # These are the overall rules for the exercise, including any predefined scenarios
    exercise_rules_from_config = exercise_config.get("validation_rules", {})

    if not validation_type or validation_type not in VALIDATOR_MAP:
        logging.error(f"No validator defined for exercise type: '{validation_type}' (Exercise ID: {request.exercise_id}).")
        return ValidationResultModel(
            output=None,
            error=f"No validator defined for exercise type: '{validation_type}'.",
            execution_time=time.time() - start_time,
            passed=False
        )

    validator_func = VALIDATOR_MAP[validation_type]

    final_run_result: DynamicValidationResult # To hold the result of the execution logic
    run_description_for_log: str

    # --- Logic to decide execution path ---
    if request.input_data is not None:
        # Case 1: input_data IS provided in the request (e.g., from "Ejecutar Código" textarea)
        run_description_for_log = f"Direct run with user input: '{request.input_data}'"
        logging.info(f"EID {request.exercise_id}: {run_description_for_log}")

        # Ensure dynamic_output is handled here for single input run
        if validation_type in ["simple_print", "saludo_personalizado", "variable_output", "dynamic_output", "function_and_output"]:
            final_run_result = validator_func(
                user_code=request.code,
                rules=exercise_rules_from_config,
                input_data=request.input_data,    # Pass direct input to the validator
                timeout=request.timeout
            )
        elif validation_type == "function_check":
            logging.warning(f"EID {request.exercise_id}: 'input_data' provided for 'function_check'. This is typically handled by scenarios with 'args'. Performing a default scenario interpretation if possible, or this might indicate a misconfiguration if the function doesn't use stdin.")
            final_run_result = validator_func(
                user_code=request.code,
                rules=exercise_rules_from_config,
                scenario_config={},  # or a real scenario if you have one
                timeout=request.timeout
            )
            # If your function_check validator *cannot* work this way, this should be an error:
            # final_run_result = DynamicValidationResult(passed=False, message="Direct input not directly applicable to function_check without a specific scenario context.", actual_output=None) #execution_time=0.0)

        else:
            final_run_result = DynamicValidationResult(passed=False, message=f"Unsupported validation type '{validation_type}' for direct input run.", actual_output=None)

    else:
        # Case 2: input_data is NOT provided in the request (e.g. "Entregar Ejercicio")
        run_description_for_log = "Predefined scenarios run or default run"
        logging.info(f"EID {request.exercise_id}: {run_description_for_log} (request.input_data was None)")

        scenarios_in_config: List[Dict[str, Any]] = exercise_rules_from_config.get("scenarios", [])

        if not scenarios_in_config:
            # No predefined scenarios. Perform a default run.
            # This is where dynamic_output should generate its multiple cases.
            logging.info(f"EID {request.exercise_id}: No predefined scenarios found. Performing a default run.")
            run_description_for_log = "Default Run (No Scenarios Defined, No Request Input)"
            if validation_type in ["simple_print", "saludo_personalizado", "variable_output", "dynamic_output", "function_and_output"]: # Ensure dynamic_output is here
                final_run_result = validator_func(
                    user_code=request.code,
                    rules=exercise_rules_from_config,
                    input_data=None, # Validator will generate cases if input_data is None
                    timeout=request.timeout
                )
            elif validation_type == "function_check":
                 final_run_result = DynamicValidationResult(passed=False, message=f"Configuration error: 'function_check' (EID {request.exercise_id}) requires 'scenarios' with 'args' in 'validation_rules' when no direct input_data or predefined scenarios are provided.", actual_output=None)
            else:
                 final_run_result = DynamicValidationResult(passed=False, message=f"Unsupported validation type '{validation_type}' for default run without scenarios.", actual_output=None)
        else:
            # Run all predefined scenarios from the exercise configuration.
            logging.info(f"EID {request.exercise_id}: Running {len(scenarios_in_config)} predefined scenarios.")
            overall_passed_scenarios = True
            accumulated_message = "All predefined scenarios passed."
            # For overall output, we might take the first scenario's output or first failing.
            representative_output: Optional[str] = None

            for i, scenario_item_config in enumerate(scenarios_in_config):
                scenario_specific_input = scenario_item_config.get("input")
                current_scenario_desc = scenario_item_config.get("description", f"Scenario {i+1}")
                logging.debug(f"  Running predefined scenario: {current_scenario_desc} with its input: '{scenario_specific_input}'")

                scenario_run_result_item: DynamicValidationResult
                if validation_type in ["simple_print", "saludo_personalizado", "variable_output", "dynamic_output", "function_and_output"]:
                    scenario_run_result_item = validator_func(
                        user_code=request.code,
                        rules=exercise_rules_from_config, # Overall exercise rules
                        input_data=scenario_specific_input, # Input for this specific scenario
                        timeout=request.timeout
                    )
                elif validation_type == "function_check":
                    scenario_run_result_item = validator_func(
                        user_code=request.code,
                        rules=exercise_rules_from_config,
                        scenario_config=scenario_item_config,
                        timeout=request.timeout
                    )
                else:
                    scenario_run_result_item = DynamicValidationResult(passed=False, message=f"Unsupported type '{validation_type}' for scenario.", actual_output=None) # Removed execution_time=0.0

                if i == 0: # Capture first scenario's output as representative if all pass
                    representative_output = scenario_run_result_item.actual_output

                if not scenario_run_result_item.passed:
                    overall_passed_scenarios = False
                    accumulated_message = f"{current_scenario_desc} failed: {scenario_run_result_item.message}"
                    representative_output = scenario_run_result_item.actual_output # Output of the failing scenario
                    logging.info(f"  Predefined Scenario {current_scenario_desc} FAILED: {scenario_run_result_item.message}")
                    break # Stop on first failed predefined scenario
                else:
                    logging.info(f"  Predefined Scenario {current_scenario_desc} PASSED.")

            final_run_result = DynamicValidationResult(
                passed=overall_passed_scenarios,
                message=accumulated_message,
                actual_output=representative_output
                # No execution_time here
            )
            run_description_for_log = "Predefined Scenarios Batch Run"

    # --- Prepare and return the final response ---
    execution_total_time = time.time() - start_time
    logging.info(f"EID {request.exercise_id}: {run_description_for_log} - Final Result Passed: {final_run_result.passed}, Message: {final_run_result.message}, Total Endpoint ExecTime: {execution_total_time:.4f}s")

    return ValidationResultModel(
        output=final_run_result.actual_output if final_run_result.actual_output is not None else "",
        error=final_run_result.message if not final_run_result.passed else None,
        execution_time=execution_total_time, # Use the overall calculated time
        passed=final_run_result.passed
    )

if __name__ == "__main__":
    import uvicorn
    # Ensure exercises are loaded for local run if app isn't fully started via uvicorn command
    if not EXERCISES_DATA:
        load_exercises_on_startup()
    uvicorn.run(app, host="0.0.0.0", port=8001)
