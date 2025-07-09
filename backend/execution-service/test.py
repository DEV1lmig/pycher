import ast
import requests
import json
from validators import CodeAnalyzer, validate_simple_print_exercise

print("=" * 80)
print("COMPREHENSIVE VALIDATOR TEST SUITE")
print("=" * 80)

# Test cases
hardcoded_fstring_code = '''
largo = 10
ancho = 5
area = largo * ancho
print(f"El área de un rectángulo de 10x5 es 50.")
'''

correct_fstring_code = '''
largo = 10
ancho = 5
area = largo * ancho
print(f"El área de un rectángulo de {largo}x{ancho} es {area}.")
'''

regular_print_code = '''
largo = 10
ancho = 5
area = largo * ancho
print("El área de un rectángulo de 10x5 es 50.")
'''

# Exercise rules
exercise_rules = {
    'expected_exact_output': 'El área de un rectángulo de 10x5 es 50.\n',
    'expected_print_count': 1,
    'required_variables_in_print': ['largo', 'ancho', 'area'],
    'strict_variable_names': ['largo', 'ancho', 'area'],
    'require_fstring': True,
    'strict_whitespace': True,
    'case_sensitive': True,
    'custom_feedback': {
        'wrong_output': 'El mensaje no es correcto. Asegúrate de usar un f-string y de que el texto coincida exactamente.',
        'wrong_variable': "Revisa que los nombres de las variables ('largo', 'ancho', 'area') sean correctos.",
        'not_fstring': "Parece que no estás usando un f-string. Recuerda poner la 'f' antes de las comillas."
    }
}

def test_ast_analysis(code, description):
    """Test the raw AST analysis logic"""
    print(f"\n🔍 {description}")
    print("-" * 60)

    tree = ast.parse(code)
    variables_used_in_prints = set()
    variables_defined = set()
    is_fstring_found = False

    for node in ast.walk(tree):
        # Track variable definitions
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variables_defined.add(target.id)

        # Track print calls and f-strings
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
            print(f"  📄 Found print call with {len(node.args)} arguments")

            for arg in node.args:
                if isinstance(arg, ast.JoinedStr):
                    is_fstring_found = True
                    print(f"  🔤 Found f-string with {len(arg.values)} parts")
                    for i, value_node in enumerate(arg.values):
                        print(f"    Part {i}: {type(value_node).__name__}")
                        if isinstance(value_node, ast.FormattedValue):
                            if isinstance(value_node.value, ast.Name):
                                var_name = value_node.value.id
                                variables_used_in_prints.add(var_name)
                                print(f"      ✅ Variable found: {var_name}")
                            else:
                                print(f"      ❌ Non-variable in f-string: {type(value_node.value)}")
                        elif isinstance(value_node, ast.Constant):
                            print(f"      📝 Constant string: {repr(value_node.value)}")
                elif isinstance(arg, ast.Name):
                    # Regular variable in print (not f-string)
                    var_name = arg.id
                    variables_used_in_prints.add(var_name)
                    print(f"  📝 Regular variable in print: {var_name}")

    print(f"  📊 Variables defined: {variables_defined}")
    print(f"  📊 Variables used in prints: {variables_used_in_prints}")
    print(f"  📊 F-string detected: {is_fstring_found}")

    return {
        'variables_defined': variables_defined,
        'variables_used_in_prints': variables_used_in_prints,
        'is_fstring': is_fstring_found
    }

def test_code_analyzer(code, description):
    """Test the CodeAnalyzer class"""
    print(f"\n🏗️ CodeAnalyzer Test: {description}")
    print("-" * 60)

    analyzer = CodeAnalyzer(code)

    print(f"  📊 Syntax error: {analyzer.syntax_error}")
    print(f"  📊 Variables defined: {analyzer.variables_defined}")
    print(f"  📊 Variables used in prints: {analyzer.variables_used_in_prints}")
    print(f"  📊 Print calls: {analyzer.analysis.get('print_calls', [])}")

    # Test variable validation
    required_vars = ['largo', 'ancho', 'area']
    errors = analyzer.check_variables_in_print(required_vars)
    print(f"  📊 Variable validation errors: {errors}")

    return {
        'analyzer': analyzer,
        'errors': errors,
        'passes_validation': len(errors) == 0
    }

