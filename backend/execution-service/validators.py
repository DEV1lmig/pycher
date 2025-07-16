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
import logging
from typing import Dict, Optional, List, Any, Tuple, Set

# Set up logger for this module
logger = logging.getLogger(__name__)

# --- Result Class ---
class DynamicValidationResult:
    def __init__(self, passed: bool, message: str = "", actual_output: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.passed = passed
        self.message = message
        self.actual_output = actual_output
        self.details = details or {}

# --- Code Execution Helper ---

PRINT_INTERCEPT_PREAMBLE = """
import builtins as _builtins
import json as _json
import sys as _sys

_original_print = _builtins.print
_captured_prints = []

def _custom_print(*args, **kwargs):
    global _captured_prints
    if args:
        _captured_prints.append({"type": type(args[0]).__name__})
    _original_print(*args, **kwargs)

_builtins.print = _custom_print
"""

PRINT_INTERCEPT_EPILOGUE_MARKER = "###PRINT_METADATA_SEPARATOR_D7A3F###"
PRINT_INTERCEPT_EPILOGUE = f"""
_sys.stdout.write("{PRINT_INTERCEPT_EPILOGUE_MARKER}\\n")
_sys.stdout.write(_json.dumps(_captured_prints) + "\\n")
_sys.stdout.flush()
"""

def run_user_code_sandboxed(
    code_string: str,
    input_data: Optional[str] = None,
    timeout: int = 5,
    capture_print_types: bool = False
) -> Tuple[str, str, bool, int, List[Dict[str, str]]]:
    """
    Runs user code in a sandbox, optionally capturing print() argument types.
    Returns: (user_stdout, stderr, timed_out, exit_code, captured_print_metadata)
    """
    code_to_run = code_string.replace('\r\n', '\n')
    if capture_print_types:
        code_to_run = PRINT_INTERCEPT_PREAMBLE + code_to_run + PRINT_INTERCEPT_EPILOGUE

    user_stdout, stderr, timed_out, exit_code = "", "", False, -1
    captured_metadata = []
    tmp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, newline='\n', encoding='utf-8') as tmp_file:
            tmp_file_path = tmp_file.name
            tmp_file.write(code_to_run)

        process_args = ["python", tmp_file_path]
        process = subprocess.Popen(
            process_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        try:
            raw_stdout, raw_stderr = process.communicate(input=input_data, timeout=timeout)
            exit_code = process.returncode

            if capture_print_types:
                parts = raw_stdout.split(f"{PRINT_INTERCEPT_EPILOGUE_MARKER}\n", 1)
                user_stdout = parts[0]
                if len(parts) > 1:
                    try:
                        json_data_str = parts[1].strip()
                        if json_data_str:
                            captured_metadata = json.loads(json_data_str)
                    except json.JSONDecodeError as e:
                        stderr += f"\n[Validator Info] Failed to parse print metadata: {e}."
                else:
                    stderr += "\n[Validator Info] Print metadata marker not found in output."
            else:
                user_stdout = raw_stdout
            stderr += raw_stderr
        except subprocess.TimeoutExpired:
            if hasattr(os, 'killpg') and hasattr(os, 'getpgid'):
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except ProcessLookupError: pass
            else: process.kill()
            process.wait()
            user_stdout = process.stdout.read() if process.stdout else ""
            stderr += "\nExecution timed out."
            timed_out = True
            exit_code = -9
        except Exception as e:
            stderr += f"\nError during sandboxed execution: {e}"
            exit_code = -1
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try: os.unlink(tmp_file_path)
            except Exception: pass
    return user_stdout, stderr, timed_out, exit_code, captured_metadata
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
# --- Centralized Code Analyzer ---
class CodeAnalyzer:
    """Parses code once and provides methods to check for various structural requirements."""
    def __init__(self, user_code: str):
        self.user_code = user_code
        self.tree: Optional[ast.AST] = None
        self.analysis: Dict[str, Any] = {}
        self.syntax_error: Optional[str] = None
        self.variables_defined: Set[str] = set()
        self.variables_used_in_prints: Set[str] = set()
        try:
            self.tree = ast.parse(self.user_code)
            self.analyze()
        except SyntaxError as e:
            self.syntax_error = str(e)

    def get_class_node(self, class_name: str) -> Optional[ast.ClassDef]:
        if not self.tree: return None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def check_method_or_property_exists(self, class_node: ast.ClassDef, name: str, is_property: bool = False) -> bool:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == name:
                if not is_property:
                    return True # It's a method
                # Check if it has the @property decorator
                if any(isinstance(d, ast.Name) and d.id == 'property' for d in item.decorator_list):
                    return True
        return False

    def check_is_dataclass(self, class_node: ast.ClassDef, frozen: Optional[bool] = None) -> bool:
        for decorator in class_node.decorator_list:
            # Simple decorator: @dataclass
            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                if frozen is None: return True # Just check for @dataclass
                if frozen is False: return True # @dataclass is not frozen by default

            # Decorator with arguments: @dataclass(frozen=True)
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == 'dataclass':
                if frozen is None: return True # It's a dataclass, regardless of args

                for kw in decorator.keywords:
                    if kw.arg == 'frozen':
                        # Check for `frozen=True` or `frozen=False`
                        if isinstance(kw.value, ast.Constant) and kw.value.value is frozen:
                            return True
                # If frozen argument is not present, it defaults to False
                if frozen is False:
                    return True
        return False

    def is_function_decorated(self, function_name: str, decorator_name: str) -> bool:
        """Verifica si una función específica está decorada por un decorador específico."""
        func_node = self.analysis.get("defined_functions", {}).get(function_name)
        if not func_node:
            return False

        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == decorator_name:
                return True
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == decorator_name:
                return True
        return False

    def is_generator(self, function_name: str) -> bool:
        """Verifica si una función es un generador buscando la palabra clave 'yield'."""
        func_node = self.analysis.get("defined_functions", {}).get(function_name)
        if not func_node:
            return False

        for node in ast.walk(func_node):
            if isinstance(node, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def analyze(self):
        if not self.tree: return
        logger.info("Starting code analysis...")
        self.analysis = {
            "imports": set(), "disallowed_imports": set(),
            "function_calls": set(), "disallowed_calls": set(),
            "has_for_loop": False, "has_if": False, "has_list_comp": False,
            "has_dict_comp": False, "has_set_comp": False, "has_lambda": False,
            "has_try_except": False, "has_yield": False, "has_with": False,
            "has_await": False, "defined_functions": {}, "defined_classes": {},
            "print_calls": []
        }

        # Security and disallowed items tracking
        disallowed_imports = {"os", "sys", "subprocess", "shutil", "socket", "requests", "urllib", "ctypes", "multiprocessing", "threading"}
        disallowed_functions = {"eval", "exec", "open", "compile"}

        for node in ast.walk(self.tree):
            # Track imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules_attempted = []
                if isinstance(node, ast.Import):
                    modules_attempted = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules_attempted = [node.module]

                for module_name in modules_attempted:
                    self.analysis["imports"].add(module_name)
                    if module_name.split('.')[0] in disallowed_imports:
                        self.analysis["disallowed_imports"].add(module_name)

            # Track function calls
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                self.analysis["function_calls"].add(func_name)
                if func_name in disallowed_functions:
                    self.analysis["disallowed_calls"].add(func_name)

                # SPECIAL HANDLING FOR PRINT CALLS - This was missing!
                if func_name == 'print':
                    print_call = {"args": [], "is_fstring": False}
                    logger.debug(f"Found print call with {len(node.args)} arguments")

                    # Check if any argument is an f-string (ast.JoinedStr)
                    is_fstring_print = any(isinstance(arg, ast.JoinedStr) for arg in node.args)

                    if is_fstring_print:
                        print_call["is_fstring"] = True
                        logger.info("Found f-string in print call")
                        for arg in node.args:
                            if isinstance(arg, ast.JoinedStr):
                                logger.debug(f"Analyzing f-string with {len(arg.values)} parts")
                                for i, value_node in enumerate(arg.values):
                                    logger.debug(f"  Part {i}: {type(value_node).__name__}")
                                    if isinstance(value_node, ast.FormattedValue):
                                        logger.debug(f"    FormattedValue: {ast.dump(value_node)}")
                                        if isinstance(value_node.value, ast.Name):
                                            var_name = value_node.value.id
                                            self.variables_used_in_prints.add(var_name)
                                            print_call["args"].append({"type": "variable", "variable_name": var_name})
                                            logger.info(f"    -> Added variable: {var_name}")
                                        else:
                                            logger.debug(f"    FormattedValue contains non-Name: {type(value_node.value)}")
                                    elif isinstance(value_node, ast.Constant):
                                        logger.debug(f"    -> Constant string: {repr(value_node.value)}")
                                    else:
                                        logger.debug(f"    F-string part is not FormattedValue or Constant: {type(value_node)}")
                    else:
                        logger.debug("Regular print call (not f-string)")
                        for arg in node.args:
                            if isinstance(arg, ast.Name):
                                var_name = arg.id
                                self.variables_used_in_prints.add(var_name)
                                print_call["args"].append({"type": "variable", "variable_name": var_name})
                                logger.debug(f"Found variable in regular print: {var_name}")

                    self.analysis["print_calls"].append(print_call)

            # Track variable assignments
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variables_defined.add(target.id)
                        logger.debug(f"Found variable definition: {target.id}")

            # Track control structures
            elif isinstance(node, ast.For):
                self.analysis["has_for_loop"] = True
            elif isinstance(node, ast.If):
                self.analysis["has_if"] = True
            elif isinstance(node, ast.ListComp):
                self.analysis["has_list_comp"] = True
            elif isinstance(node, ast.DictComp):
                self.analysis["has_dict_comp"] = True
            elif isinstance(node, ast.SetComp):
                self.analysis["has_set_comp"] = True
            elif isinstance(node, ast.Lambda):
                self.analysis["has_lambda"] = True
            elif isinstance(node, ast.Try):
                self.analysis["has_try_except"] = True
            elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                self.analysis["has_yield"] = True
            elif isinstance(node, ast.With):
                self.analysis["has_with"] = True
            elif isinstance(node, ast.Await):
                self.analysis["has_await"] = True

            # Track function and class definitions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.analysis["defined_functions"][node.name] = node
            elif isinstance(node, ast.ClassDef):
                self.analysis["defined_classes"][node.name] = node

        logger.info(f"Analysis complete. Variables defined: {self.variables_defined}")
        logger.info(f"Variables used in prints: {self.variables_used_in_prints}")
        logger.info(f"Print calls: {self.analysis['print_calls']}")

    def check_static_requirements(self, rules: Dict[str, Any], scope_node: Optional[ast.AST] = None) -> List[str]:
        if self.syntax_error: return [f"Syntax error: {self.syntax_error}"]
        if not self.analysis: self.analyze()

        failures = []
        scope = scope_node or self.tree
        if not scope: return failures

        # Security checks
        if self.analysis["disallowed_imports"]: failures.append(f"Security error: Disallowed module import(s): {', '.join(self.analysis['disallowed_imports'])}.")
        if self.analysis["disallowed_calls"]: failures.append(f"Security error: Disallowed function call(s): {', '.join(self.analysis['disallowed_calls'])}.")
        if failures: return failures # Stop if security checks fail

        # Structural checks
        if rules.get("require_for_loop") and not any(isinstance(n, ast.For) for n in ast.walk(scope)): failures.append("A 'for' loop is required.")
        if rules.get("require_if_statement") and not any(isinstance(n, ast.If) for n in ast.walk(scope)): failures.append("An 'if' statement is required.")
        if rules.get("require_list_comprehension") and not any(isinstance(n, ast.ListComp) for n in ast.walk(scope)): failures.append("A list comprehension is required.")
        if rules.get("require_dict_comprehension") and not any(isinstance(n, ast.DictComp) for n in ast.walk(scope)): failures.append("A dictionary comprehension is required.")
        if rules.get("require_set_comprehension") and not any(isinstance(n, ast.SetComp) for n in ast.walk(scope)): failures.append("A set comprehension is required.")
        if rules.get("require_lambda") and not any(isinstance(n, ast.Lambda) for n in ast.walk(scope)): failures.append("A 'lambda' expression is required.")
        if rules.get("require_try_except") and not any(isinstance(n, ast.Try) for n in ast.walk(scope)): failures.append("A 'try...except' block is required.")
        if rules.get("require_yield") and not any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(scope)): failures.append("A 'yield' statement is required (must be a generator).")
        if rules.get("require_with_statement") and not any(isinstance(n, ast.With) for n in ast.walk(scope)): failures.append("A 'with' statement is required.")
        if rules.get("require_return_statement") and not any(isinstance(n, ast.Return) for n in ast.walk(scope)): failures.append("A 'return' statement is required.")

        # Function/Class specific checks
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if rules.get("require_async") and not isinstance(scope, ast.AsyncFunctionDef): failures.append(f"Function '{scope.name}' must be async ('async def').")
            if rules.get("require_await") and not any(isinstance(n, ast.Await) for n in ast.walk(scope)): failures.append("An 'await' expression is required.")

        return failures

    def check_variable_definitions(self, required_variables: List[str]) -> List[str]:
        """Checks that the given variables are defined somewhere in the code."""
        if self.syntax_error: return []
        missing_definitions = set(required_variables) - self.variables_defined
        if missing_definitions:
            return [f"Missing required variable definitions: {', '.join(sorted(list(missing_definitions)))}."]
        return []

    def check_variables_in_print(self, required_variables: List[str]) -> List[str]:
        """Checks that the given variables are defined and then used within a print() call."""
        if self.syntax_error: return []

        # First, ensure variables are defined before checking usage.
        def_errors = self.check_variable_definitions(required_variables)
        if def_errors:
            return def_errors

        missing_usage = set(required_variables) - self.variables_used_in_prints
        if missing_usage:
            return [f"Required variables not used in any print statement: {', '.join(sorted(list(missing_usage)))}."]
        return []

# --- Specific Exercise Validators ---

def validate_saludo_personalizado(
    user_code: str,
    rules: Dict[str, Any],
    input_data: Optional[str] = None,
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

    format_template = rules.get("output_format_template")
    requires_input_func = rules.get("requires_input_function", True)

    if not format_template:
        return DynamicValidationResult(False, "Validation config error: 'output_format_template' missing.")
    if requires_input_func and input_data is None:
        return DynamicValidationResult(False, "Scenario config error: Input data not provided for validation.")

    # --- Behavioral Check ---
    expected_output = format_template.replace("{var}", input_data or "")

    # --- FIX: Prepare input with a newline to simulate the user pressing Enter ---
    # This is crucial for the `input()` function to work correctly in the sandbox.
    sandbox_input = f"{input_data}\n" if requires_input_func and input_data is not None else None

    # Pass the prepared input to the sandboxed execution
    stdout, stderr, timed_out, exit_code, _ = run_user_code_sandboxed(
        user_code,
        input_data=sandbox_input, # Use the variable with the newline
        timeout=timeout
    )

    if timed_out:
        return DynamicValidationResult(False, "Execution timed out.", actual_output=stdout)
    if exit_code != 0:
        return DynamicValidationResult(False, f"Runtime error: {stderr.strip()}", actual_output=stdout)

    # Normalize both outputs by stripping whitespace to handle newlines from print()
    normalized_stdout = stdout.strip()
    normalized_expected = expected_output.strip()

    if normalized_stdout == normalized_expected:
        return DynamicValidationResult(True, "Exercise passed!", actual_output=stdout)
    else:
        msg = f"Output mismatch. Expected: '{normalized_expected}' but got: '{normalized_stdout}'"
        return DynamicValidationResult(False, msg, actual_output=stdout)


def validate_simple_print_exercise(user_code: str, rules: Dict[str, Any], **kwargs) -> DynamicValidationResult:
    logger.info(f"Starting simple_print validation. Rules: {rules}")
    analyzer = CodeAnalyzer(user_code)

    # 1. Prioritize syntax error reporting
    if analyzer.syntax_error:
        return DynamicValidationResult(False, f"Your code has a syntax error: {analyzer.syntax_error}")

    # Check for variable USAGE IN PRINT - FIX THE KEY NAME
    vars_in_print = rules.get("required_variables_in_print")  # Changed from "require_variables_in_print"
    if vars_in_print:
        logger.info(f"Checking for required variables in print: {vars_in_print}")
        logger.info(f"Variables actually found in prints: {analyzer.variables_used_in_prints}")
        logger.info(f"Print calls analysis: {analyzer.analysis.get('print_calls', [])}")

        print_usage_errors = analyzer.check_variables_in_print(vars_in_print)
        if print_usage_errors:
            logger.warning(f"Variable usage check failed: {print_usage_errors}")
            feedback_key = "wrong_variable"  # Changed to match the exercise config
            default_msg = "You defined the correct variables, but didn't use them in your print statement."
            message = rules.get("custom_feedback", {}).get(feedback_key, default_msg)
            return DynamicValidationResult(False, message)
        else:
            logger.info("Variable usage check passed")

    # Check for f-string requirement
    if rules.get("require_fstring"):
        if not analyzer.analysis.get("print_calls") or not analyzer.analysis["print_calls"][0].get("is_fstring"):
            feedback_key = "not_fstring"
            message = rules.get("custom_feedback", {}).get(feedback_key, "This exercise requires using an f-string.")
            return DynamicValidationResult(False, message) # Immediate failure

    # 3. If all static checks passed, THEN execute the code and check the output.
    stdout, stderr, timed_out, exit_code, captured_prints = run_user_code_sandboxed(
        user_code, input_data=kwargs.get("input_data"), timeout=kwargs.get("timeout", 5), capture_print_types=True
    )
    if timed_out: return DynamicValidationResult(False, "Execution timed out.", actual_output=stdout)
    if exit_code != 0: return DynamicValidationResult(False, f"Runtime error: {stderr.strip()}", actual_output=stdout)
    if not stdout.strip(): return DynamicValidationResult(False, "No output detected. Use print() to display results.", actual_output=stdout)

    # 4. Check runtime conditions like output content and print count.
    feedback = []
    passed = True

    # Check print count
    expected_print_count = rules.get("expected_print_count")
    if expected_print_count is not None and len(captured_prints) != expected_print_count:
        passed = False
        feedback_key = "wrong_print_count"
        message = rules.get("custom_feedback", {}).get(feedback_key, f"Expected {expected_print_count} print operations, found {len(captured_prints)}.")
        feedback.append(message)

    # Check exact output content
    expected_output = rules.get("expected_exact_output")
    if expected_output is not None:
        normalized_stdout = stdout.replace('\r\n', '\n')
        normalized_expected = expected_output.replace('\r\n', '\n')
        if normalized_stdout != normalized_expected:
            passed = False
            feedback_key = "wrong_output"
            message = rules.get("custom_feedback", {}).get(feedback_key, f"Output content differs. Expected: {repr(normalized_expected)}, Got: {repr(normalized_stdout)}.")
            feedback.append(message)

    if not passed:
        return DynamicValidationResult(False, " ".join(feedback), actual_output=stdout)

    return DynamicValidationResult(True, "Exercise passed!", actual_output=stdout)


def validate_dynamic_output_exercise(user_code: str, rules: Dict[str, Any], **kwargs) -> DynamicValidationResult:
    analyzer = CodeAnalyzer(user_code)

    # Prioritize syntax error reporting
    if analyzer.syntax_error:
        return DynamicValidationResult(False, f"Your code has a syntax error: {analyzer.syntax_error}")

    # Check for variable definitions if required
    if "require_variable_definitions" in rules:
        def_errors = analyzer.check_variable_definitions(rules["require_variable_definitions"])
        if def_errors:
            return DynamicValidationResult(False, "Variable definition error: " + "; ".join(def_errors))

    # Check for variable usage in print statements if required
    if "require_variables_in_print" in rules:
        print_errors = analyzer.check_variables_in_print(rules["require_variables_in_print"])
        if print_errors:
            return DynamicValidationResult(False, "Variable usage error: " + "; ".join(print_errors))

    static_failures = analyzer.check_static_requirements(rules)
    if static_failures:
        return DynamicValidationResult(False, "Static analysis failed: " + " ".join(static_failures))

    # --- START: FIX for test case handling ---
    test_cases = kwargs.get("input_data")

    # Ensure test_cases is always a list. If a single string is passed, wrap it in a list.
    if isinstance(test_cases, str):
        test_cases = [test_cases]
    elif test_cases is None:
        # Generate test cases if not provided
        constraints = rules.get("input_constraints", {"type": "int", "min": 0, "max": 100})
        num_cases = rules.get("num_cases", 5)
        test_cases = generate_dynamic_test_cases(constraints, num_cases)
    # --- END: FIX for test case handling ---

    all_cases_passed = True
    feedback = []
    last_stdout = "" # Store the stdout of the last run case

    for i, case_input in enumerate(test_cases):
        try:
            transform_expr = rules.get("transform_for_template", "value")
            input_type = rules.get("input_constraints", {}).get("type", "str")
            actual_case_value = {"int": int, "str": str, "string": str, "bool": bool, "float": float}[input_type](case_input)
            expected_transformed = eval(transform_expr, {"value": actual_case_value})
            expected_output = rules.get("output_format_template", "{var}\n").replace("{var}", str(expected_transformed))
        except Exception as e:
            return DynamicValidationResult(False, f"Validation config error on case '{case_input}': {e}")

        # --- START: FIX for input handling ---
        # The input() function reads a line, so we must append a newline
        # character to simulate the user pressing Enter. This is the crucial step.
        input_with_newline = f"{case_input}\n"
        stdout, stderr, timed_out, exit_code, _ = run_user_code_sandboxed(user_code, input_with_newline, kwargs.get("timeout", 5))
        # --- END: FIX for input handling ---

        last_stdout = stdout # Always update with the latest output

        # --- START: IMPROVED VALIDATION LOGIC ---
        # Normalize both outputs by replacing Windows newlines and stripping whitespace.
        # This makes the validation robust against trailing newlines from print()
        # and other minor whitespace differences.
        normalized_stdout = stdout.replace('\r\n', '\n').strip()
        normalized_expected = expected_output.replace('\r\n', '\n').strip()

        if timed_out or exit_code != 0 or normalized_stdout != normalized_expected:
            all_cases_passed = False
            # Provide clearer feedback using the normalized values.
            feedback.append(f"Failed on input '{case_input}'. Expected: '{normalized_expected}', Got: '{normalized_stdout}'.")
            break # Stop on first failure
        # --- END: IMPROVED VALIDATION LOGIC ---

    if all_cases_passed:
        # --- FIX: Pass the actual_output on success ---
        return DynamicValidationResult(True, "All dynamic test cases passed!", actual_output=last_stdout)
    else:
        # --- FIX: Pass the actual_output on failure ---
        return DynamicValidationResult(False, "One or more dynamic test cases failed. " + " ".join(feedback), actual_output=last_stdout)

def generate_dynamic_test_cases(constraints: Dict[str, Any], num_cases: int) -> List[str]:
    t = constraints.get("type", "int")
    if t == "int":
        return [str(random.randint(constraints.get("min", 0), constraints.get("max", 100))) for _ in range(num_cases)]
    elif t in ["str", "string"]:
        charset = constraints.get("charset", "abcdefghijklmnopqrstuvwxyz")
        return [''.join(random.choices(charset, k=random.randint(constraints.get("min_length", 3), constraints.get("max_length", 10)))) for _ in range(num_cases)]
    return []

def validate_function_exercise(user_code: str, rules: Dict[str, Any], scenario_config: Dict[str, Any], **kwargs) -> DynamicValidationResult:
    func_name = rules.get("function_name")
    if not func_name: return DynamicValidationResult(False, "Config error: 'function_name' missing.")

    analyzer = CodeAnalyzer(user_code)
    func_node = analyzer.analysis.get("defined_functions", {}).get(func_name)
    static_failures = analyzer.check_static_requirements(rules, scope_node=func_node)
    if static_failures:
        return DynamicValidationResult(False, f"Function '{func_name}' static analysis failed: " + " ".join(static_failures))

    temp_module_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding='utf-8') as tmp_file:
            temp_module_path = tmp_file.name
            tmp_file.write(user_code)

        spec = importlib.util.spec_from_file_location(f"usermodule_{os.path.basename(temp_module_path)}", temp_module_path)
        if not spec or not spec.loader: return DynamicValidationResult(False, "Failed to create module spec.")

        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)

        if not hasattr(user_module, func_name): return DynamicValidationResult(False, f"Function '{func_name}' not defined.")

        actual_func = getattr(user_module, func_name)
        args = scenario_config.get("args", [])

        actual_return = asyncio.run(actual_func(*args)) if inspect.iscoroutinefunction(actual_func) else actual_func(*args)

        if "expected_return_value" in scenario_config:
            expected_return = scenario_config["expected_return_value"]
            if actual_return != expected_return:
                return DynamicValidationResult(False, f"Returned {repr(actual_return)}, expected {repr(expected_return)}.")

        if "expected_return_type" in scenario_config:
            expected_type = scenario_config["expected_return_type"]
            if type(actual_return).__name__ != expected_type:
                return DynamicValidationResult(False, f"Returned type '{type(actual_return).__name__}', expected '{expected_type}'.")

        return DynamicValidationResult(True, "Function scenario passed.")
    except Exception as e:
        return DynamicValidationResult(False, f"Error executing function '{func_name}': {type(e).__name__}: {e}")
    finally:
        if temp_module_path and os.path.exists(temp_module_path):
            try: os.unlink(temp_module_path)
            except Exception: pass

