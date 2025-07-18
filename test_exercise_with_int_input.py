#!/usr/bin/env python3
"""
Script para probar un ejercicio que requiere conversión de entrada a entero
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'execution-service'))

from validators import validate_saludo_personalizado

def test_exercise_with_int_input():
    """Simula un ejercicio que requiere entrada de tipo entero"""
    
    print("=== Ejercicio: Calcular el doble de un número ===")
    print("El estudiante debe pedir un número y mostrar su doble")
    print()
    
    # Código correcto del estudiante
    correct_code = '''
numero = int(input("Ingresa un número: "))
doble = numero * 2
print(f"El doble de {numero} es {doble}")
'''
    
    # Código incorrecto del estudiante (sin conversión a int)
    incorrect_code = '''
numero = input("Ingresa un número: ")
doble = numero * 2
print(f"El doble de {numero} es {doble}")
'''
    
    # Reglas del ejercicio
    rules = {
        "output_format_template": "El doble de {var} es {var}",  # Simplificado para la prueba
        "requires_input_function": True,
        "expected_input_type": "int",  # ¡Aquí está la clave!
        "require_fstring": True,
        "custom_feedback": {
            "wrong_input_type": "Debes convertir la entrada a entero usando int(input()).",
            "invalid_input_value": "El valor ingresado no es un número válido."
        }
    }
    
    print("--- Probando código CORRECTO ---")
    result1 = validate_saludo_personalizado(correct_code, rules, input_data="5")
    print(f"Resultado: {'✅ PASÓ' if result1.passed else '❌ FALLÓ'}")
    print(f"Mensaje: {result1.message}")
    if result1.actual_output:
        print(f"Salida: {result1.actual_output.strip()}")
    print()
    
    print("--- Probando código INCORRECTO (sin int()) ---")
    result2 = validate_saludo_personalizado(incorrect_code, rules, input_data="5")
    print(f"Resultado: {'✅ PASÓ' if result2.passed else '❌ FALLÓ'}")
    print(f"Mensaje: {result2.message}")
    if result2.actual_output:
        print(f"Salida: {result2.actual_output.strip()}")
    print()
    
    print("--- Probando con entrada inválida ---")
    result3 = validate_saludo_personalizado(correct_code, rules, input_data="abc")
    print(f"Resultado: {'✅ PASÓ' if result3.passed else '❌ FALLÓ'}")
    print(f"Mensaje: {result3.message}")
    if result3.actual_output:
        print(f"Salida: {result3.actual_output.strip()}")

if __name__ == "__main__":
    test_exercise_with_int_input()