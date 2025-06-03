import ast
import subprocess
import tempfile
import os
import signal
import importlib.util
from typing import Dict, Optional, List, Any, Tuple

# --- Result Class ---
class DynamicValidationResult:
    def __init__(self, passed: bool, message: str = "", actual_output: Optional[str] = None, details: Optional[Dict] = None):
        self.passed = passed
        self.message = message  # Error message if not passed, or success message
        self.actual_output = actual_output  # stdout from user's code if run
        self.details = details or {}

# --- Code Execution Helper ---
def run_user_code_sandboxed(
    code_string: str,
    input_data: Optional[str] = None,
    timeout: int = 5
) -> Tuple[str, str, bool, int]:
    """
    Runs user code in a sandbox.
    Returns: (stdout, stderr, timed_out, exit_code)
    """
    code_string_lf = code_string.replace('\r\n', '\n')
    stdout_res, stderr_res, timed_out_res, exit_code_res = "", "", False, -1

    # Create a temporary file with .py extension
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, newline='\n', encoding='utf-8') as tmp_file:
        tmp_file_path = tmp_file.name
        tmp_file.write(code_string_lf)

    try:
        # Use "python" which is more generic; ensure it's Python 3 in the environment.
        # Or explicitly use "python3" if that's standard for your deployment.
        process_args = ["python", tmp_file_path]
        process = subprocess.Popen(
            process_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None # For POSIX systems to kill process group
        )
        try:
            stdout_res, stderr_res = process.communicate(input=input_data, timeout=timeout)
            exit_code_res = process.returncode
        except subprocess.TimeoutExpired:
            if hasattr(os, 'killpg') and hasattr(os, 'getpgid'): # POSIX
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM) # Send SIGTERM to the process group
                    process.wait(timeout=1) # Wait a bit for graceful termination
                    if process.poll() is None: # If still running
                         os.killpg(os.getpgid(process.pid), signal.SIGKILL) # Force kill
                except ProcessLookupError: # Process might have already exited
                    pass
                except AttributeError: # os.getpgid might not be available (e.g. Windows)
                    process.kill() # Fallback for non-POSIX or if setsid wasn't used
            else: # Non-POSIX (e.g. Windows)
                process.kill()

            process.wait() # Ensure process is reaped
            stderr_res += "\nExecution timed out." # Append to any existing stderr
            timed_out_res = True
            exit_code_res = -9 # Standard for timeout (like kill -9)
            # Try to get any partial output
            if process.stdout and not stdout_res:
                try:
                    stdout_res = process.stdout.read()
                except: pass # Ignore errors reading from already closed streams
            if process.stderr and not stderr_res:
                try:
                    stderr_res = process.stderr.read()
                except: pass


    except FileNotFoundError:
        stderr_res = "Python interpreter not found. Please ensure 'python' is in your system PATH."
        exit_code_res = -127 # Common exit code for command not found
    except Exception as e:
        stderr_res = f"Error during sandboxed execution: {str(e)}"
        exit_code_res = -1 # Generic execution error
    finally:
        if os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except Exception: # Ignore errors during cleanup if file is locked or already deleted
                pass
    return stdout_res, stderr_res, timed_out_res, exit_code_res

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
    input_data: Optional[str] = None, # Usually not needed for simple print
    timeout: int = 5
) -> DynamicValidationResult:
    """
    Validates exercises that require printing an exact string.
    Rule: "expected_exact_output": "The string to be printed\n"
    """
    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res

    expected_exact_output = rules.get("expected_exact_output")
    if not isinstance(expected_exact_output, str): # Ensure it's a string
        return DynamicValidationResult(False, "Validation config error: 'expected_exact_output' rule is missing or not a string.")

    stdout, stderr, timed_out, exit_code = run_user_code_sandboxed(user_code, input_data, timeout)

    if timed_out:
        return DynamicValidationResult(False, "Execution timed out.", actual_output=stdout)
    if exit_code != 0:
        # Provide stderr if it's not empty, otherwise a generic runtime error message
        error_message = stderr.strip() if stderr.strip() else "Runtime error occurred."
        return DynamicValidationResult(False, f"Runtime error: {error_message}", actual_output=stdout)

    # For simple print, stderr should ideally be empty.
    # However, if user mistakenly uses input(), it might generate a prompt on stderr.
    # We might want to be lenient or strict based on exercise design.
    # For now, if exit_code is 0, we primarily check stdout.

    if stdout == expected_exact_output:
        return DynamicValidationResult(True, "Exercise passed!", actual_output=stdout)
    else:
        # Escape newlines for clearer comparison in messages
        expected_repr = repr(expected_exact_output)
        actual_repr = repr(stdout)
        return DynamicValidationResult(
            False,
            f"Output mismatch. Expected: {expected_repr}\nGot: {actual_repr}",
            actual_output=stdout
        )