def _validate_class_unit(user_code: str, class_name: str, scenarios: List[Dict], analyzer: CodeAnalyzer) -> DynamicValidationResult:
    """Valida una clase basada en escenarios de configuración y validación."""
    if class_name not in analyzer.analysis["defined_classes"]:
        return DynamicValidationResult(False, f"Clase '{class_name}' no está definida.")

    temp_module_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding='utf-8') as tmp_file:
            temp_module_path = tmp_file.name
            tmp_file.write(user_code)

        spec = importlib.util.spec_from_file_location(f"usermodule_{os.path.basename(temp_module_path)}", temp_module_path)
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        UserClass = getattr(user_module, class_name)

        for i, scenario in enumerate(scenarios):
            setup_code = scenario.get("setup_code", "")
            validation_code = scenario.get("validation_code", "")
            expected = scenario.get("expected_return_value")
            try:
                exec_globals = {"__builtins__": __builtins__, class_name: UserClass}
                exec(setup_code, exec_globals)
                actual = eval(validation_code, exec_globals)
                if actual != expected:
                    return DynamicValidationResult(False, f"Escenario {i+1} falló. Se esperaba '{expected}', pero se obtuvo '{actual}'.")
            except Exception as e:
                return DynamicValidationResult(False, f"Escenario {i+1} produjo un error: {type(e).__name__}: {e}")
    except Exception as e:
        return DynamicValidationResult(False, f"Error al cargar la clase: {e}")
    finally:
        if temp_module_path and os.path.exists(temp_module_path):
            os.unlink(temp_module_path)
    return DynamicValidationResult(True, "Todos los escenarios pasaron.")

