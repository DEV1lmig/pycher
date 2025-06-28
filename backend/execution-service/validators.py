import ast
import subprocess
import tempfile
import os
import time
import signal
import importlib.util
import random
import json
import asyncio
import inspect
from typing import Dict, Optional, List, Any, Tuple

# --- Result Class ---
class DynamicValidationResult:
    def __init__(self, passed: bool, message: str = "", actual_output: Optional[str] = None, details: Optional[Dict[str, Any]] = None): # Changed details to Dict[str, Any]
        self.passed = passed
        self.message = message
        self.actual_output = actual_output
        self.details = details or {}

# --- Code Execution Helper ---

PRINT_INTERCEPT_PREAMBLE = """
import builtins as _builtins_for_print_capture
import json as _json_for_print_capture
import sys as _sys_for_print_capture

_original_print_func_for_capture = _builtins_for_print_capture.print
_captured_print_args_list_for_validation = []

def _custom_print_for_validation_capture(*args, **kwargs):
    global _captured_print_args_list_for_validation
    # Capture type of the first argument if it exists
    # This is a simplification; for multiple args in one print, or complex sep/end,
    # more sophisticated capture would be needed if rules demand it.
    # For now, we assume exercises with expected_types usually print one main item per call.
    if args:
        first_arg = args[0]
        _captured_print_args_list_for_validation.append({
            "type": type(first_arg).__name__
            # "value_repr": repr(first_arg) # Could be added for debugging
        })
    # Call the original print to ensure output still goes to actual stdout
    _original_print_func_for_capture(*args, **kwargs)

_builtins_for_print_capture.print = _custom_print_for_validation_capture

# User code will be injected after this line by the calling function
"""

PRINT_INTERCEPT_EPILOGUE_MARKER = "###PRINT_METADATA_SEPARATOR_D7A3F###"
PRINT_INTERCEPT_EPILOGUE = f"""
# This epilogue code runs after the user's script.
# It prints the captured print argument types using the original stdout.
_sys_for_print_capture.stdout.write("{PRINT_INTERCEPT_EPILOGUE_MARKER}\\n")
_sys_for_print_capture.stdout.write(_json_for_print_capture.dumps(_captured_print_args_list_for_validation) + "\\n")
_sys_for_print_capture.stdout.flush()
"""

