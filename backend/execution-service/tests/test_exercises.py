import pytest
import json
import os
import subprocess
import tempfile
import time
import importlib.util
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Path to the seed_exercises.json file
# Assumes tests are run from the project root directory (e.g., 'pycher')
SEED_FILE_PATH = os.path.join("backend", "shared", "seed_data", "seed_exercises.json")

def run_code_in_subprocess(code_string: str, input_str: Optional[str], timeout: int = 5) -> Tuple[str, str, float]:
    """
    Executes a string of Python code in a separate process.
    Returns (stdout, stderr, execution_time).
    """
    start_time = time.time()
    stdout_res, stderr_res = "", ""

    # Use a temporary file to write the code
    # Ensure the file is closed before Popen uses it, especially on Windows.
    temp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding='utf-8') as tmp_file:
            temp_file_path = tmp_file.name
            tmp_file.write(code_string)

        # Determine python executable
        python_executable = sys.executable # Use the same python that runs pytest

        process = subprocess.Popen(
            [python_executable, temp_file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        try:
            stdout_res, stderr_res = process.communicate(input=input_str, timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill() # Ensure the process is killed
            # Attempt to get any output after killing
            out, err = process.communicate()
            stdout_res += out
            stderr_res += err
            stderr_res += f"\nExecution timed out after {timeout} seconds."
        except Exception as e:
            stderr_res += f"\nError during Popen.communicate: {str(e)}"

    except FileNotFoundError:
        stderr_res = f"Error: Python interpreter '{sys.executable}' not found or temp file issue."
    except Exception as e:
        stderr_res = f"Error preparing or executing code: {str(e)}"
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    execution_time = time.time() - start_time
    return stdout_res, stderr_res, execution_time

def execute_function_from_code_string(code_string: str, function_name: str, args: List[Any], module_name_prefix="test_dyn_module") -> Any:
    """
    Dynamically loads a function from a string of Python code and executes it.
    """
    # Create a unique module name to avoid conflicts
    module_name = f"{module_name_prefix}_{uuid.uuid4().hex}"

    temp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding='utf-8', prefix=module_name + "_") as tmp_file:
            temp_file_path = tmp_file.name
            tmp_file.write(code_string)

        spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create module spec for {module_name} from {temp_file_path}")

        module_obj = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module_obj # Add to sys.modules before exec_module
        spec.loader.exec_module(module_obj)

        if not hasattr(module_obj, function_name):
            raise AttributeError(f"Function '{function_name}' not found in the provided code module '{module_name}'.")

        func_to_execute = getattr(module_obj, function_name)
        return func_to_execute(*args)

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if module_name in sys.modules:
            del sys.modules[module_name] # Clean up from sys.modules

def load_all_exercises_with_tests():
    """Loads exercises and their parsed test cases from the JSON file."""
    if not os.path.exists(SEED_FILE_PATH):
        # Try to construct path relative to this test file if absolute fails
        alt_path = os.path.join(os.path.dirname(__file__), "..", "seed_data", "seed_exercises.json")
        if os.path.exists(alt_path):
            current_seed_file_path = os.path.normpath(alt_path)
        else:
            pytest.fail(f"Seed file not found at {SEED_FILE_PATH} or {alt_path}")
    else:
        current_seed_file_path = SEED_FILE_PATH

    with open(current_seed_file_path, 'r', encoding='utf-8') as f:
        exercises_data = json.load(f)

    params_for_tests = []
    for exercise in exercises_data:
        exercise_id = exercise.get("id", "UnknownID")
        exercise_title = exercise.get("title", "Untitled Exercise")
        solution_code = exercise.get("solution_code")

        if not solution_code:
            print(f"Warning: Exercise ID {exercise_id} ('{exercise_title}') has no solution_code. Skipping.")
            continue

        try:
            raw_test_cases = exercise.get('test_cases', '[]')
            parsed_test_cases = json.loads(raw_test_cases) if raw_test_cases else []
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse test_cases for exercise ID {exercise_id} ('{exercise_title}'). Error: {e}. Skipping.")
            continue
        except KeyError:
            print(f"Warning: 'test_cases' key missing for exercise ID {exercise_id} ('{exercise_title}'). Skipping.")
            continue

        if not parsed_test_cases:
            # print(f"Info: No test cases found for exercise ID {exercise_id} ('{exercise_title}').")
            pass # Allow exercises with no test cases, they just won't be tested

        for i, test_case in enumerate(parsed_test_cases):
            # Sanitize title and description for test ID
            safe_title = "".join(c if c.isalnum() else "_" for c in exercise_title[:30])
            case_desc = test_case.get('description', f"case_{i+1}")
            safe_case_desc = "".join(c if c.isalnum() else "_" for c in case_desc[:30])

            test_id = f"ex{exercise_id}_{safe_title}_{safe_case_desc}"
            params_for_tests.append(pytest.param(exercise, test_case, id=test_id))

    return params_for_tests

# Generate test parameters when the module is loaded
exercise_test_parameters = load_all_exercises_with_tests()

@pytest.mark.parametrize("exercise_details, test_case_details", exercise_test_parameters)
def test_exercise_solution_code(exercise_details: Dict[str, Any], test_case_details: Dict[str, Any]):
    solution_code = exercise_details["solution_code"]
    exercise_id = exercise_details["id"]
    exercise_title = exercise_details["title"]

    test_type = test_case_details.get("test_type") # Default to stdio if not specified

    if test_type == "function_return" or test_type == "function_return_type":
        function_name = test_case_details.get("function_name")
        args = test_case_details.get("args", [])

        if not function_name:
            pytest.fail(f"Exercise ID {exercise_id} ('{exercise_title}'), test_type '{test_type}' requires 'function_name' in test_case.")

        try:
            actual_return_value = execute_function_from_code_string(solution_code, function_name, args)
        except Exception as e:
            pytest.fail(f"Exercise ID {exercise_id} ('{exercise_title}'): Failed to execute function '{function_name}'. Error: {e}")

        if test_type == "function_return":
            expected_return_value = test_case_details.get("expected_return_value")
            assert actual_return_value == expected_return_value, \
                f"Exercise ID {exercise_id} ('{exercise_title}'): Function '{function_name}' with args {args}. Expected return: {expected_return_value}, Got: {actual_return_value}"

        elif test_type == "function_return_type":
            expected_return_type_name = test_case_details.get("expected_return_type")
            if not expected_return_type_name:
                 pytest.fail(f"Exercise ID {exercise_id} ('{exercise_title}'), test_type 'function_return_type' requires 'expected_return_type'.")

            actual_type_name = type(actual_return_value).__name__
            assert actual_type_name == expected_return_type_name, \
                f"Exercise ID {exercise_id} ('{exercise_title}'): Function '{function_name}'. Expected return type: '{expected_return_type_name}', Got: '{actual_type_name}'"

    else: # Default to stdio test (input/output)
        input_data = test_case_details.get("input")
        expected_output = test_case_details.get("output")

        if expected_output is None:
            pytest.fail(f"Exercise ID {exercise_id} ('{exercise_title}'): Stdio test case is missing 'output' field.")

        actual_output, actual_error, _ = run_code_in_subprocess(solution_code, input_data)

        # Normalize line endings (CRLF to LF) for consistent comparison
        normalized_actual_output = actual_output.replace('\r\n', '\n')
        normalized_expected_output = expected_output.replace('\r\n', '\n')

        assert normalized_actual_output == normalized_expected_output, \
            (f"Exercise ID {exercise_id} ('{exercise_title}'): Input '{input_data}'.\n"
             f"Expected STDOUT:\n'''{normalized_expected_output}'''\n"
             f"Actual STDOUT:\n'''{normalized_actual_output}'''\n"
             f"Actual STDERR:\n'''{actual_error.strip()}'''")

        # Optionally, assert that stderr is empty if no error is expected by the test case design.
        # This basic version doesn't assume stderr expectations unless explicitly part of 'output'.
        # If a test is *designed* to produce a specific error, 'output' might contain that, or a new field 'expected_error' would be needed.