def _validate_function_unit(user_code: str, func_name: str, scenarios: List[Dict], analyzer: CodeAnalyzer) -> DynamicValidationResult:
    """Valida una función estándar o generadora."""
    if func_name not in analyzer.analysis["defined_functions"]:
        return DynamicValidationResult(False, f"Función '{func_name}' no está definida.")

    temp_module_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding='utf-8') as tmp_file:
            temp_module_path = tmp_file.name
            tmp_file.write(user_code)

        spec = importlib.util.spec_from_file_location(f"usermodule_{random.randint(1000,9999)}", temp_module_path)
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        actual_func = getattr(user_module, func_name)
        is_gen = analyzer.is_generator(func_name)

        for i, scenario in enumerate(scenarios):
            args = scenario.get("args", [])
            expected = scenario.get("expected_return_value")
            try:
                actual = actual_func(*args)
                # Manejo especial para generadores y sets
                if is_gen:
                    actual = list(actual)

                # Si el valor esperado es una lista, y el actual es un set, comparar sin orden
                if isinstance(expected, list) and isinstance(actual, set):
                    if set(expected) != actual:
                         return DynamicValidationResult(False, f"Escenario {i+1} con args {args} falló. Se esperaba un set equivalente a '{expected}', pero se obtuvo '{actual}'.")
                elif actual != expected:
                    return DynamicValidationResult(False, f"Escenario {i+1} con args {args} falló. Se esperaba '{expected}', pero se obtuvo '{actual}'.")
            except Exception as e:
                return DynamicValidationResult(False, f"Escenario {i+1} produjo un error: {type(e).__name__}: {e}")
    except Exception as e:
        return DynamicValidationResult(False, f"Error al cargar la función: {e}")
    finally:
        if temp_module_path and os.path.exists(temp_module_path):
            os.unlink(temp_module_path)
    return DynamicValidationResult(True, "Todos los escenarios pasaron.")

