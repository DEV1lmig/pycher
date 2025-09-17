#!/usr/bin/env python3
"""
Script de prueba para validar la funcionalidad de validación de tipos en validate_saludo_personalizado
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'execution-service'))

from validators import validate_saludo_personalizado

def test_string_input():
    """Prueba con entrada de tipo string (debería pasar)"""
    print("=== Test 1: String input (should pass) ===")
    
    user_code = '''
nombre = input("Ingresa tu nombre: ")
print(f"¡Hola, {nombre}!")
'''
    
    rules = {
        "output_format_template": "¡Hola, {var}!",
        "requires_input_function": True,
        "expected_input_type": "str",
        "require_fstring": True,
        "custom_feedback": {
            "wrong_input_type": "Debes usar input() directamente para strings."
        }
    }
    
    result = validate_saludo_personalizado(user_code, rules, input_data="Juan")
    print(f"Result: {result.passed}")
    print(f"Message: {result.message}")
    print(f"Output: {result.actual_output}")
    print()

def test_int_input_correct():
    """Prueba con entrada de tipo int correcta (debería pasar)"""
    print("=== Test 2: Int input correct (should pass) ===")
    
    user_code = '''
edad = int(input("Ingresa tu edad: "))
print(f"Tienes {edad} años!")
'''
    
    rules = {
        "output_format_template": "Tienes {var} años!",
        "requires_input_function": True,
        "expected_input_type": "int",
        "require_fstring": True,
        "custom_feedback": {
            "wrong_input_type": "Debes convertir la entrada a entero usando int(input())."
        }
    }
    
    result = validate_saludo_personalizado(user_code, rules, input_data="25")
    print(f"Result: {result.passed}")
    print(f"Message: {result.message}")
    print(f"Output: {result.actual_output}")
    print()

def test_int_input_incorrect():
    """Prueba con entrada de tipo int incorrecta (debería fallar)"""
    print("=== Test 3: Int input incorrect (should fail) ===")
    
    user_code = '''
edad = input("Ingresa tu edad: ")
print(f"Tienes {edad} años!")
'''
    
    rules = {
        "output_format_template": "Tienes {var} años!",
        "requires_input_function": True,
        "expected_input_type": "int",
        "require_fstring": True,
        "custom_feedback": {
            "wrong_input_type": "Debes convertir la entrada a entero usando int(input())."
        }
    }
    
    result = validate_saludo_personalizado(user_code, rules, input_data="25")
    print(f"Result: {result.passed}")
    print(f"Message: {result.message}")
    print(f"Output: {result.actual_output}")
    print()

def test_float_input_correct():
    """Prueba con entrada de tipo float correcta (debería pasar)"""
    print("=== Test 4: Float input correct (should pass) ===")
    
    user_code = '''
precio = float(input("Ingresa el precio: "))
print(f"El precio es ${precio}")
'''
    
    rules = {
        "output_format_template": "El precio es ${var}",
        "requires_input_function": True,
        "expected_input_type": "float",
        "require_fstring": True,
        "custom_feedback": {
            "wrong_input_type": "Debes convertir la entrada a decimal usando float(input())."
        }
    }
    
    result = validate_saludo_personalizado(user_code, rules, input_data="19.99")
    print(f"Result: {result.passed}")
    print(f"Message: {result.message}")
    print(f"Output: {result.actual_output}")
    print()

def test_invalid_input_value():
    """Prueba con valor de entrada inválido para el tipo (debería fallar)"""
    print("=== Test 5: Invalid input value for type (should fail) ===")
    
    user_code = '''
edad = int(input("Ingresa tu edad: "))
print(f"Tienes {edad} años!")
'''
    
    rules = {
        "output_format_template": "Tienes {var} años!",
        "requires_input_function": True,
        "expected_input_type": "int",
        "require_fstring": True,
        "custom_feedback": {
            "wrong_input_type": "Debes convertir la entrada a entero usando int(input()).",
            "invalid_input_value": "El valor ingresado no es un número válido."
        }
    }
    
    result = validate_saludo_personalizado(user_code, rules, input_data="abc")
    print(f"Result: {result.passed}")
    print(f"Message: {result.message}")
    print(f"Output: {result.actual_output}")
    print()

if __name__ == "__main__":
    test_string_input()
    test_int_input_correct()
    test_int_input_incorrect()
    test_float_input_correct()
    test_invalid_input_value()