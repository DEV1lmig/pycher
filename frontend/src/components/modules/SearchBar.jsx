"use client"

import { useState } from "react"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"

export function SearchBar() {
  const [query, setQuery] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Ejemplos de sugerencias basadas en la consulta
  const suggestions = [
    { type: "curso", title: "Python Básico: Variables y Tipos", url: "/dashboard/courses/python-basico" },
    { type: "tema", title: "Funciones Lambda", url: "/dashboard/courses/python-intermedio/lambda" },
    { type: "ejercicio", title: "Ejercicio: Calculadora Simple", url: "/dashboard/exercises/calculadora" },
    { type: "documentación", title: "Módulo datetime", url: "/dashboard/docs/datetime" },
  ].filter((item) => query.length > 2 && item.title.toLowerCase().includes(query.toLowerCase()))

  return (
    <div className="relative w-64">
      <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
      <Input
        placeholder="Buscar temas, ejercicios..."
        className="pl-8 bg-[#160f30] border-[#312a56] text-white w-full"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
      />

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a1433] border border-[#312a56] rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
          {suggestions.map((item, index) => (
            <a
              key={index}
              href={item.url}
              className="block p-2 hover:bg-[#312a56] border-b border-[#312a56] last:border-b-0"
            >
              <div className="text-sm font-medium">{item.title}</div>
              <div className="text-xs text-gray-400">{item.type}</div>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