def validate_exam_exercise(user_code: str, rules: Dict[str, Any], **kwargs) -> DynamicValidationResult:
    """Validador principal para exámenes que orquesta múltiples pruebas."""
    logger.info("--- Iniciando validación de examen ---")
    analyzer = CodeAnalyzer(user_code)
    if analyzer.syntax_error:
        return DynamicValidationResult(False, f"Tu código tiene un error de sintaxis: {analyzer.syntax_error}")

    # Check for security issues first
    static_failures = analyzer.check_static_requirements({}) # Basic security check
    if static_failures:
        return DynamicValidationResult(False, "Static analysis failed: " + " ".join(static_failures))

    feedback = {"Unidades de Código": [], "Requisitos Estructurales": [], "Salida del Script": []}
    passed_checks = 0
    total_checks = 0

    # --- 1. Validar Unidades de Código (Clases y Funciones) ---
    test_units = rules.get("functions", [])
    total_checks += len(test_units)
    for unit in test_units:
        unit_name = unit.get("function_name")
        scenarios = unit.get("scenarios", [])
        is_class_test = scenarios and "setup_code" in scenarios[0]

        result = _validate_class_unit(user_code, unit_name, scenarios, analyzer) if is_class_test else _validate_function_unit(user_code, unit_name, scenarios, analyzer)
        feedback["Unidades de Código"].append(f"Unidad '{unit_name}': {'PASSED' if result.passed else 'FAILED'}. {result.message}")
        if result.passed: passed_checks += 1

    # --- 2. Validar Clases Definidas Separadamente (backward compatibility) ---
    class_rules_list = rules.get("classes", [])
    total_checks += len(class_rules_list)

    for class_rules in class_rules_list:
        class_name = class_rules.get("class_name")
        scenarios = class_rules.get("scenarios", [])

        if not class_name:
            feedback["Unidades de Código"].append(f"Config error for a class in the exam.")
            continue

        result = _validate_class_unit(user_code, class_name, scenarios, analyzer)
        feedback["Unidades de Código"].append(f"Clase '{class_name}': {'PASSED' if result.passed else 'FAILED'}. {result.message}")
        if result.passed: passed_checks += 1

    # --- 3. Validar Requisitos Estructurales Dinámicos desde JSON ---
    struct_rules = rules.get("structural_requirements", {})

    required_imports = struct_rules.get("imports", [])
    total_checks += len(required_imports)
    for imp in required_imports:
        if imp in analyzer.analysis["imports"]:
            passed_checks += 1
            feedback["Requisitos Estructurales"].append(f"Import '{imp}': PASSED.")
        else:
            feedback["Requisitos Estructurales"].append(f"Import '{imp}': FAILED. No se encontró la importación requerida.")

    decorator_rules = struct_rules.get("decorators", [])
    total_checks += len(decorator_rules)
    for dec_rule in decorator_rules:
        func = dec_rule.get("function")
        deco = dec_rule.get("decorator")
        if func and deco:
            if analyzer.is_function_decorated(func, deco):
                passed_checks += 1
                feedback["Requisitos Estructurales"].append(f"Decorador '@{deco}' en '{func}': PASSED.")
            else:
                feedback["Requisitos Estructurales"].append(f"Decorador '@{deco}' en '{func}': FAILED. El decorador no fue aplicado a la función correcta.")

    # --- 4. Validar Salida Completa del Script ---
    expected_output = rules.get("expected_script_output")
    if expected_output:
        total_checks += 1
        stdout, stderr, timed_out, exit_code, _ = run_user_code_sandboxed(user_code)
        if exit_code == 0 and not timed_out:
            normalized_stdout = "\n".join(line.strip() for line in stdout.strip().splitlines())
            normalized_expected = "\n".join(line.strip() for line in expected_output.strip().splitlines())
            if normalized_stdout == normalized_expected:
                passed_checks += 1
                feedback["Salida del Script"].append("Salida del Script: PASSED.")
            else:
                feedback["Salida del Script"].append(f"Salida del Script: FAILED. La salida no coincide.\nSe esperaba:\n---\n{normalized_expected}\n---\nSe obtuvo:\n---\n{normalized_stdout}\n---")
        else:
            feedback["Salida del Script"].append(f"Salida del Script: FAILED. El código produjo un error: {stderr}")

    # --- 5. Generar Reporte Final ---
    if total_checks == 0:
        return DynamicValidationResult(False, "No se encontraron pruebas para validar en la configuración del examen.")

    summary = f"Resultado: {passed_checks}/{total_checks} pruebas pasadas."
    final_message_parts = [summary]
    for category, messages in feedback.items():
        if messages:
            final_message_parts.append(f"\n--- {category} ---")
            final_message_parts.extend(f"- {msg}" for msg in messages)

    final_message = "\n".join(final_message_parts)
    return DynamicValidationResult(passed_checks == total_checks, final_message)