def validate_saludo_personalizado(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None, # This is the name to be used for the scenario
    timeout: int = 5
) -> DynamicValidationResult:
    """
    Validates "Saludo Personalizado" type exercises.
    Rules:
      "target_variable_names": ["nombre", "name"] (list of allowed var names for AST check)
      "output_format_template": "¡Hola, {var}!" ({var} is placeholder for the name)
      "requires_input_function": true/false (Optional, to guide AST checks and feedback)
    """
    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res

    target_vars = rules.get("target_variable_names", ["nombre"]) # Default to "nombre"
    format_template = rules.get("output_format_template")
    requires_input_func = rules.get("requires_input_function", True) # Assume input() is expected by default

    if not format_template:
        return DynamicValidationResult(False, "Validation config error: 'output_format_template' missing.")
    if input_data is None and requires_input_func: # If input() is expected, scenario must provide data
        return DynamicValidationResult(False, "Scenario config error: Input data (name) not provided for validation, but exercise expects input.")

    # --- AST Checks (More detailed) ---
    found_target_assignment = False
    assigned_var_is_from_input = False
    printed_var_name_in_fstring = None
    fstring_structure_ok = False

    try:
        tree = ast.parse(user_code)
        for node in ast.walk(tree):
            # Check for variable assignment (e.g., nombre = "value" or nombre = input(...))
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target_node = node.targets[0]
                if isinstance(target_node, ast.Name) and target_node.id in target_vars:
                    found_target_assignment = True
                    if isinstance(node.value, ast.Call) and \
                       isinstance(node.value.func, ast.Name) and \
                       node.value.func.id == 'input':
                        assigned_var_is_from_input = True

            # Check for print(f"¡Hola, {var}!")
            elif isinstance(node, ast.Call) and \
                 isinstance(node.func, ast.Name) and node.func.id == 'print':
                if node.args and isinstance(node.args[0], ast.JoinedStr): # f-string
                    fstring_node = node.args[0]
                    # Attempt to match "¡Hola, {var}!" structure
                    # This is a simplified match, real templates can be more complex
                    # Example: format_template = "¡Hola, {var}!"
                    # We expect: Constant("¡Hola, ") + FormattedValue(Name(id='var')) + Constant("!")
                    parts = format_template.split("{var}")
                    prefix = parts[0]
                    suffix = parts[1] if len(parts) > 1 else ""

                    if len(fstring_node.values) >= 1: # At least the prefix or the variable part
                        # Check prefix
                        if isinstance(fstring_node.values[0], ast.Constant) and \
                           fstring_node.values[0].value == prefix:
                            # Check variable part
                            if len(fstring_node.values) >= 2 and \
                               isinstance(fstring_node.values[1], ast.FormattedValue) and \
                               isinstance(fstring_node.values[1].value, ast.Name):
                                printed_var_name_in_fstring = fstring_node.values[1].value.id
                                # Check suffix if present
                                if suffix:
                                    if len(fstring_node.values) >= 3 and \
                                       isinstance(fstring_node.values[2], ast.Constant) and \
                                       fstring_node.values[2].value == suffix:
                                        fstring_structure_ok = True
                                else: # No suffix
                                    if len(fstring_node.values) == 2: # Prefix + Var
                                        fstring_structure_ok = True
                            elif not prefix and isinstance(fstring_node.values[0], ast.FormattedValue) and \
                                 isinstance(fstring_node.values[0].value, ast.Name): # Case: print(f"{var}")
                                 printed_var_name_in_fstring = fstring_node.values[0].value.id
                                 if not suffix and len(fstring_node.values) == 1:
                                     fstring_structure_ok = True


    except SyntaxError:
        return DynamicValidationResult(False, "Syntax error in your code.")

    # --- Behavioral Check ---
    # Construct expected output using the provided input_data (name)
    # The placeholder in the template should be consistent, e.g., "{var}"
    expected_output = format_template.replace("{var}", input_data if input_data is not None else "") + "\n"

    # If the exercise doesn't require input(), but the user code uses it, input_data for sandbox should be None
    # to potentially trigger EOFError if not handled, or to see if it prints a default.
    # However, for this validator, input_data is the scenario's name.
    sandbox_input = input_data if requires_input_func else None

    stdout, stderr, timed_out, exit_code = run_user_code_sandboxed(user_code, sandbox_input, timeout)

    if timed_out:
        return DynamicValidationResult(False, "Execution timed out.", actual_output=stdout)

    if exit_code != 0:
        error_message = stderr.strip() if stderr.strip() else "Runtime error occurred."
        # If input was expected but not provided by user code (EOFError)
        if "EOFError" in error_message and requires_input_func and not assigned_var_is_from_input:
            error_message = "Runtime error: Your code tried to read input, but it might not be doing so correctly or the exercise scenario didn't provide it."
        return DynamicValidationResult(False, f"Runtime error: {error_message}", actual_output=stdout)

    if stdout == expected_output:
        feedback_msgs = []
        if requires_input_func and not assigned_var_is_from_input:
            feedback_msgs.append("Hint: Make sure you are using the `input()` function to get the name.")
        if not found_target_assignment:
            feedback_msgs.append(f"Hint: Consider assigning the input to a variable (e.g., one of {target_vars}).")
        if not fstring_structure_ok or not printed_var_name_in_fstring:
            feedback_msgs.append("Hint: Ensure you are using an f-string for printing, like `print(f\"" + format_template.replace("{var}", "{your_variable_name}") + "\")`.")
        elif printed_var_name_in_fstring not in target_vars and found_target_assignment:
             feedback_msgs.append(f"Hint: You assigned to a variable like '{', '.join(target_vars)}' but printed a different variable '{printed_var_name_in_fstring}' in the f-string.")

        if feedback_msgs:
            return DynamicValidationResult(True, "Exercise passed! " + " ".join(feedback_msgs), actual_output=stdout)
        return DynamicValidationResult(True, "Exercise passed!", actual_output=stdout)
    else:
        msg = f"Output mismatch. Expected something like: '{expected_output.strip()}'\nGot: '{stdout.strip()}'"
        if requires_input_func and not assigned_var_is_from_input:
             msg += "\nHint: Did you use the `input()` function to get the name?"
        return DynamicValidationResult(False, msg, actual_output=stdout)


