import { useEffect, useState } from "react"
import { getUserProfile } from "@/services/userService"

export function WelcomeHeader() {
  const [user, setUser] = useState("")

  useEffect(() => {
    getUserProfile().then(setUser)
  }, [])

  return (
    <div className="bg-gradient-to-r from-[#312a56] to-[#1a1433] rounded-lg p-6">
      <h1 className="text-3xl font-bold mb-2">
        ¡Bienvenido de vuelta{user ? `, ${user.firstName}` : ""}!
      </h1>
      <p className="text-gray-300 mb-4">
        Continúa tu viaje de aprendizaje en Python. Tienes 3 cursos en progreso.
      </p>
      <div className="flex flex-wrap gap-4 mt-4">
        <button className="bg-[#5f2dee] hover:bg-[#4f25c5] text-white px-4 py-2 rounded-md flex items-center">
          Continuar Aprendiendo
        </button>
        <button className="bg-transparent border border-[#5f2dee] text-white px-4 py-2 rounded-md hover:bg-[#5f2dee]/10">
          Ver Mi Progreso
        </button>
      </div>
    </div>
  )
}
