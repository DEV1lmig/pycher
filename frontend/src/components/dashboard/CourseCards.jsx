import { Link } from "@tanstack/react-router";
import { ArrowRight, Star } from "lucide-react";
import FadeContent from "@/components/ui/fade-content.jsx";

export function CourseCards({ courses }) {
  return (
    <FadeContent blur={true} duration={100} easing="ease-out" initialOpacity={0} delay={0}>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 cursor-default gap-6">
      {courses.map((course) => (
        <div
          key={course.id}
          className="bg-primary-opaque/10 rounded-lg border hover:bg-dark hover:scale-105 border-primary-opaque/0 hover:border-primary transition-all ease-out duration-300 cursor-default shadow-lg"
        >
          <div className={`h-3 bg-gradient-to-r ${course.color_theme}`}></div>
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
                <span className="text-white">{course.duration_minutes}</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-400">Módulos: </span>
                <span className="text-white">{course.total_modules}</span>
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
              <span className="text-sm text-gray-400">{course.students_count} estudiantes</span>
              <Link
                href={`/courses/${course.id}`}
                className="flex items-center text-primary hover:text-[#9980f2] transition-colors"
              >
                Ver curso <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </div>
        </div>
      ))}
    </div>
    </FadeContent>
  );
}