# --- Validator Dispatcher Map ---
def validate_flexible_exercise(user_code: str, rules: Dict[str, Any], **kwargs) -> DynamicValidationResult:
    """
    Validator for tutorial-style exercises where we care more about code structure than exact output.
    """
    analyzer = CodeAnalyzer(user_code)

    # Check for required coding structures
    struct_requirements = {}
    if rules.get("require_tuple"): struct_requirements["tuple"] = True
    if rules.get("require_set"): struct_requirements["set"] = True
    if rules.get("require_dict"): struct_requirements["dict"] = True
    if rules.get("require_list"): struct_requirements["list"] = True

    # Check for AST-level requirements
    static_failures = analyzer.check_static_requirements(rules)
    if static_failures:
        return DynamicValidationResult(False, "Static analysis failed: " + " ".join(static_failures))

    # Run the code
    stdout, stderr, timed_out, exit_code, _ = run_user_code_sandboxed(
        user_code, input_data=kwargs.get("input_data"), timeout=kwargs.get("timeout", 5)
    )

    if timed_out:
        return DynamicValidationResult(False, "Execution timed out.", actual_output=stdout)
    if exit_code != 0:
        return DynamicValidationResult(False, f"Runtime error: {stderr.strip()}", actual_output=stdout)
    if not stdout.strip():
        return DynamicValidationResult(False, "No output detected. Use print() to display results.", actual_output=stdout)

    # If we have minimum structure requirements but no exact output requirements,
    # consider it a pass as long as there's some output
    return DynamicValidationResult(True, "Exercise passed!", actual_output=stdout)