def run_user_code_sandboxed(
    code_string: str,
    input_data: Optional[str] = None,
    timeout: int = 5,
    capture_print_types: bool = False # New flag
) -> Tuple[str, str, bool, int, List[Dict[str, str]]]: # Added List for captured types
    """
    Runs user code in a sandbox.
    If capture_print_types is True, injects code to capture print() arg types.
    Returns: (user_stdout, stderr, timed_out, exit_code, captured_print_metadata_list)
    """
    code_to_run = code_string.replace('\r\n', '\n')
    if capture_print_types:
        code_to_run = PRINT_INTERCEPT_PREAMBLE + code_to_run + PRINT_INTERCEPT_EPILOGUE

    user_stdout_res, stderr_res, timed_out_res, exit_code_res = "", "", False, -1
    captured_print_metadata = [] # Initialize

    tmp_file_path = None # Ensure tmp_file_path is defined for finally block
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, newline='\n', encoding='utf-8') as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(code_to_run)

        # ... (rest of the subprocess.Popen and communicate logic remains the same) ...
        process_args = ["python", tmp_file_path]
        process = subprocess.Popen(
            process_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, # Keep as text for easier splitting later
            encoding='utf-8', # Specify encoding
            errors='replace', # Handle potential decoding errors in output
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        try:
            # stdout_bytes, stderr_bytes = process.communicate(input=input_data.encode('utf-8') if input_data else None, timeout=timeout)
            # stdout_res = stdout_bytes.decode('utf-8', errors='replace')
            # stderr_res = stderr_bytes.decode('utf-8', errors='replace')
            # Using text=True handles encoding/decoding, but be mindful of raw stdout for parsing
            raw_stdout, raw_stderr = process.communicate(input=input_data, timeout=timeout)
            exit_code_res = process.returncode

            # Now, parse raw_stdout if capture_print_types was True
            if capture_print_types:
                parts = raw_stdout.split(f"{PRINT_INTERCEPT_EPILOGUE_MARKER}\n", 1)
                user_stdout_res = parts[0]
                if len(parts) > 1:
                    try:
                        # The second part should be the JSON list, potentially with a trailing newline
                        json_data_str = parts[1].strip()
                        if json_data_str: # Ensure it's not empty before parsing
                            captured_print_metadata = json.loads(json_data_str)
                    except json.JSONDecodeError as e:
                        # If JSON parsing fails, log it or add to stderr for debugging
                        # This indicates an issue with the injected code or unexpected output
                        stderr_res += f"\n[Validator Info] Failed to parse print type metadata: {e}. Raw metadata part: {parts[1][:200]}"
                        # user_stdout_res might contain the marker if splitting failed as expected
                else:
                    # Marker not found, something went wrong with injection or output
                    user_stdout_res = raw_stdout # Assume all output is user's
                    stderr_res += "\n[Validator Info] Print type metadata marker not found in output."
            else:
                user_stdout_res = raw_stdout

            stderr_res = raw_stderr # Keep stderr as is

        except subprocess.TimeoutExpired:
            if hasattr(os, 'killpg') and hasattr(os, 'getpgid'):
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait(timeout=1)
                    if process.poll() is None: os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception: pass
            else: process.kill()
            process.wait()

            # Try to get partial output even on timeout
            partial_stdout = ""
            if process.stdout:
                try: partial_stdout = process.stdout.read()
                except: pass

            if capture_print_types: # Attempt to parse even partial output
                parts = partial_stdout.split(f"{PRINT_INTERCEPT_EPILOGUE_MARKER}\n", 1)
                user_stdout_res = parts[0]
                # No metadata parsing on timeout, too unreliable
            else:
                user_stdout_res = partial_stdout

            stderr_res += "\nExecution timed out."
            timed_out_res = True
            exit_code_res = -9
        except FileNotFoundError:
            stderr_res = "Python interpreter not found. Please ensure 'python' is in your system PATH."
            exit_code_res = -127 # Common exit code for command not found
        except Exception as e:
            stderr_res = f"Error during sandboxed execution: {str(e)}"
            exit_code_res = -1 # Generic execution error
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass
    return user_stdout_res, stderr_res, timed_out_res, exit_code_res, captured_print_metadata

# --- General Security Check ---
def general_security_check(user_code: str) -> DynamicValidationResult:
    """
    Performs basic security checks on the user's code using AST.
    """
    disallowed_imports = {"os", "sys", "subprocess", "shutil", "socket", "requests", "urllib", "ctypes", "multiprocessing", "threading"}
    disallowed_functions = {"eval", "exec", "open", "compile"} # `open` might be allowed for specific exercises with strict rules

    try:
        tree = ast.parse(user_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules_attempted = []
                if isinstance(node, ast.Import):
                    modules_attempted = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules_attempted = [node.module]

                for module_name in modules_attempted:
                    if module_name.split('.')[0] in disallowed_imports:
                        return DynamicValidationResult(False, f"Security error: Disallowed module import ('{module_name}').")

            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in disallowed_functions:
                    return DynamicValidationResult(False, f"Security error: Disallowed function call ('{node.func.id}').")

            # Check for file operations via attributes (e.g., __builtins__.open)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
                if node.attr in disallowed_functions:
                     return DynamicValidationResult(False, f"Security error: Disallowed built-in attribute access ('{node.attr}').")

    except SyntaxError:
        # This will also be caught by the execution sandbox, but good to note
        return DynamicValidationResult(False, "Syntax error in your code.")
    return DynamicValidationResult(True, "Security checks passed.")


# --- Specific Exercise Validators ---

def validate_simple_print_exercise(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None, # Usually None for simple_print
    timeout: int = 10
) -> DynamicValidationResult:
    details: Dict[str, Any] = {"validator": "simple_print"}
    start_time = time.time()

    try:
        # --- AST Checks for required structures ---
        require_for_loop = rules.get("require_for_loop", False)
        require_list_append = rules.get("require_list_append") # e.g., "compras"
        require_variables_in_print = rules.get("require_variables_in_print")

        if require_for_loop or require_list_append or require_variables_in_print:
            tree = ast.parse(user_code)

            if require_for_loop:
                if not any(isinstance(node, ast.For) for node in ast.walk(tree)):
                    return DynamicValidationResult(False, "Your solution is missing a 'for' loop, which is required for this exercise.", details=details)
                details["ast_for_loop_found"] = True

            if require_list_append:
                # Check for list assignment and subsequent append call
                list_assigned = False
                append_called = False
                for node in ast.walk(tree):
                    # Check for assignment: var = []
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == require_list_append and isinstance(node.value, ast.List):
                                list_assigned = True
                    # Check for call: var.append(...)
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                            if node.func.value.id == require_list_append and node.func.attr == 'append':
                                append_called = True

                if not (list_assigned and append_called):
                     return DynamicValidationResult(False, f"The exercise requires you to create a list named '{require_list_append}' and use the '.append()' method on it.", details=details)
                details["ast_list_append_found"] = True

        # Check for required variables in print calls (more robust check)
        require_vars_in_print = rules.get("require_variables_in_print")
        if require_vars_in_print:
            printed_variables = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                    for arg in node.args:
                        # Walk through the arguments of the print call to find all used variables
                        for sub_node in ast.walk(arg):
                            if isinstance(sub_node, ast.Name) and isinstance(sub_node.ctx, ast.Load):
                                printed_variables.add(sub_node.id)

            required_set = set(require_vars_in_print)
            if not required_set.issubset(printed_variables):
                missing = sorted(list(required_set - printed_variables))
                return DynamicValidationResult(False, f"Your print statements are missing the required variables: {', '.join(missing)}. Make sure to print the variables themselves, not their values directly.", details=details)
            details["ast_variables_in_print_check_passed"] = True

        # Check for other structural requirements like for loops or list appends
        require_for_loop = rules.get("require_for_loop", False)
        if require_for_loop and not any(isinstance(node, ast.For) for node in ast.walk(tree)):
            return DynamicValidationResult(False, "Your solution is missing a 'for' loop, which is required for this exercise.", details=details)

        require_list_append = rules.get("require_list_append")
        if require_list_append:
            # Simplified check for append method call on the named list
            append_called = any(
                isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == require_list_append and
                node.func.attr == 'append'
                for node in ast.walk(tree)
            )
            if not append_called:
                return DynamicValidationResult(False, f"The exercise requires you to use the '.append()' method on the '{require_list_append}' list.", details=details)
            details["ast_list_append_found"] = True

    except SyntaxError as e:
        return DynamicValidationResult(False, f"Syntax error in your code: {e}", details=details)

    # --- 2. If all static checks passed, run the code and check the output ---
    stdout, stderr, timed_out, exit_code_res, captured_prints_metadata = run_user_code_sandboxed(
        user_code, input_data, timeout, capture_print_types=True
    )
    details["execution_time"] = time.time() - start_time
    details["exit_code"] = exit_code_res
    details["timed_out"] = timed_out

    feedback_messages = []
    core_checks_passed = True

    if timed_out:
        return DynamicValidationResult(False, "Execution timed out.", actual_output=stdout, details=details)

    if exit_code_res != 0:
        error_message = stderr.strip() if stderr.strip() else "Runtime error occurred."
        return DynamicValidationResult(False, f"Runtime error: {error_message}", actual_output=stdout, details=details)

    if not stdout.strip(): # Check if any print occurred
        return DynamicValidationResult(False, "No output detected. Ensure your code uses print() to display results.", actual_output=stdout, details=details)

    # --- 3. Perform dynamic checks on the output ---
    # Metadata Check: Number of print calls
    expected_print_count = rules.get("expected_print_count")
    actual_print_count = len(captured_prints_metadata)
    details["actual_print_count"] = actual_print_count
    if expected_print_count is not None and actual_print_count != expected_print_count:
        core_checks_passed = False
        feedback_messages.append(f"Expected {expected_print_count} print operations, but found {actual_print_count}.")
        details["print_count_check_passed"] = False
    elif expected_print_count is not None:
        details["print_count_check_passed"] = True

    # Metadata Check: Types of printed items
    expected_types = rules.get("expected_types") # list of type names as strings
    actual_printed_types = [item['type'] for item in captured_prints_metadata]
    details["actual_printed_types"] = actual_printed_types
    if isinstance(expected_types, list):
        details["type_check_rules_exist"] = True
        if actual_print_count != len(expected_types) and expected_print_count is None:
            core_checks_passed = False
            feedback_messages.append(f"Expected {len(expected_types)} printed items based on type rules, but found {actual_print_count}.")
            details["type_check_passed"] = False
        elif actual_print_count == len(expected_types):
            type_match_current_run = True
            for i, exp_type in enumerate(expected_types):
                if actual_printed_types[i] != exp_type:
                    core_checks_passed = False
                    type_match_current_run = False
                    feedback_messages.append(f"Type mismatch for printed item #{i+1}: expected '{exp_type}', got '{actual_printed_types[i]}'.")
                    break
            details["type_check_passed"] = type_match_current_run
        elif expected_print_count is not None and actual_print_count == expected_print_count:
             core_checks_passed = False
             feedback_messages.append(f"Mismatch between expected_print_count ({expected_print_count}) and length of expected_types list ({len(expected_types)}). Review exercise rules.")
             details["type_check_passed"] = False

    # Content Check
    expected_exact_output = rules.get("expected_exact_output")
    content_matches = True
    if expected_exact_output is not None:
        details["content_check_rules_exist"] = True
        normalized_stdout = stdout.replace('\r\n', '\n')
        normalized_expected_output = expected_exact_output.replace('\r\n', '\n')
        if normalized_stdout != normalized_expected_output:
            content_matches = False
            feedback_messages.append(f"Output content differs. Expected: {repr(normalized_expected_output)}, Got: {repr(normalized_stdout)}.")
        details["content_check_passed"] = content_matches
    else:
        details["content_check_passed"] = True

    # --- 4. Final result calculation ---
    if core_checks_passed and content_matches:
        final_message = "Exercise passed!"
        if feedback_messages:
            final_message += " " + " ".join(feedback_messages)
        return DynamicValidationResult(True, final_message, actual_output=stdout, details=details)
    elif core_checks_passed and not content_matches:
        final_message = "Core requirements (like types and print counts) met, but the exact output content is different. " + " ".join(feedback_messages)
        return DynamicValidationResult(False, final_message, actual_output=stdout, details=details)
    else:
        final_message = "Validation failed. " + " ".join(feedback_messages)
        return DynamicValidationResult(False, final_message, actual_output=stdout, details=details)


def validate_saludo_personalizado(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None, # This is the name to be used for this validation run
    timeout: int = 5
) -> DynamicValidationResult:
    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res

    details: Dict[str, Any] = {}
    feedback_messages = []
    ast_checks_passed = True

    target_vars = rules.get("target_variable_names", ["nombre"])
    format_template = rules.get("output_format_template")
    requires_input_func = rules.get("requires_input_function", True)
    require_fstring_print = rules.get("require_fstring", True)

    if not format_template:
        return DynamicValidationResult(False, "Validation config error: 'output_format_template' missing.", details=details)
    if input_data is None and requires_input_func:
        return DynamicValidationResult(False, "Scenario config error: Input data (name) not provided for validation, but exercise expects input.", details=details)

    # AST Checks
    found_target_assignment = False
    assigned_var_is_from_input = False
    printed_var_name_in_fstring = None
    fstring_structure_ok_ast = False
    used_input_function_ast = False
    used_fstring_for_print_ast = False

    try:
        tree = ast.parse(user_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target_node = node.targets[0]
                if isinstance(target_node, ast.Name) and target_node.id in target_vars:
                    found_target_assignment = True
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'input':
                        assigned_var_is_from_input = True
                        used_input_function_ast = True
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'input':
                 used_input_function_ast = True # Detect input() even if not assigned to target_vars
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                if node.args and isinstance(node.args[0], ast.JoinedStr): # f-string
                    used_fstring_for_print_ast = True
                    fstring_node = node.args[0]
                    parts = format_template.split("{var}")
                    prefix = parts[0]
                    suffix = parts[1] if len(parts) > 1 else ""
                    # Simplified AST check for f-string structure
                    if len(fstring_node.values) >= 1:
                        if isinstance(fstring_node.values[0], ast.Constant) and fstring_node.values[0].value == prefix:
                            if len(fstring_node.values) >= 2 and isinstance(fstring_node.values[1], ast.FormattedValue) and isinstance(fstring_node.values[1].value, ast.Name):
                                printed_var_name_in_fstring = fstring_node.values[1].value.id
                                if suffix:
                                    if len(fstring_node.values) >= 3 and isinstance(fstring_node.values[2], ast.Constant) and fstring_node.values[2].value == suffix:
                                        fstring_structure_ok_ast = True
                                elif len(fstring_node.values) == 2 : # No suffix, prefix + var
                                    fstring_structure_ok_ast = True
                        elif not prefix and isinstance(fstring_node.values[0], ast.FormattedValue) and isinstance(fstring_node.values[0].value, ast.Name): # Case: print(f"{var}")
                            printed_var_name_in_fstring = fstring_node.values[0].value.id
                            if not suffix and len(fstring_node.values) == 1:
                                fstring_structure_ok_ast = True
    except SyntaxError:
        return DynamicValidationResult(False, "Syntax error in your code.", details=details)

    details["ast_found_target_assignment"] = found_target_assignment
    details["ast_assigned_var_is_from_input"] = assigned_var_is_from_input
    details["ast_used_input_function"] = used_input_function_ast
    details["ast_used_fstring_for_print"] = used_fstring_for_print_ast
    details["ast_fstring_structure_ok"] = fstring_structure_ok_ast
    details["ast_printed_var_name_in_fstring"] = printed_var_name_in_fstring

    if requires_input_func and not used_input_function_ast:
        ast_checks_passed = False
        feedback_messages.append("Hint: The `input()` function was expected but not found in your code.")
    if requires_input_func and found_target_assignment and not assigned_var_is_from_input :
        ast_checks_passed = False
        feedback_messages.append(f"Hint: Variable '{target_vars[0]}' should be assigned the result of `input()`.")
    if require_fstring_print and not used_fstring_for_print_ast:
        ast_checks_passed = False
        feedback_messages.append("Hint: An f-string was expected for the print statement.")
    if used_fstring_for_print_ast and not fstring_structure_ok_ast:
        ast_checks_passed = False
        feedback_messages.append(f"Hint: The f-string structure seems incorrect. Expected something like `print(f\"{format_template.replace('{var}', '{your_variable_name}')}\")`.")
    if printed_var_name_in_fstring and printed_var_name_in_fstring not in target_vars:
        ast_checks_passed = False
        feedback_messages.append(f"Hint: You printed '{printed_var_name_in_fstring}' in the f-string, but expected a variable like '{target_vars[0]}'.")


    # Behavioral Check
    stdout, stderr, timed_out, exit_code_res, captured_prints_metadata = run_user_code_sandboxed(
        user_code, input_data if requires_input_func else None, timeout, capture_print_types=True
    )
    details.update({
        "stdout": stdout, "stderr": stderr, "timed_out": timed_out, "exit_code": exit_code_res,
        "captured_prints_metadata": captured_prints_metadata
    })

    if timed_out:
        return DynamicValidationResult(False, "Execution timed out.", actual_output=stdout, details=details)
    if exit_code_res != 0:
        err_msg = stderr.strip() if stderr.strip() else "Runtime error."
        if "EOFError" in err_msg and requires_input_func and not assigned_var_is_from_input : # More specific EOF
             err_msg = "Runtime error: Code tried to read input, but `input()` might not be used correctly or assigned to the expected variable."
        return DynamicValidationResult(False, f"Runtime error: {err_msg}", actual_output=stdout, details=details)

    # Metadata checks on output
    behavioral_checks_passed = True
    if not captured_prints_metadata:
        behavioral_checks_passed = False
        feedback_messages.append("No print output was captured.")
    elif len(captured_prints_metadata) != 1:
        behavioral_checks_passed = False
        feedback_messages.append(f"Expected 1 print statement, but found {len(captured_prints_metadata)}.")
    elif captured_prints_metadata[0]['type'] != 'str':
        behavioral_checks_passed = False
        feedback_messages.append(f"Expected the printed output to be a string, but got {captured_prints_metadata[0]['type']}.")

    # Content Check (based on template)
    expected_output_str = format_template.replace("{var}", input_data if input_data is not None else "") + "\n"
    normalized_stdout = stdout.replace('\r\n', '\n')
    content_matches = (normalized_stdout == expected_output_str)
    details["content_check_passed"] = content_matches
    if not content_matches:
        feedback_messages.append(f"Output content differs. Expected: {repr(expected_output_str)}, Got: {repr(normalized_stdout)}.")

    # Final result
    if ast_checks_passed and behavioral_checks_passed and content_matches:
        return DynamicValidationResult(True, "Exercise passed! " + " ".join(feedback_messages), actual_output=stdout, details=details)
    elif ast_checks_passed and behavioral_checks_passed and not content_matches:
        msg = "Code structure and types are correct, but the exact output content is different. " + " ".join(feedback_messages)
        return DynamicValidationResult(False, msg, actual_output=stdout, details=details) # Still fail if content is off
    else: # AST or behavioral checks failed
        return DynamicValidationResult(False, "Validation failed. " + " ".join(feedback_messages), actual_output=stdout, details=details)


def validate_dynamic_output_exercise(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None, # If provided, run as a single test case
    timeout: int = 5
) -> DynamicValidationResult:
    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res

    details: Dict[str, Any] = {"test_case_results": []}
    format_template = rules.get("output_format_template", "{var}\n")
    transform_expr = rules.get("transform_for_template")
    requires_input_func_rule = rules.get("requires_input_function", False) # Does the exercise fundamentally need input()
    require_fstring_rule = rules.get("require_fstring", False) # <-- NEW

    if not transform_expr:
        return DynamicValidationResult(False, "Validation config error: 'transform_for_template' missing.", details=details)

    test_cases_values: List[str]
    if input_data is not None:
        test_cases_values = [input_data]
        details["run_mode"] = "single_case_direct_input"
    else:
        constraints = rules.get("input_constraints", {"type": "int", "min": 0, "max": 100})
        num_cases = rules.get("num_cases", 5) # Reduced default for faster validation if many exercises
        test_cases_values = generate_dynamic_test_cases(constraints, num_cases=num_cases)
        if not test_cases_values:
            return DynamicValidationResult(False, "Failed to generate dynamic test cases.", details=details)
        details["run_mode"] = "multiple_generated_cases"
        details["generated_case_count"] = len(test_cases_values)

    overall_passed = True
    accumulated_feedback = []

    # --- MODIFIED: AST checks for input() and f-string usage ---
    used_input_function_ast = False
    used_fstring_for_print_ast = False
    used_if_statement_ast = False
    require_if_statement = rules.get("require_if_statement", False)

    try:
        tree = ast.parse(user_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                used_if_statement_ast = True
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == 'input':
                    used_input_function_ast = True
                elif node.func.id == 'print' and node.args and isinstance(node.args[0], ast.JoinedStr):
                    used_fstring_for_print_ast = True
    except SyntaxError:
        return DynamicValidationResult(False, "Syntax error in your code.", details=details)

    if require_if_statement and not used_if_statement_ast:
        overall_passed = False
        accumulated_feedback.append("AST Check: An 'if' statement is required for this exercise but was not found.")
        details["ast_if_check_failed"] = True
        return DynamicValidationResult(False, " ".join(accumulated_feedback), details=details)
    if require_if_statement:
        details["ast_if_check_passed"] = True

    if requires_input_func_rule and not used_input_function_ast:
        overall_passed = False
        accumulated_feedback.append("AST Check: The `input()` function was expected but not found.")
        details["ast_input_check_failed"] = True
        return DynamicValidationResult(False, " ".join(accumulated_feedback), details=details)
    details["ast_input_check_passed"] = True

    if require_fstring_rule and not used_fstring_for_print_ast:
        # This is a strong hint, but might not be a hard failure depending on the exercise
        accumulated_feedback.append("Hint: An f-string was expected for the print statement but not found.")
        details["ast_fstring_check_passed"] = False
    else:
        details["ast_fstring_check_passed"] = True
    # --- END MODIFICATION ---


    for i, case_value_str in enumerate(test_cases_values):
        case_details: Dict[str, Any] = {"input_case": case_value_str}
        expected_var_transformed: Any
        try:
            # The 'value' in transform_expr refers to the current test case input
            # Ensure 'value' is of the correct type for eval if constraints specify type
            actual_case_value_for_eval: Any = case_value_str
            input_type = rules.get("input_constraints", {}).get("type", "str")
            if input_type == "int": actual_case_value_for_eval = int(case_value_str)
            elif input_type == "bool": actual_case_value_for_eval = bool(case_value_str) # Simplified

            expected_var_transformed = eval(transform_expr, {"value": actual_case_value_for_eval, "int": int, "str": str, "bool": bool, "float": float})
            case_details["expected_transformed_value"] = expected_var_transformed
            expected_output_for_case = format_template.replace("{var}", str(expected_var_transformed))
            case_details["expected_output_string_for_case"] = expected_output_for_case
        except Exception as e:
            overall_passed = False
            accumulated_feedback.append(f"Case #{i+1} (Input: {case_value_str}): Error in validation transform: {e}")
            case_details["error"] = f"Transform error: {e}"
            details["test_case_results"].append(case_details)
            continue # Skip to next case

        stdout, stderr, timed_out, exit_code_res, captured_prints = run_user_code_sandboxed(
            user_code, input_data=case_value_str if requires_input_func_rule else None, timeout=timeout, capture_print_types=True
        )
        case_details.update({
            "stdout": stdout, "stderr": stderr, "timed_out": timed_out, "exit_code": exit_code_res,
            "captured_prints": captured_prints
        })

        if timed_out:
            overall_passed = False
            accumulated_feedback.append(f"Case #{i+1} (Input: {case_value_str}): Execution timed out.")
            case_details["passed"] = False
            details["test_case_results"].append(case_details)
            continue
        if exit_code_res != 0:
            overall_passed = False
            accumulated_feedback.append(f"Case #{i+1} (Input: {case_value_str}): Runtime error: {stderr.strip()}")
            case_details["passed"] = False
            details["test_case_results"].append(case_details)
            continue
        if not captured_prints:
            overall_passed = False
            accumulated_feedback.append(f"Case #{i+1} (Input: {case_value_str}): No print output detected.")
            case_details["passed"] = False
            details["test_case_results"].append(case_details)
            continue

        # --- NEW: Check print count per case ---
        expected_prints_per_case = rules.get("expected_print_count_per_case")
        if expected_prints_per_case is not None and len(captured_prints) != expected_prints_per_case:
            overall_passed = False
            accumulated_feedback.append(f"Case #{i+1} (Input: {case_value_str}): Expected {expected_prints_per_case} print operations, but found {len(captured_prints)}.")
            case_details["passed"] = False
            details["test_case_results"].append(case_details)
            continue
        # --- END NEW ---

        # Metadata: Check type of printed item (assuming one primary item printed per dynamic case)
        # This might need refinement if multiple prints or complex outputs are expected per case.
        # For now, let's assume the *first* print's first arg type should match the type of expected_var_transformed.
        actual_printed_type = captured_prints[0]['type'] if captured_prints else "NoneType"
        expected_transformed_value_type = type(expected_var_transformed).__name__
        case_details["actual_printed_type"] = actual_printed_type
        case_details["expected_transformed_value_type"] = expected_transformed_value_type

        if actual_printed_type != expected_transformed_value_type:
            overall_passed = False
            accumulated_feedback.append(f"Case #{i+1} (Input: {case_value_str}): Type mismatch. Expected printed type related to '{expected_transformed_value_type}', got '{actual_printed_type}'.")
            case_details["passed"] = False
            # details["test_case_results"].append(case_details) # Appended later
            # continue # Don't necessarily stop if type is wrong but content might be right for some reason

        # Content check for this case
        normalized_stdout = stdout.replace('\r\n', '\n')
        normalized_expected_output = expected_output_for_case.replace('\r\n', '\n')
        if normalized_stdout != normalized_expected_output:
            overall_passed = False # Content mismatch is a failure for dynamic cases
            accumulated_feedback.append(f"Case #{i+1} (Input: {case_value_str}): Output content mismatch. Expected: {repr(normalized_expected_output)}, Got: {repr(normalized_stdout)}.")
            case_details["passed"] = False
        else:
            # If type was wrong but content was right, it's still a failure due to earlier overall_passed=False
             if case_details.get("passed", True): # Only mark as passed if not already failed by type
                 case_details["passed"] = True


        details["test_case_results"].append(case_details)


    final_message = " ".join(accumulated_feedback)
    if overall_passed:
        final_message = "All dynamic test cases passed!"
        # For single input mode, actual_output is relevant. For multiple, it's less so.
        return DynamicValidationResult(True, final_message, actual_output=details["test_case_results"][0]["stdout"] if input_data and details["test_case_results"] else None, details=details)
    else:
        # actual_output could be the stdout of the first failing case if desired
        first_failing_stdout = None
        for res in details["test_case_results"]:
            if not res.get("passed", True):
                first_failing_stdout = res.get("stdout")
                break
        return DynamicValidationResult(False, "One or more dynamic test cases failed. " + final_message, actual_output=first_failing_stdout, details=details)

def generate_dynamic_test_cases(constraints: Dict[str, Any], num_cases: int = 10):
    """
    Generate random test cases based on input constraints.
    Supported types: int, str
    """
    t = constraints.get("type")
    cases = []
    if t == "int":
        min_val = constraints.get("min", 0)
        max_val = constraints.get("max", 100)
        for _ in range(num_cases):
            cases.append(str(random.randint(min_val, max_val)))
    elif t == "str":
        min_length = constraints.get("min_length", 3)
        max_length = constraints.get("max_length", 10)
        charset = constraints.get("charset", "abcdefghijklmnopqrstuvwxyz")
        for _ in range(num_cases):
            length = random.randint(min_length, max_length)
            cases.append(''.join(random.choices(charset, k=length)))
    return cases


def _validate_class_structure_ast(user_code: str, class_name: str, rules: Dict[str, Any]) -> Optional[DynamicValidationResult]:
    """
    Performs static analysis on a class's structure using AST.
    Checks for inheritance, required methods, and private attributes.
    """
    details: Dict[str, Any] = {"validator": "class_structure_ast", "class_name_rule": class_name}
    try:
        tree = ast.parse(user_code)
        class_node = next((n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name), None)

        if not class_node:
            return DynamicValidationResult(False, f"Class '{class_name}' not defined in your code.", details=details)

        # Check for inheritance
        require_inheritance_from = rules.get("require_inheritance_from")
        if require_inheritance_from:
            base_names = {b.id for b in class_node.bases if isinstance(b, ast.Name)}
            if require_inheritance_from not in base_names:
                return DynamicValidationResult(False, f"Class '{class_name}' is required to inherit from '{require_inheritance_from}'.", details=details)
            details["ast_inheritance_check_passed"] = True

        # Check for required methods
        require_methods = rules.get("require_methods")
        if require_methods:
            defined_methods = {n.name for n in class_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if not set(require_methods).issubset(defined_methods):
                missing = sorted(list(set(require_methods) - defined_methods))
                return DynamicValidationResult(False, f"Class '{class_name}' is missing required method(s): {', '.join(missing)}.", details=details)
            details["ast_methods_check_passed"] = True

        # Check for encapsulation (private attributes in __init__)
        require_private_attributes = rules.get("require_private_attributes")
        if require_private_attributes:
            init_node = next((n for n in class_node.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
            if not init_node:
                return DynamicValidationResult(False, f"Class '{class_name}' is missing an '__init__' method, which is required for private attribute check.", details=details)

            private_attrs_found = set()
            for node in ast.walk(init_node):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self' and isinstance(node.ctx, ast.Store):
                    if node.attr.startswith('__') and not node.attr.endswith('__'):
                        private_attrs_found.add(node.attr)
                    elif node.attr.startswith('_') and not node.attr.startswith('__'):
                        private_attrs_found.add(node.attr)

            if not set(require_private_attributes).issubset(private_attrs_found):
                missing = sorted(list(set(require_private_attributes) - private_attrs_found))
                return DynamicValidationResult(False, f"Class '{class_name}' __init__ is missing required private attribute(s) (e.g., _attr or __attr): {', '.join(missing)}.", details=details)
            details["ast_private_attributes_check_passed"] = True

        return None
    except SyntaxError as e:
        return DynamicValidationResult(False, f"Syntax error in your code: {e}", details=details)


def _validate_function_structure_ast(user_code: str, func_name: str, rules: Dict[str, Any]) -> Optional[DynamicValidationResult]:
    """
    Performs static analysis on a function's structure using AST.
    Returns a failure result if a check fails, otherwise returns None.
    This is a helper to avoid re-running these checks for every scenario in an exam.
    """
    details: Dict[str, Any] = {"validator": "function_structure_ast", "function_name_rule": func_name}
    try:
        require_lambda = rules.get("require_lambda", False)
        require_function_call = rules.get("require_function_call")
        require_try_except = rules.get("require_try_except", False)
        disallow_function_call = rules.get("disallow_function_call")
        require_for_loop = rules.get("require_for_loop", False)
        require_if_statement = rules.get("require_if_statement", False)
        require_list_comprehension = rules.get("require_list_comprehension", False)
        require_return = rules.get("require_return_statement", False)
        # New advanced requirements
        require_dict_comprehension = rules.get("require_dict_comprehension", False)
        require_set_comprehension = rules.get("require_set_comprehension", False)
        require_yield = rules.get("require_yield", False)
        require_with_statement = rules.get("require_with_statement", False)
        require_async = rules.get("require_async", False)
        require_await = rules.get("require_await", False)
        require_decorator = rules.get("require_decorator")
        require_import = rules.get("require_import")

        tree = ast.parse(user_code)

        # Module-level checks
        if require_import:
            required_imports = [require_import] if isinstance(require_import, str) else require_import
            found_imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    found_imports.update(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    found_imports.add(node.module.split('.')[0])
            if not set(required_imports).issubset(found_imports):
                missing = sorted(list(set(required_imports) - found_imports))
                return DynamicValidationResult(False, f"Your code is missing required import(s): {', '.join(missing)}.", details=details)
            details["ast_import_check_passed"] = True

        func_node = next((n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name), None)

        if not func_node:
            # If the function itself doesn't exist in the AST, the dynamic check will provide a better error.
            return None

        # Check for empty or trivial function body
        non_docstring_body = [node for node in func_node.body if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))]
        if not non_docstring_body or (len(non_docstring_body) == 1 and isinstance(non_docstring_body[0], ast.Pass)):
            return DynamicValidationResult(False, f"Function '{func_name}' has a trivial body. It must contain implementation logic, not just 'pass'.", details=details)

        if require_for_loop and not any(isinstance(node, ast.For) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a 'for' loop, which is required.", details=details)
        if require_if_statement and not any(isinstance(node, ast.If) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing an 'if' statement, which is required.", details=details)
        if require_list_comprehension and not any(isinstance(node, ast.ListComp) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a list comprehension, which is required.", details=details)
        if require_dict_comprehension and not any(isinstance(node, ast.DictComp) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a dictionary comprehension, which is required.", details=details)
        if require_set_comprehension and not any(isinstance(node, ast.SetComp) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a set comprehension, which is required.", details=details)
        if require_yield and not any(isinstance(node, (ast.Yield, ast.YieldFrom)) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is not a generator. It's missing a 'yield' statement.", details=details)
        if require_with_statement and not any(isinstance(node, ast.With) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a 'with' statement, which is required.", details=details)
        if require_async and not isinstance(func_node, ast.AsyncFunctionDef):
            return DynamicValidationResult(False, f"Function '{func_name}' must be an async function (defined with 'async def').", details=details)
        if require_await and not any(isinstance(node, ast.Await) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing an 'await' expression, which is required.", details=details)
        if require_lambda and not any(isinstance(node, ast.Lambda) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a 'lambda' expression, which is required.", details=details)
        if require_try_except and not any(isinstance(node, ast.Try) for node in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a 'try...except' block, which is required.", details=details)
        if require_return and not any(isinstance(child, ast.Return) for child in ast.walk(func_node)):
            return DynamicValidationResult(False, f"Function '{func_name}' is missing a 'return' statement.", details=details)

        if require_decorator:
            required_decorators = [require_decorator] if isinstance(require_decorator, str) else require_decorator
            # This is a simplified check for simple decorators like @my_decorator
            found_decorators = {deco.id for deco in func_node.decorator_list if isinstance(deco, ast.Name)}
            if not set(required_decorators).issubset(found_decorators):
                missing = sorted(list(set(required_decorators) - found_decorators))
                return DynamicValidationResult(False, f"Function '{func_name}' is missing required decorator(s): {', '.join(missing)}.", details=details)
            details["ast_decorator_check_passed"] = True

        if require_function_call:
            required_calls = [require_function_call] if isinstance(require_function_call, str) else require_function_call
            found_calls = {node.func.id for node in ast.walk(func_node) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
            if not set(required_calls).issubset(found_calls):
                missing = sorted(list(set(required_calls) - found_calls))
                return DynamicValidationResult(False, f"Function '{func_name}' is missing required function call(s): {', '.join(missing)}.", details=details)

        return None # All structural checks passed
    except SyntaxError as e:
        return DynamicValidationResult(False, f"Syntax error in your code: {e}", details=details)


def validate_function_exercise(
    user_code: str,
    rules: Dict[str, Any],
    scenario_config: Dict[str, Any],
    timeout: int = 5,
    skip_ast_checks: bool = False
) -> DynamicValidationResult:
    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res # security_res already includes details

    func_name = rules.get("function_name")
    details: Dict[str, Any] = {"function_name_rule": func_name, "scenario_args": scenario_config.get("args")}

    if not func_name:
        return DynamicValidationResult(False, "Validation config error: 'function_name' missing in rules.", details=details)

    args = scenario_config.get("args", [])
    expected_return_value = scenario_config.get("expected_return_value")
    has_expected_return_check = "expected_return_value" in scenario_config
    expected_type_str = scenario_config.get("expected_return_type")
    details.update({
        "expected_return_value": expected_return_value if has_expected_return_check else "N/A",
        "expected_return_type": expected_type_str or "N/A"
    })

    code_string_lf = user_code.replace('\r\n', '\n')

    # --- AST Checks are now skippable and consolidated ---
    if not skip_ast_checks:
        ast_check_result = _validate_function_structure_ast(code_string_lf, func_name, rules)
        if ast_check_result:
            return ast_check_result
    # --- End AST Checks ---

    temp_module_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, newline='\n', encoding='utf-8') as tmp_code_file:
            tmp_code_file.write(code_string_lf)
            temp_module_path = tmp_code_file.name
            module_name = f"usermodule_{os.path.splitext(os.path.basename(temp_module_path))[0]}"


        spec = importlib.util.spec_from_file_location(module_name, temp_module_path)
        if spec is None or spec.loader is None:
            return DynamicValidationResult(False, "Failed to create module spec for user code.", details=details)

        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        details["module_loaded"] = True

        if not hasattr(user_module, func_name):
            details["function_defined_in_module"] = False
            return DynamicValidationResult(False, f"Function '{func_name}' not defined in your code.", details=details)
        details["function_defined_in_module"] = True
        actual_func = getattr(user_module, func_name)

        # --- MODIFICATION FOR ASYNC ---
        if inspect.iscoroutinefunction(actual_func):
            try:
                actual_return_value = asyncio.run(actual_func(*args))
            except RuntimeError as e:
                # Handle cases where an event loop is already running if necessary
                return DynamicValidationResult(False, f"Error running async function '{func_name}': {e}", details=details)
        else:
            actual_return_value = actual_func(*args)
        # --- END MODIFICATION ---

        actual_return_type_str = type(actual_return_value).__name__
        details["actual_return_value"] = repr(actual_return_value) # Use repr for clarity
        details["actual_return_type"] = actual_return_type_str

        if has_expected_return_check:
            if actual_return_value != expected_return_value:
                return DynamicValidationResult(False, f"Function '{func_name}' with args {args} returned {repr(actual_return_value)}, expected {repr(expected_return_value)}.", details=details)
        details["return_value_check_passed"] = True if not has_expected_return_check or actual_return_value == expected_return_value else False


        if expected_type_str:
            if actual_return_type_str != expected_type_str:
                return DynamicValidationResult(False, f"Function '{func_name}' with args {args} returned type '{actual_return_type_str}', expected type '{expected_type_str}'.", details=details)
        details["return_type_check_passed"] = True if not expected_type_str or actual_return_type_str == expected_type_str else False

        return DynamicValidationResult(True, "Function scenario passed.", actual_output=str(actual_return_value), details=details)
    except SyntaxError:
        return DynamicValidationResult(False, "Syntax error in your code.", details=details)
    except Exception as e:
        details["execution_exception_type"] = type(e).__name__
        details["execution_exception_message"] = str(e)
        return DynamicValidationResult(False, f"Error executing function '{func_name}': {type(e).__name__}: {e}", details=details)
    finally:
        if temp_module_path and os.path.exists(temp_module_path):
            try: os.unlink(temp_module_path)
            except Exception: pass


def validate_function_and_output_exercise(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None,
    timeout: int = 5
) -> DynamicValidationResult:
    details: Dict[str, Any] = {"validation_type": "function_and_output"}
    # 1. Function check
    func_rules = rules.get("function_rules", {})
    scenarios = func_rules.get("scenarios", [])
    all_func_scenarios_passed = True
    func_feedback = []
    details["function_check_results"] = []

    if not func_rules.get("function_name") or not scenarios:
         # If no function rules, it's essentially a simple_print. Or a config error.
         # For now, let's assume function_rules are expected if this validator is chosen.
         return DynamicValidationResult(False, "Configuration error: 'function_rules' (with name and scenarios) are required for 'function_and_output' validation.", details=details)


    for i, scenario_config in enumerate(scenarios):
        scenario_result = validate_function_exercise(
            user_code=user_code,
            rules=func_rules, # func_rules contains the function_name
            scenario_config=scenario_config,
            timeout=timeout
        )
        details["function_check_results"].append(scenario_result.details) # Add details from func validation
        if not scenario_result.passed:
            all_func_scenarios_passed = False
            func_feedback.append(f"Function scenario #{i+1} (args: {scenario_config.get('args')}): {scenario_result.message}")
            # No need to break, collect all function scenario failures

    if not all_func_scenarios_passed:
        return DynamicValidationResult(False, "Function validation failed. " + " | ".join(func_feedback), details=details)

    # 2. Output check (similar to simple_print, but less emphasis on types if function already checked them)
    output_checks_passed = True
    output_feedback = []
    expected_exact_output = rules.get("expected_exact_output")
    stdout_final = "" # To store the stdout from the sandboxed run for output check

    if expected_exact_output is not None: # Only run for output if expected_exact_output is defined
        details["output_check_rules_exist"] = True
        stdout_final, stderr_final, timed_out_final, exit_code_final, prints_meta_final = run_user_code_sandboxed(
            user_code, input_data, timeout, capture_print_types=True # Capture types for output part too
        )
        details["output_check_run"] = {
            "stdout": stdout_final, "stderr": stderr_final, "timed_out": timed_out_final,
            "exit_code": exit_code_final, "captured_prints": prints_meta_final
        }

        if timed_out_final:
            output_checks_passed = False
            output_feedback.append("Execution for output check timed out.")
        elif exit_code_final != 0:
            output_checks_passed = False
            output_feedback.append(f"Runtime error during output check: {stderr_final.strip()}")
        elif not prints_meta_final and not stdout_final.strip():
             output_checks_passed = False
             output_feedback.append("No output detected for the script's print part.")
        else:
            normalized_stdout = stdout_final.replace('\r\n', '\n')
            normalized_expected = expected_exact_output.replace('\r\n', '\n')
            if normalized_stdout != normalized_expected:
                output_checks_passed = False
                output_feedback.append(f"Script output content mismatch. Expected: {repr(normalized_expected)}, Got: {repr(normalized_stdout)}.")
            details["output_content_check_passed"] = output_checks_passed
    else:
        details["output_check_rules_exist"] = False # No output check rule
        output_checks_passed = True # Trivially true if no output expected

    if all_func_scenarios_passed and output_checks_passed:
        return DynamicValidationResult(True, "Function and script output are correct!", actual_output=stdout_final, details=details)
    else:
        full_feedback = []
        if not all_func_scenarios_passed: full_feedback.extend(func_feedback) # Should not happen due to early exit
        if not output_checks_passed: full_feedback.extend(output_feedback)
        return DynamicValidationResult(False, "Validation failed. " + " | ".join(full_feedback), actual_output=stdout_final, details=details)


def validate_class_exercise(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None, # Not typically used, but kept for signature consistency
    timeout: int = 10
) -> DynamicValidationResult:
    """
    Validates class-based exercises by instantiating classes, checking attributes, and calling methods.
    """
    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res

    class_name = rules.get("class_name")
    scenarios = rules.get("scenarios")
    details: Dict[str, Any] = {"validator": "class_exercise", "class_name": class_name, "scenario_results": []}

    if not class_name or not isinstance(scenarios, list):
        return DynamicValidationResult(False, "Validation config error: 'class_name' and 'scenarios' list are required.", details=details)

    # Perform static AST checks first
    static_check_result = _validate_class_structure_ast(user_code, class_name, rules)
    if static_check_result:
        return static_check_result

    # Load module for dynamic testing
    code_string_lf = user_code.replace('\r\n', '\n')
    temp_module_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, newline='\n', encoding='utf-8') as tmp_code_file:
            tmp_code_file.write(code_string_lf)
            temp_module_path = tmp_code_file.name

        module_name = f"usermodule_class_{os.path.splitext(os.path.basename(temp_module_path))[0]}"
        spec = importlib.util.spec_from_file_location(module_name, temp_module_path)
        if spec is None or spec.loader is None:
            return DynamicValidationResult(False, "Failed to create module spec for user code.", details=details)

        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        details["module_loaded"] = True

        if not hasattr(user_module, class_name):
            return DynamicValidationResult(False, f"Class '{class_name}' not found in the loaded module.", details=details)

        UserClass = getattr(user_module, class_name)

        # Run through scenarios
        instances = {} # To store created instances like {"my_car": <Car object>}
        for i, scenario in enumerate(scenarios):
            scenario_details = {"scenario_index": i, "actions": []}
            action = scenario.get("action")

            try:
                if action == "instantiate":
                    instance_name = scenario.get("instance_name", f"instance_{i}")
                    args = scenario.get("args", [])
                    instance = UserClass(*args)
                    instances[instance_name] = instance
                    scenario_details["actions"].append({"action": "instantiate", "instance_name": instance_name, "args": args, "passed": True})

                elif action == "check_attribute":
                    instance_name = scenario["instance_name"]
                    attr_name = scenario["attribute_name"]
                    expected_val = scenario["expected_value"]

                    instance = instances[instance_name]
                    actual_val = getattr(instance, attr_name)

                    if actual_val != expected_val:
                        raise AssertionError(f"Attribute '{attr_name}' on '{instance_name}' has value {repr(actual_val)}, expected {repr(expected_val)}.")
                    scenario_details["actions"].append({"action": "check_attribute", "instance_name": instance_name, "attribute": attr_name, "expected": expected_val, "actual": actual_val, "passed": True})

                elif action == "call_method":
                    instance_name = scenario["instance_name"]
                    method_name = scenario["method_name"]
                    args = scenario.get("args", [])

                    instance = instances[instance_name]
                    method_to_call = getattr(instance, method_name)

                    # --- MODIFICATION FOR ASYNC ---
                    if inspect.iscoroutinefunction(method_to_call):
                        try:
                            actual_return = asyncio.run(method_to_call(*args))
                        except RuntimeError as e:
                            raise RuntimeError(f"Error running async method '{method_name}': {e}")
                    else:
                        actual_return = method_to_call(*args)
                    # --- END MODIFICATION ---

                    if "expected_return_value" in scenario:
                        expected_return = scenario["expected_return_value"]
                        if actual_return != expected_return:
                            raise AssertionError(f"Method '{method_name}' on '{instance_name}' returned {repr(actual_return)}, expected {repr(expected_return)}.")
                    scenario_details["actions"].append({"action": "call_method", "instance_name": instance_name, "method": method_name, "args": args, "returned": repr(actual_return), "passed": True})

                else:
                    raise ValueError(f"Unknown action '{action}' in scenario #{i}.")

            except Exception as e:
                # Fail the entire validation on the first error
                return DynamicValidationResult(False, f"Scenario #{i+1} ({action}) failed: {type(e).__name__}: {e}", details=details)

            details["scenario_results"].append(scenario_details)

        return DynamicValidationResult(True, "All class validation scenarios passed.", details=details)

    except Exception as e:
        return DynamicValidationResult(False, f"An unexpected error occurred during class validation: {type(e).__name__}: {e}", details=details)
    finally:
        if temp_module_path and os.path.exists(temp_module_path):
            try: os.unlink(temp_module_path)
            except Exception: pass


def validate_exam_exercise(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None,
    timeout: int = 10,
    direct_input_run: bool = False  # This flag is now ignored. Validation always runs.
) -> DynamicValidationResult:
    # The "direct input run" logic that bypassed validation has been removed
    # to ensure consistency between running and submitting code for exams.

    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res

    function_definitions_rules = rules.get("functions")
    details: Dict[str, Any] = {"validation_type": "exam", "function_results": []}

    if not isinstance(function_definitions_rules, list) or not function_definitions_rules:
        return DynamicValidationResult(False, "Validation config error: 'functions' list is missing or empty in rules for exam.", details=details)

    overall_exam_passed = True
    passed_function_count = 0
    total_function_count = len(function_definitions_rules)
    master_feedback_list = []

    for func_idx, func_def_rules in enumerate(function_definitions_rules):
        func_name = func_def_rules.get("function_name")
        scenarios = func_def_rules.get("scenarios")
        current_func_details: Dict[str, Any] = {"function_name": func_name, "scenario_results": []}

        if not func_name or not isinstance(scenarios, list):
            master_feedback_list.append(f"Exam Config Error: Invalid definition for function #{func_idx+1} ('{func_name or 'Unknown'}').")
            overall_exam_passed = False
            details["function_results"].append(current_func_details)
            continue

        # Perform static checks ONCE per function.
        static_check_result = _validate_function_structure_ast(user_code, func_name, func_def_rules)
        if static_check_result:
            # Static check failed (e.g., syntax error, missing 'if', 'pass' body).
            # Fail this entire function with one message and move to the next.
            master_feedback_list.append(f"Function '{func_name}': FAILED - {static_check_result.message}")
            overall_exam_passed = False
            current_func_details["all_scenarios_passed"] = False
            current_func_details["static_check_failure"] = static_check_result.details
            details["function_results"].append(current_func_details)
            continue

        single_function_rules_for_validator = func_def_rules # Validator expects this structure
        current_function_all_scenarios_passed = True

        for scen_idx, scenario_config in enumerate(scenarios):
            scenario_result = validate_function_exercise(
                user_code=user_code,
                rules=single_function_rules_for_validator,
                scenario_config=scenario_config,
                timeout=timeout, # Use overall exam timeout per function scenario for simplicity
                skip_ast_checks=True # IMPORTANT: Skip checks we just did
            )
            current_func_details["scenario_results"].append(scenario_result.details) # Store detailed result of each scenario
            if not scenario_result.passed:
                # Prepend the specific scenario failure to the master list for clarity
                master_feedback_list.insert(0,
                    f"Function '{func_name}': FAILED on scenario with args {scenario_config.get('args')} - {scenario_result.message}"
                )
                overall_exam_passed = False
                current_function_all_scenarios_passed = False
                break # Stop checking scenarios for this function after the first failure.

        if current_function_all_scenarios_passed:
            master_feedback_list.append(f"Function '{func_name}': PASSED all scenarios.")
            passed_function_count += 1
            current_func_details["all_scenarios_passed"] = True
        else:
            current_func_details["all_scenarios_passed"] = False
        details["function_results"].append(current_func_details)


    if overall_exam_passed:
        final_message = f"¡Examen completado con éxito! Todas las {total_function_count} funciones pasaron."
        return DynamicValidationResult(True, final_message, details=details)
    else:
        summary_message = (
            f"Examen parcialmente completado. {passed_function_count}/{total_function_count} funciones pasaron. "
            "Revisa los detalles:\n" + "\n".join(master_feedback_list)
        )
        return DynamicValidationResult(False, summary_message, details=details)

# --- Validator Dispatcher Map ---
VALIDATOR_MAP = {
    "simple_print": validate_simple_print_exercise,
    "saludo_personalizado": validate_saludo_personalizado,
    "function_check": validate_function_exercise, # For single function validation
    "dynamic_output": validate_dynamic_output_exercise,
    "function_and_output": validate_function_and_output_exercise,
    "class_exercise": validate_class_exercise,
    "exam": validate_exam_exercise,
}
