import { useEffect, useState } from "react"
import { getUserProfile } from "@/services/userService"
import AnimatedContent from '../ui/animated-content'

export function WelcomeHeader() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    getUserProfile().then(setUser)
  }, [])

  return (
    <AnimatedContent
          distance={40}
          direction="vertical"
          reverse={true}
          config={{ tension: 100, friction: 20 }}
          initialOpacity={0.2}
          animateOpacity
          scale={1}
          threshold={0.2}
        >
    <div className="bg-gradient-to-r from-[#312a56] to-[#1a1433] rounded-lg p-6">
      <h1 className="text-3xl font-bold mb-2">
        ¡Bienvenido de vuelta, {user ? `${user.first_name}` : "Carlos Rodríguez"}!
      </h1>
      <p className="text-gray-300 mb-4">
        Continúa tu viaje de aprendizaje en Python. Tienes 3 cursos en progreso.
      </p>
      <div className="flex flex-wrap gap-4 mt-4">
        <button className="bg-primary hover:bg-primary-opaque transition ease-out duration-300 text-white px-4 py-2 rounded-md flex items-center">
          Continuar aprendiendo
        </button>
        <button className="bg-secondary text-dark  px-4 py-2 rounded-md hover:bg-secondary/80 hover:text-dark transition ease-out duration-300">
          Ver mi progreso
        </button>
      </div>
    </div>
    </AnimatedContent>
  )
}