def validate_conditional_print_exercise(user_code: str, rules: Dict[str, Any], **kwargs) -> DynamicValidationResult:
    analyzer = CodeAnalyzer(user_code)
    if analyzer.syntax_error:
        return DynamicValidationResult(False, f"Your code has a syntax error: {analyzer.syntax_error}")

    # Static analysis for if statement
    if rules.get("require_if_statement", True) and not analyzer.analysis.get("has_if"):
        return DynamicValidationResult(False, "This exercise requires using an if/else statement.")

    # Determine which inputs to test
    inputs_to_test = []
    user_provided_input = kwargs.get("input_data")

    if user_provided_input is not None:
        inputs_to_test.append(user_provided_input)
    else:
        # Check if we have test_cases (new format) or output_logic (old format)
        test_cases = rules.get("test_cases", [])
        if test_cases:
            # NEW FORMAT: Use predefined test cases with input/expected_output pairs
            for case in test_cases:
                case_input = case.get("input")
                expected_output = case.get("expected_output")
                if case_input is not None and expected_output is not None:
                    input_with_newline = f'{case_input}\n'
                    stdout, stderr, timed_out, exit_code, _ = run_user_code_sandboxed(
                        user_code, input_with_newline, kwargs.get("timeout", 5)
                    )

                    if timed_out:
                        return DynamicValidationResult(False, f"Execution timed out on input '{case_input}'.", actual_output=stdout)
                    if exit_code != 0:
                        return DynamicValidationResult(False, f"Runtime error on input '{case_input}': {stderr.strip()}", actual_output=stdout)

                    # Compare the actual output with the expected output
                    normalized_stdout = stdout.replace('\r\n', '\n').strip()
                    normalized_expected = expected_output.replace('\r\n', '\n').strip()

                    if normalized_stdout != normalized_expected:
                        feedback_key = "wrong_output"
                        default_msg = f"Failed on input '{case_input}'. Expected: '{normalized_expected}', but got: '{normalized_stdout}'"
                        message = rules.get("custom_feedback", {}).get(feedback_key, default_msg)
                        return DynamicValidationResult(False, message, actual_output=stdout)

            # If all test cases passed
            return DynamicValidationResult(True, "All test cases passed!")

        else:
            # OLD FORMAT: Use output_logic for dynamic evaluation
            output_logic = rules.get("output_logic")
            if not output_logic or not all(k in output_logic for k in ["condition", "true_output", "false_output"]):
                return DynamicValidationResult(False, "Validation config error: Either 'test_cases' or complete 'output_logic' rule is required.")

            # This would be for exercises that use dynamic logic evaluation
            # (keeping the existing logic for backward compatibility)
            inputs_to_test = ["10", "7"]  # Default test inputs if none provided

    # Handle user-provided input case (when testing from frontend)
    if user_provided_input is not None:
        input_with_newline = f'{user_provided_input}\n'
        stdout, stderr, timed_out, exit_code, _ = run_user_code_sandboxed(
            user_code, input_with_newline, kwargs.get("timeout", 5)
        )

        if timed_out:
            return DynamicValidationResult(False, f"Execution timed out.", actual_output=stdout)
        if exit_code != 0:
            return DynamicValidationResult(False, f"Runtime error: {stderr.strip()}", actual_output=stdout)

        return DynamicValidationResult(True, "Code executed successfully with your input.", actual_output=stdout)

    # This should not be reached for exercises with test_cases format
    return DynamicValidationResult(False, "No validation path matched.")