def test_validator_function(code, description):
    """Test the validate_simple_print_exercise function"""
    print(f"\n⚙️ Validator Function Test: {description}")
    print("-" * 60)

    result = validate_simple_print_exercise(code, exercise_rules)

    print(f"  📊 Passed: {result.passed}")
    print(f"  📊 Message: {result.message}")
    print(f"  📊 Output: {repr(result.actual_output)}")

    return result

def test_api_endpoint(code, description):
    """Test the actual API endpoint"""
    print(f"\n🌐 API Endpoint Test: {description}")
    print("-" * 60)

    payload = {
        "exercise_id": 3,
        "code": code,
        "input_data": "",
        "timeout": 10
    }

    try:
        response = requests.post("http://localhost:8001/execute", json=payload)
        print(f"  📊 Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"  📊 Passed: {result.get('passed')}")
            print(f"  📊 Error: {result.get('error')}")
            print(f"  📊 Output: {repr(result.get('output'))}")
            print(f"  📊 Execution Time: {result.get('execution_time')}")
            return result
        else:
            print(f"  ❌ HTTP Error: {response.text}")
            return None
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return None

def run_comprehensive_test():
    """Run all test categories"""

    test_cases = [
        (hardcoded_fstring_code, "HARDCODED F-STRING (should fail)"),
        (correct_fstring_code, "CORRECT F-STRING (should pass)"),
        (regular_print_code, "REGULAR PRINT (should fail - no f-string)")
    ]

    results = {}

    for code, description in test_cases:
        print(f"\n{'=' * 80}")
        print(f"TESTING: {description}")
        print(f"{'=' * 80}")

        # Test 1: Raw AST Analysis
        ast_result = test_ast_analysis(code, f"Raw AST Analysis - {description}")

        # Test 2: CodeAnalyzer Class
        analyzer_result = test_code_analyzer(code, description)

        # Test 3: Validator Function
        validator_result = test_validator_function(code, description)

        # Test 4: API Endpoint
        api_result = test_api_endpoint(code, description)

        # Store results
        results[description] = {
            'ast': ast_result,
            'analyzer': analyzer_result,
            'validator': validator_result,
            'api': api_result
        }

    # Summary
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print(f"{'=' * 80}")

    for test_name, test_results in results.items():
        print(f"\n📋 {test_name}")
        print("-" * 60)

        # Expected results based on test case
        if "HARDCODED" in test_name or "REGULAR PRINT" in test_name:
            expected_pass = False
            expectation = "SHOULD FAIL"
        else:
            expected_pass = True
            expectation = "SHOULD PASS"

        print(f"  Expected: {expectation}")

        # AST Analysis
        ast_vars = test_results['ast']['variables_used_in_prints']
        required_vars = {'largo', 'ancho', 'area'}
        ast_has_all_vars = required_vars.issubset(ast_vars)
        print(f"  🔍 AST finds all variables: {ast_has_all_vars}")

        # Analyzer
        analyzer_passes = test_results['analyzer']['passes_validation']
        print(f"  🏗️ Analyzer validation: {'PASS' if analyzer_passes else 'FAIL'}")

        # Validator Function
        validator_passes = test_results['validator'].passed
        print(f"  ⚙️ Validator function: {'PASS' if validator_passes else 'FAIL'}")

        # API
        api_passes = test_results['api']['passed'] if test_results['api'] else None
        print(f"  🌐 API endpoint: {'PASS' if api_passes else 'FAIL' if api_passes is not None else 'ERROR'}")

        # Overall consistency check
        all_consistent = (
            (analyzer_passes == expected_pass) and
            (validator_passes == expected_pass) and
            (api_passes == expected_pass if api_passes is not None else True)
        )

        print(f"  🎯 Results consistent with expectations: {'✅ YES' if all_consistent else '❌ NO'}")

if __name__ == "__main__":
    run_comprehensive_test()
