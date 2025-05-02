import { Link } from "@tanstack/react-router";
import { ArrowRight, Star } from "lucide-react"

export function CourseCards() {
  const courses = [
    {
      id: "python-basico",
      title: "Python Básico",
      description: "Aprende los fundamentos de Python, sintaxis básica y estructuras de datos.",
      level: "Principiante",
      duration: "20 horas",
      modules: 8,
      rating: 4.8,
      students: 1245,
      image: "/placeholder.svg?height=200&width=400",
      color: "from-[#5f2dee] to-[#9980f2]",
    },
    {
      id: "python-intermedio",
      title: "Python Intermedio",
      description: "Profundiza en Python con programación orientada a objetos y manejo de errores.",
      level: "Intermedio",
      duration: "25 horas",
      modules: 10,
      rating: 4.7,
      students: 892,
      image: "/placeholder.svg?height=200&width=400",
      color: "from-[#312a56] to-[#5f2dee]",
    },
    {
      id: "python-avanzado",
      title: "Python Avanzado",
      description: "Domina temas avanzados como concurrencia, metaprogramación y optimización.",
      level: "Avanzado",
      duration: "30 horas",
      modules: 12,
      rating: 4.9,
      students: 567,
      image: "/placeholder.svg?height=200&width=400",
      color: "from-[#f2d231] to-[#f2a531]",
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {courses.map((course) => (
        <div
          key={course.id}
          className="bg-[#1a1433] rounded-lg overflow-hidden border border-[#312a56] hover:border-[#5f2dee] transition-all hover:shadow-lg hover:shadow-[#5f2dee]/20"
        >
          <div className={`h-3 bg-gradient-to-r ${course.color}`}></div>
          <div className="p-5">
            <h3 className="text-xl font-bold mb-2">{course.title}</h3>
            <p className="text-gray-400 text-sm mb-4">{course.description}</p>

            <div className="grid grid-cols-2 gap-2 mb-4">
              <div className="text-sm">
                <span className="text-gray-400">Nivel: </span>
                <span className="text-white">{course.level}</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-400">Duración: </span>
                <span className="text-white">{course.duration}</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-400">Módulos: </span>
                <span className="text-white">{course.modules}</span>
              </div>
              <div className="text-sm flex items-center">
                <span className="text-gray-400 mr-1">Valoración: </span>
                <span className="text-white flex items-center">
                  {course.rating}
                  <Star className="h-3 w-3 text-[#f2d231] ml-1" fill="#f2d231" />
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-gray-400">{course.students} estudiantes</span>
              <Link
                href={`/dashboard/courses/${course.id}`}
                className="flex items-center text-[#5f2dee] hover:text-[#9980f2] transition-colors"
              >
                Ver curso <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