def validate_class_exercise(user_code: str, rules: Dict[str, Any], **kwargs) -> DynamicValidationResult:
    """
    Validates exercises that require the user to define and use a class.
    It performs static analysis and then dynamically imports and tests the class.
    """
    class_name = rules.get("class_name")
    if not class_name:
        return DynamicValidationResult(False, "Validation config error: 'class_name' is missing.")

    # 1. Static Analysis
    analyzer = CodeAnalyzer(user_code)
    if analyzer.syntax_error:
        return DynamicValidationResult(False, f"Your code has a syntax error: {analyzer.syntax_error}")

    class_node = analyzer.get_class_node(class_name)
    if not class_node:
        return DynamicValidationResult(False, f"Class '{class_name}' was not found in your code.")

    if rules.get("require_dataclass") and not analyzer.check_is_dataclass(class_node):
        return DynamicValidationResult(False, f"The class '{class_name}' must be a dataclass. Did you use the '@dataclass' decorator?")

    if rules.get("require_frozen") and not analyzer.check_is_dataclass(class_node, frozen=True):
        return DynamicValidationResult(False, f"The dataclass '{class_name}' must be immutable. Use '@dataclass(frozen=True)'.")

    # 2. Dynamic Import and Execution of Checks
    temp_module_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding='utf-8') as tmp_file:
            temp_module_path = tmp_file.name
            tmp_file.write(user_code)

        spec = importlib.util.spec_from_file_location(f"usermodule_{os.path.basename(temp_module_path).replace('.py', '')}", temp_module_path)
        if not spec or not spec.loader:
            return DynamicValidationResult(False, "Validator error: Failed to create module spec.")

        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)

        if not hasattr(user_module, class_name):
            return DynamicValidationResult(False, f"Failed to import class '{class_name}'. Check for errors outside the class definition.")

        UserClass = getattr(user_module, class_name)

        # This dictionary will hold instances created during checks
        instances = {}

        # Execute checks sequentially
        for i, check in enumerate(rules.get("checks", [])):
            check_type = check.get("type")
            instance_name = check.get("instance_name", "default")

            try:
                if check_type == "instantiation":
                    args = check.get("args", [])
                    kwargs = check.get("kwargs", {})
                    instance = UserClass(*args, **kwargs)
                    instances[instance_name] = instance

                elif check_type == "attribute_check":
                    instance = instances[instance_name]
                    attr_name = check["attribute"]
                    expected_value = check["expected_value"]
                    if not hasattr(instance, attr_name):
                        return DynamicValidationResult(False, f"Check {i+1} failed: Instance has no attribute '{attr_name}'.")
                    actual_value = getattr(instance, attr_name)
                    if actual_value != expected_value:
                        return DynamicValidationResult(False, f"Check {i+1} failed: Attribute '{attr_name}' should be '{expected_value}', but was '{actual_value}'.")

                elif check_type == "property_check":
                    instance = instances[instance_name]
                    prop_name = check["property"]
                    expected_value = check["expected_value"]
                    if not hasattr(instance, prop_name):
                         return DynamicValidationResult(False, f"Check {i+1} failed: Instance has no property '{prop_name}'.")
                    actual_value = getattr(instance, prop_name)
                    if actual_value != expected_value:
                        return DynamicValidationResult(False, f"Check {i+1} failed: Property '{prop_name}' should be '{expected_value}', but was '{actual_value}'.")

                elif check_type == "method_call":
                    instance = instances[instance_name]
                    method_name = check["method"]
                    args = check.get("args", [])
                    kwargs = check.get("kwargs", {})
                    if not hasattr(instance, method_name):
                        return DynamicValidationResult(False, f"Check {i+1} failed: Instance has no method '{method_name}'.")
                    method = getattr(instance, method_name)
                    actual_return = method(*args, **kwargs)

                    if "expected_return_value" in check:
                        expected_return = check["expected_return_value"]
                        if actual_return != expected_return:
                            return DynamicValidationResult(False, f"Check {i+1} failed: Method '{method_name}' returned '{actual_return}' but expected '{expected_return}'.")

                    if check.get("saves_return_as"):
                        instances[check["saves_return_as"]] = actual_return


                elif check_type == "str_check":
                    instance = instances[instance_name]
                    expected_str = check["expected_output"]
                    actual_str = str(instance)
                    if actual_str != expected_str:
                        return DynamicValidationResult(False, f"Check {i+1} failed: The string representation was incorrect. Expected '{expected_str}', got '{actual_str}'.")

            except Exception as e:
                return DynamicValidationResult(False, f"An error occurred during check {i+1} ({check_type}): {type(e).__name__}: {e}")

    except Exception as e:
        return DynamicValidationResult(False, f"A critical error occurred during validation: {type(e).__name__}: {e}")
    finally:
        if temp_module_path and os.path.exists(temp_module_path):
            try: os.unlink(temp_module_path)
            except Exception: pass

    return DynamicValidationResult(True, "All class checks passed!")

VALIDATOR_MAP = {
    "simple_print": validate_simple_print_exercise,
    "dynamic_output": validate_dynamic_output_exercise,
    "conditional_print": validate_conditional_print_exercise,
    "function_scenarios": validate_exam_exercise, # Replaces function_check, exam
    "exam": validate_exam_exercise, # Keep for compatibility
    "saludo_personalizado": validate_saludo_personalizado, # <-- ADD THIS LINE
    "flexible_exercise": validate_flexible_exercise,  # Add the new validator
    "class_exercise": validate_class_exercise,
    # "function_and_output" is deprecated for simplicity.
    # "class_exercise" can be added back here if needed, following the new pattern.
}
