import { Link } from "@tanstack/react-router";
import { ArrowRight, Star, Lock, CheckCircle, Users } from "lucide-react";
import FadeContent from "@/components/ui/fade-content.jsx";
import { useCourseAccess } from "@/hooks/useCourseAccess";
import { Badge } from "@/components/ui/badge";

function CourseCard({ course, isLocked, isCompleted, isEnrolled, progress_percentage }) {
  return (
    <>
      {/* Lock Overlay */}
      {isLocked && (
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm rounded-lg z-10 flex items-center justify-center">
          <div className="text-center p-4">
            <Lock className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-300 text-sm font-medium">Curso Bloqueado</p>
          </div>
        </div>
      )}

      <Link
        to={isLocked ? "#" : `/courses/${course.id}`}
        className={`block bg-primary-opaque/10 rounded-lg border shadow-lg transition-all ease-out duration-300 ${
          isLocked
            ? "border-gray-600 cursor-not-allowed"
            : "border-primary-opaque/0 hover:border-primary hover:bg-dark hover:scale-105 cursor-pointer"
        }`}
        onClick={(e) => {
          if (isLocked) {
            e.preventDefault();
          }
        }}
      >
        {/* Color bar with completion indicator */}
        <div className={`h-3 bg-gradient-to-r ${course.color_theme} relative`}>
          {isCompleted && (
            <div className="absolute right-2 top-0 bottom-0 flex items-center">
              <CheckCircle className="h-4 w-4 text-white" />
            </div>
          )}
        </div>

        <div className="p-5">
          <div className="flex items-start justify-between mb-2">
            <h3 className={`text-xl font-bold ${isLocked ? "text-gray-400" : "text-white"}`}>
              {course.title}
            </h3>
            {isEnrolled && (
              <Badge variant="secondary" className="ml-2">
                {isCompleted ? "Completado" : `${Math.round(progress_percentage)}%`}
              </Badge>
            )}
          </div>

          <p className={`text-sm mb-4 ${isLocked ? "text-gray-500" : "text-gray-400"}`}>
            {course.description}
          </p>

          <div className="grid grid-cols-2 gap-2 mb-4">
            <div className="text-sm">
              <span className={isLocked ? "text-gray-500" : "text-gray-400"}>Nivel: </span>
              <span className={isLocked ? "text-gray-400" : "text-white"}>{course.level}</span>
            </div>
            <div className="text-sm">
              <span className={isLocked ? "text-gray-500" : "text-gray-400"}>Duración: </span>
              <span className={isLocked ? "text-gray-400" : "text-white"}>{course.duration_minutes} min</span>
            </div>
            <div className="text-sm">
              <span className={isLocked ? "text-gray-500" : "text-gray-400"}>Módulos: </span>
              <span className={isLocked ? "text-gray-400" : "text-white"}>{course.total_modules}</span>
            </div>
            <div className="text-sm flex items-center">
              <span className={`mr-1 ${isLocked ? "text-gray-500" : "text-gray-400"}`}>Valoración: </span>
              <span className={`flex items-center ${isLocked ? "text-gray-400" : "text-white"}`}>
                {course.rating}
                <Star className={`h-3 w-3 ml-1 ${isLocked ? "text-gray-500" : "text-[#f2d231]"}`}
                      fill={isLocked ? "#6b7280" : "#f2d231"} />
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-2">
              <Users className={`h-4 w-4 ${isLocked ? "text-gray-500" : "text-primary"}`} />
              <span className={`text-sm ${isLocked ? "text-gray-500" : "text-gray-400"}`}>
                {course.students_count} estudiantes
              </span>
            </div>
            {!isLocked && (
              <div className="flex items-center text-primary hover:text-[#9980f2] transition-colors">
                {isEnrolled ? "Continuar curso" : "Ver curso"}
                <ArrowRight className="h-4 w-4 ml-1" />
              </div>
            )}
          </div>
        </div>
      </Link>
    </>
  );
}

export function CourseCards({ courses, progressMap = {} }) {
  const { hasAccessToCourse, loading } = useCourseAccess();

  if (loading) {
    return (
      <FadeContent blur={true} duration={500} easing="ease-out" initialOpacity={0} delay={250}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 cursor-default gap-6">
          {courses.map((course) => (
            <div key={course.id} className="bg-primary-opaque/10 rounded-lg border border-primary-opaque/0 shadow-lg animate-pulse">
              <div className="h-3 bg-gray-600"></div>
              <div className="p-5">
                <div className="h-6 bg-gray-600 rounded mb-2"></div>
                <div className="h-4 bg-gray-600 rounded mb-4"></div>
                <div className="grid grid-cols-2 gap-2 mb-4">
                  <div className="h-4 bg-gray-600 rounded"></div>
                  <div className="h-4 bg-gray-600 rounded"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </FadeContent>
    );
  }

  return (
    <FadeContent blur={true} duration={500} easing="ease-out" initialOpacity={0} delay={250}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 cursor-default gap-6">
        {courses.map((course) => {
          const accessInfo = hasAccessToCourse(course.id);
          const progress = progressMap[course.id];
          const isLocked = !accessInfo.hasAccess;
          const isCompleted = progress?.is_completed;
          const isEnrolled = !!progress;

          return (
            <div key={course.id} className="relative">
              <CourseCard
                course={course}
                isLocked={isLocked}
                isCompleted={isCompleted}
                isEnrolled={isEnrolled}
                progress_percentage={progress?.progress_percentage ?? 0}
              />
            </div>
          );
        })}
      </div>
    </FadeContent>
  );
}
