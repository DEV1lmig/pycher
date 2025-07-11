import pytest
import ast
from validators import CodeAnalyzer, DynamicValidationResult
import os
import sys
from re import match, search
from typing import List, Dict
import requests
import asyncio
from dataclasses import dataclass
from functools import wraps
import re
from typing import Generator, List
import re

class TestCodeAnalyzer:
    """Test suite for CodeAnalyzer.analyze() method"""

    def test_basic_analysis_empty_code(self):
        """Test analysis of empty code"""
        analyzer = CodeAnalyzer("")
        assert analyzer.syntax_error is None
        assert analyzer.analysis["imports"] == set()
        assert analyzer.analysis["defined_functions"] == {}
        assert analyzer.analysis["defined_classes"] == {}
        assert analyzer.variables_defined == set()

    def test_syntax_error_handling(self):
        """Test handling of syntax errors"""
        code = "def invalid_syntax(:\n    pass"
        analyzer = CodeAnalyzer(code)
        assert analyzer.syntax_error is not None
        assert "syntax" in analyzer.syntax_error.lower()

    def test_import_detection(self):
        """Test detection of various import statements"""
        code = """
"""
        analyzer = CodeAnalyzer(code)
        expected_imports = {"os", "sys", "re", "typing", "requests"}
        assert analyzer.analysis["imports"] == expected_imports
        assert "os" in analyzer.analysis["disallowed_imports"]
        assert "sys" in analyzer.analysis["disallowed_imports"]
        assert "requests" in analyzer.analysis["disallowed_imports"]

    def test_function_call_detection(self):
        """Test detection of function calls and security violations"""
        code = """
print("Hello")
eval("2 + 2")
exec("x = 1")
len([1, 2, 3])
open("file.txt")
"""
        analyzer = CodeAnalyzer(code)
        expected_calls = {"print", "eval", "exec", "len", "open"}
        assert analyzer.analysis["function_calls"] == expected_calls
        assert "eval" in analyzer.analysis["disallowed_calls"]
        assert "exec" in analyzer.analysis["disallowed_calls"]
        assert "open" in analyzer.analysis["disallowed_calls"]

    def test_variable_definitions(self):
        """Test detection of variable assignments"""
        code = """
x = 10
name = "Python"
numbers = [1, 2, 3]
person = {"name": "Ana", "age": 25}
"""
        analyzer = CodeAnalyzer(code)
        expected_vars = {"x", "name", "numbers", "person"}
        assert analyzer.variables_defined == expected_vars

    def test_class_definitions(self):
        """Test detection of class definitions"""
        code = """
class Persona:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self.edad = edad

    def cumplir_anos(self):
        self.edad += 1

class Producto:
    pass
"""
        analyzer = CodeAnalyzer(code)
        assert "Persona" in analyzer.analysis["defined_classes"]
        assert "Producto" in analyzer.analysis["defined_classes"]
        assert isinstance(analyzer.analysis["defined_classes"]["Persona"], ast.ClassDef)

    def test_function_definitions(self):
        """Test detection of function definitions including async"""
        code = """
def generar_pares(n):
    for i in range(1, n + 1):
        yield i * 2

async def async_function():
    await some_operation()
    return "done"

def lambda_user():
    return lambda x: x * 2
"""
        analyzer = CodeAnalyzer(code)
        assert "generar_pares" in analyzer.analysis["defined_functions"]
        assert "async_function" in analyzer.analysis["defined_functions"]
        assert "lambda_user" in analyzer.analysis["defined_functions"]
        assert isinstance(analyzer.analysis["defined_functions"]["generar_pares"], ast.FunctionDef)
        assert isinstance(analyzer.analysis["defined_functions"]["async_function"], ast.AsyncFunctionDef)

    def test_control_structures(self):
        """Test detection of control structures"""
        code = """
# For loop
for i in range(5):
    print(i)

# If statement
if x > 0:
    print("positive")
else:
    print("negative")

# Try-except
try:
    result = 10 / 0
except ZeroDivisionError:
    print("error")

# With statement
with open("file.txt") as f:
    content = f.read()
"""
        analyzer = CodeAnalyzer(code)
        assert analyzer.analysis["has_for_loop"] is True
        assert analyzer.analysis["has_if"] is True
        assert analyzer.analysis["has_try_except"] is True
        assert analyzer.analysis["has_with"] is True

    def test_comprehensions(self):
        """Test detection of list, dict, and set comprehensions"""
        code = """
# List comprehension
squares = [x**2 for x in range(10)]

# Dict comprehension
square_dict = {x: x**2 for x in range(5)}

# Set comprehension
even_set = {x for x in range(10) if x % 2 == 0}
"""
        analyzer = CodeAnalyzer(code)
        assert analyzer.analysis["has_list_comp"] is True
        assert analyzer.analysis["has_dict_comp"] is True
        assert analyzer.analysis["has_set_comp"] is True

    def test_lambda_functions(self):
        """Test detection of lambda expressions"""
        code = """
# Simple lambda
double = lambda x: x * 2

# Lambda in map
numbers = list(map(lambda x: x**2, [1, 2, 3, 4]))

# Lambda in filter
evens = list(filter(lambda x: x % 2 == 0, range(10)))
"""
        analyzer = CodeAnalyzer(code)
        assert analyzer.analysis["has_lambda"] is True

    def test_generator_functions(self):
        """Test detection of yield statements (generators)"""
        code = """
def fibonacci_generator(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

def yield_from_example():
    yield from range(5)
"""
        analyzer = CodeAnalyzer(code)
        assert analyzer.analysis["has_yield"] is True

    def test_async_await(self):
        """Test detection of async/await patterns"""
        code = """

async def fetch_data():
    result = await asyncio.sleep(1)
    return result

async def main():
    data = await fetch_data()
    return data
"""
        analyzer = CodeAnalyzer(code)
        assert analyzer.analysis["has_await"] is True

    def test_print_statement_analysis_simple(self):
        """Test analysis of simple print statements"""
        code = """
name = "Ana"
age = 25
print(name)
print(age)
print("Hello World")
"""
        analyzer = CodeAnalyzer(code)
        assert len(analyzer.analysis["print_calls"]) == 3
        assert "name" in analyzer.variables_used_in_prints
        assert "age" in analyzer.variables_used_in_prints

        # Check first print call
        first_print = analyzer.analysis["print_calls"][0]
        assert first_print["is_fstring"] is False
        assert any(arg["variable_name"] == "name" for arg in first_print["args"])

    def test_print_statement_analysis_fstring(self):
        """Test analysis of f-string print statements"""
        code = """
nombre = "Carlos"
edad = 30
print(f"Hola, mi nombre es {nombre}")
print(f"Tengo {edad} años")
print(f"En 5 años tendré {edad + 5} años")
"""
        analyzer = CodeAnalyzer(code)
        assert len(analyzer.analysis["print_calls"]) == 3
        assert "nombre" in analyzer.variables_used_in_prints
        assert "edad" in analyzer.variables_used_in_prints

        # Check f-string detection
        for print_call in analyzer.analysis["print_calls"]:
            assert print_call["is_fstring"] is True

    def test_complex_class_with_decorators(self):
        """Test analysis of classes with decorators and methods"""
        code = """

def log_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@dataclass
class Producto:
    nombre: str
    precio: float

    @log_decorator
    def aplicar_descuento(self, porcentaje):
        self.precio *= (1 - porcentaje / 100)
        return self.precio

    @property
    def precio_con_iva(self):
        return self.precio * 1.21
"""
        analyzer = CodeAnalyzer(code)
        assert "Producto" in analyzer.analysis["defined_classes"]
        assert "log_decorator" in analyzer.analysis["defined_functions"]
        assert analyzer.analysis["has_lambda"] is False  # No lambda in this code
        assert "dataclasses" in analyzer.analysis["imports"]
        assert "functools" in analyzer.analysis["imports"]

    def test_advanced_exam_style_code(self):
        """Test analysis of advanced exam-style code with multiple concepts"""
        code = """

def filtrar_emails(emails: List[str]) -> List[str]:
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return [email for email in emails if re.match(patron, email)]

def generar_fibonacci(n: int) -> Generator[int, None, None]:
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

class Calculadora:
    def __init__(self):
        self.historial = []

    def sumar(self, a, b):
        resultado = a + b
        self.historial.append(f"{a} + {b} = {resultado}")
        return resultado

    def __str__(self):
        return f"Calculadora con {len(self.historial)} operaciones"

# Uso de lambda y map
numeros = [1, 2, 3, 4, 5]
cuadrados = list(map(lambda x: x**2, numeros))

# Uso de comprehension con filtro
pares = [x for x in numeros if x % 2 == 0]

# Print con f-strings
calc = Calculadora()
resultado = calc.sumar(5, 3)
print(f"El resultado es {resultado}")
print(f"Calculadora: {calc}")
"""
        analyzer = CodeAnalyzer(code)

        # Check imports
        assert "re" in analyzer.analysis["imports"]
        assert "typing" in analyzer.analysis["imports"]

        # Check functions
        assert "filtrar_emails" in analyzer.analysis["defined_functions"]
        assert "generar_fibonacci" in analyzer.analysis["defined_functions"]

        # Check class
        assert "Calculadora" in analyzer.analysis["defined_classes"]

        # Check control structures
        assert analyzer.analysis["has_for_loop"] is True
        assert analyzer.analysis["has_yield"] is True
        assert analyzer.analysis["has_lambda"] is True
        assert analyzer.analysis["has_list_comp"] is True

        # Check variables
        assert "numeros" in analyzer.variables_defined
        assert "cuadrados" in analyzer.variables_defined
        assert "pares" in analyzer.variables_defined
        assert "calc" in analyzer.variables_defined
        assert "resultado" in analyzer.variables_defined

        # Check print analysis
        assert len(analyzer.analysis["print_calls"]) == 2
        assert "resultado" in analyzer.variables_used_in_prints
        assert "calc" in analyzer.variables_used_in_prints

    def test_decorator_patterns(self):
        """Test detection of decorator patterns"""
        code = """
def mi_decorador(func):
    def wrapper(*args, **kwargs):
        print("Antes de la función")
        resultado = func(*args, **kwargs)
        print("Después de la función")
        return resultado
    return wrapper

@mi_decorador
def saludar(nombre):
    print(f"¡Hola, {nombre}!")

class MiClase:
    @property
    def valor(self):
        return self._valor

    @valor.setter
    def valor(self, nuevo_valor):
        self._valor = nuevo_valor
"""
        analyzer = CodeAnalyzer(code)
        assert "mi_decorador" in analyzer.analysis["defined_functions"]
        assert "saludar" in analyzer.analysis["defined_functions"]
        assert "MiClase" in analyzer.analysis["defined_classes"]

    def test_regex_operations(self):
        """Test code that uses regular expressions"""
        code = """

def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email))

def extraer_numeros(texto):
    return re.findall(r'\d+', texto)

def reemplazar_espacios(texto):
    return re.sub(r'\s+', '_', texto)

# Uso de las funciones
email_valido = validar_email("usuario@example.com")
numeros = extraer_numeros("Tengo 25 años y vivo en el número 123")
texto_modificado = reemplazar_espacios("Hola mundo Python")

print(f"Email válido: {email_valido}")
print(f"Números encontrados: {numeros}")
print(f"Texto modificado: {texto_modificado}")
"""
        analyzer = CodeAnalyzer(code)
        assert "re" in analyzer.analysis["imports"]
        assert "validar_email" in analyzer.analysis["defined_functions"]
        assert "extraer_numeros" in analyzer.analysis["defined_functions"]
        assert "reemplazar_espacios" in analyzer.analysis["defined_functions"]
        assert "email_valido" in analyzer.variables_defined
        assert "numeros" in analyzer.variables_defined
        assert "texto_modificado" in analyzer.variables_defined

    def test_mixed_print_types(self):
        """Test analysis of mixed print statement types"""
        code = """
nombre = "Python"
version = 3.9
caracteristicas = ["simple", "potente", "versátil"]

# Print simple
print("Lenguaje de programación")

# Print con variable
print(nombre)

# Print con f-string
print(f"La versión actual es {version}")

# Print con múltiples argumentos
print("Características:", caracteristicas)

# Print con f-string complejo
print(f"{nombre} {version} tiene estas características: {', '.join(caracteristicas)}")
"""
        analyzer = CodeAnalyzer(code)
        assert len(analyzer.analysis["print_calls"]) == 5

        # Check variable usage detection
        assert "nombre" in analyzer.variables_used_in_prints
        assert "version" in analyzer.variables_used_in_prints
        assert "caracteristicas" in analyzer.variables_used_in_prints

        # Check f-string detection
        fstring_calls = [call for call in analyzer.analysis["print_calls"] if call["is_fstring"]]
        assert len(fstring_calls) == 2  # Two f-string prints