def validate_function_exercise(
    user_code: str,
    rules: Dict[str, Any], # Contains "function_name"
    scenario_config: Dict[str, Any], # Contains "args", "expected_return_value", "expected_return_type"
    timeout: int = 5 # Overall timeout for this validation step
) -> DynamicValidationResult:
    """
    Validates exercises where user defines a function.
    Rules: "function_name": "name_of_function_to_test"
    Scenario_config:
      "args": [arg1, arg2]
      "expected_return_value": value (optional, checked if present)
      "expected_return_type": "str" (optional, type name as string, checked if present)
    """
    # Security check on the entire user_code string first
    security_res = general_security_check(user_code)
    if not security_res.passed:
        return security_res

    func_name = rules.get("function_name")
    if not func_name:
        return DynamicValidationResult(False, "Validation config error: 'function_name' missing in rules.")

    args = scenario_config.get("args", [])
    expected_return_value = scenario_config.get("expected_return_value")
    has_expected_return_check = "expected_return_value" in scenario_config # Explicitly check key presence
    expected_type_str = scenario_config.get("expected_return_type")

    # Dynamically import and run the function.
    # This execution happens within the main service process, so it's not sandboxed like
    # run_user_code_sandboxed. The general_security_check is crucial here.
    # For true sandboxing of function execution, one would need to use run_user_code_sandboxed
    # with a wrapper script that calls the function and prints its result, then parse that.
    # However, for direct type/value checking, dynamic import is more straightforward if security is managed.

    code_string_lf = user_code.replace('\r\n', '\n')
    temp_module_path = None
    try:
        # Create a temporary file to write the code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, newline='\n', encoding='utf-8') as tmp_code_file:
            tmp_code_file.write(code_string_lf) # Write the user's function definition
            temp_module_path = tmp_code_file.name
            # Use a unique module name to avoid conflicts if run multiple times
            module_name = f"usermodule_{os.path.splitext(os.path.basename(temp_module_path))[0]}"


        spec = importlib.util.spec_from_file_location(module_name, temp_module_path)
        if spec is None or spec.loader is None: # Should not happen if file is created
            return DynamicValidationResult(False, "Failed to create module spec for user code.")

        user_module = importlib.util.module_from_spec(spec)
        # Crucial: Execute the module to make definitions available
        spec.loader.exec_module(user_module)

        if not hasattr(user_module, func_name):
            return DynamicValidationResult(False, f"Function '{func_name}' not defined in your code.")

        actual_func = getattr(user_module, func_name)

        # Timeout for the function call itself is hard to implement here without
        # complex mechanisms (threading/multiprocessing). The request timeout is the main guard.
        actual_return_value = actual_func(*args) # Call the user's function
        actual_return_type_str = type(actual_return_value).__name__

        # Check 1: Return value
        if has_expected_return_check:
            if actual_return_value != expected_return_value:
                return DynamicValidationResult(False, f"Function '{func_name}' with args {args} returned '{actual_return_value}', expected '{expected_return_value}'.")

        # Check 2: Return type
        if expected_type_str:
            if actual_return_type_str != expected_type_str:
                return DynamicValidationResult(False, f"Function '{func_name}' with args {args} returned type '{actual_return_type_str}', expected type '{expected_type_str}'.")

        # If all checks passed for this scenario
        return DynamicValidationResult(True, "Function scenario passed.", actual_output=str(actual_return_value))

    except SyntaxError:
        return DynamicValidationResult(False, "Syntax error in your code.")
    except Exception as e:
        # This catches errors from the user's code during module execution or function call
        return DynamicValidationResult(False, f"Error executing function '{func_name}': {type(e).__name__}: {e}")
    finally:
        # Clean up the temporary module file
        if temp_module_path and os.path.exists(temp_module_path):
            try:
                os.unlink(temp_module_path)
            except Exception: # Silently ignore cleanup errors
                pass

# --- Validator Dispatcher Map ---
VALIDATOR_MAP = {
    "simple_print": validate_simple_print_exercise,
    "saludo_personalizado": validate_saludo_personalizado,
    "function_check": validate_function_exercise,
    # Add more mappings as you define validation_types and implement new validators
    # e.g., "loop_check", "class_method_check", etc.
}
