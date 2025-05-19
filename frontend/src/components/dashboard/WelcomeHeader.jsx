import { useEffect, useState } from "react"
import { getUserProfile } from "@/services/userService"
import AnimatedContent from '../ui/animated-content'
import Particles from "../ui/particles";

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
          config={{ tension: 100, friction: 10 }}
          initialOpacity={0.2}
          animateOpacity
          scale={1}
          threshold={0.2}
        >
    <div className="bg-dark shadow-2xl border-primary/5 border py-12 relative overflow-hidden rounded-lg p-6 cursor-default">
    <div className="absolute inset-0 z-10">
      <Particles
              particleColors={['#8363f2', '#8363f2']}
              particleCount={300}
              particleSpread={5}
              speed={0.2}
              particleBaseSize={70}
              moveParticlesOnHover={false}
              alphaParticles={false}
              disableRotation={true}
            />
    </div>
    <div className="relative z-20">
      <h1 className="text-3xl font-bold mb-2  relative text-white">
        ¡Bienvenido de vuelta, {user ? `${user.first_name}` : "Carlos Rodríguez"}!
      </h1>
      <p className="text-gray-300 mb-4">
        Continúa tu viaje de aprendizaje en Python. Tienes 3 cursos en progreso.
      </p>
      <div className="flex flex-wrap gap-4 mt-4">
        <button className="bg-primary hover:bg-primary-opaque transition ease-out duration-300 text-white px-4 py-2 rounded-md flex items-center">
          Continuar aprendiendo
        </button>
        <button className="bg-secondary text-dark  px-4 py-2 rounded-md hover:bg-secondary hover:text-dark transition ease-out duration-300">
          Ver mi progreso
        </button>
      </div>
      </div>
    </div>
    </AnimatedContent>
  )
}
