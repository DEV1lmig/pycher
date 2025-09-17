#!/usr/bin/env python3
"""
Script para probar la funcionalidad de rechazo de entrada numérica en ejercicios de saludo personalizado
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'execution-service'))

from validators import validate_saludo_personalizado

def test_numeric_input_rejection():
    """Prueba la funcionalidad de rechazo de entrada numérica"""
    
    print("=== Ejercicio: Saludo Personalizado (NO acepta números) ===")
    print("El estudiante debe ingresar un NOMBRE, no un número")
    print()
    
    # Código del estudiante (correcto)
    student_code = '''
nombre = input("Ingresa tu nombre: ")
print(f"¡Hola, {nombre}!")
'''
    
    # Reglas del ejercicio (con rechazo de entrada numérica)
    rules = {
        "output_format_template": "¡Hola, {var}!",
        "requires_input_function": True,
        "expected_input_type": "str",  # Tipo string
        "reject_numeric_input": True,  # ¡Nueva regla!
        "require_fstring": True,
        "custom_feedback": {
            "numeric_input_rejected": "Por favor ingresa tu nombre (texto), no un número.",
            "not_fstring": "Usa un f-string para el saludo.",
            "wrong_output": "El formato del saludo no es correcto."
        }
    }
    
    print("--- Probando con NOMBRE VÁLIDO (Juan) ---")
    result1 = validate_saludo_personalizado(student_code, rules, input_data="Juan")
    print(f"Resultado: {'✅ PASÓ' if result1.passed else '❌ FALLÓ'}")
    print(f"Mensaje: {result1.message}")
    if result1.actual_output:
        print(f"Salida: {result1.actual_output.strip()}")
    print()
    
    print("--- Probando con NÚMERO ENTERO (123) ---")
    result2 = validate_saludo_personalizado(student_code, rules, input_data="123")
    print(f"Resultado: {'✅ PASÓ' if result2.passed else '❌ FALLÓ (como se esperaba)'}")
    print(f"Mensaje: {result2.message}")
    if result2.actual_output:
        print(f"Salida: {result2.actual_output.strip()}")
    print()
    
    print("--- Probando con NÚMERO DECIMAL (45.67) ---")
    result3 = validate_saludo_personalizado(student_code, rules, input_data="45.67")
    print(f"Resultado: {'✅ PASÓ' if result3.passed else '❌ FALLÓ (como se esperaba)'}")
    print(f"Mensaje: {result3.message}")
    if result3.actual_output:
        print(f"Salida: {result3.actual_output.strip()}")
    print()
    
    print("--- Probando con SOLO DÍGITOS (999) ---")
    result4 = validate_saludo_personalizado(student_code, rules, input_data="999")
    print(f"Resultado: {'✅ PASÓ' if result4.passed else '❌ FALLÓ (como se esperaba)'}")
    print(f"Mensaje: {result4.message}")
    if result4.actual_output:
        print(f"Salida: {result4.actual_output.strip()}")
    print()
    
    print("--- Probando con NOMBRE CON NÚMEROS (Ana123) ---")
    result5 = validate_saludo_personalizado(student_code, rules, input_data="Ana123")
    print(f"Resultado: {'✅ PASÓ' if result5.passed else '❌ FALLÓ'}")
    print(f"Mensaje: {result5.message}")
    if result5.actual_output:
        print(f"Salida: {result5.actual_output.strip()}")
    print()
    
    print("--- Probando SIN la regla reject_numeric_input ---")
    rules_without_rejection = rules.copy()
    rules_without_rejection["reject_numeric_input"] = False
    
    result6 = validate_saludo_personalizado(student_code, rules_without_rejection, input_data="123")
    print(f"Resultado: {'✅ PASÓ' if result6.passed else '❌ FALLÓ'}")
    print(f"Mensaje: {result6.message}")
    if result6.actual_output:
        print(f"Salida: {result6.actual_output.strip()}")

if __name__ == "__main__":
    test_numeric_input_rejection()