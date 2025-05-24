import { useEffect, useState } from "react";
import { useParams, Link } from "@tanstack/react-router";
import { getCourseById, getModulesByCourseId } from "@/services/contentService";
import { enrollInCourse, checkCourseAccess } from "@/services/userService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { BookOpen, Clock, Users, Star, Home, Lock, CheckCircle } from "lucide-react";
import { ModuleCard } from "@/components/courses/ModuleCard";
import { courseDetailRoute } from "@/router";
import AnimatedContent from '../../components/ui/animated-content';
import FadeContent from "@/components/ui/fade-content";
import Waves from "@/components/ui/waves";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { useCourseAccess } from "@/hooks/useCourseAccess";

export default function CourseDetailPage() {
  const { courseId } = useParams({ from: courseDetailRoute.id });
  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [enrolling, setEnrolling] = useState(false);

  const { hasAccessToCourse, getCourseProgress, refreshEnrollments, loading: courseAccessLoading } = useCourseAccess(); // Added loading state

  useEffect(() => {
    getCourseById(courseId).then(setCourse);
  }, [courseId]);

  useEffect(() => {
    if (!courseId) return;
    getModulesByCourseId(courseId)
      .then(data => {
        if (Array.isArray(data)) setModules(data);
        else if (data) setModules([data]);
        else setModules([]);
      })
      .catch(() => setModules([]));
  }, [courseId]);

  const handleEnrollment = async () => {
    setEnrolling(true);
    try {
      await enrollInCourse(courseId);
      await refreshEnrollments(); // Ensure enrollments are refreshed
    } catch (error) {
      console.error('Error enrolling in course:', error);
      // Add user feedback here, e.g., a toast notification
    } finally {
      setEnrolling(false);
    }
  };

  if (!course || courseAccessLoading) return <div className="text-white p-8 text-center">Cargando detalles del curso...</div>; // Improved loading state

  const courseAccessInfo = hasAccessToCourse(parseInt(courseId));
  const userCourseProgress = getCourseProgress(parseInt(courseId));

  const isCourseLockedByPrerequisite = !courseAccessInfo.hasAccess;
  const isUserEnrolledInThisCourse = !!userCourseProgress;
  const isCourseCompleted = userCourseProgress?.is_completed;

  // Modules are effectively locked if the course has prerequisites not met OR if the user is not enrolled
  const modulesEffectivelyLocked = isCourseLockedByPrerequisite || !isUserEnrolledInThisCourse;
  const displayLockReason = isCourseLockedByPrerequisite ? courseAccessInfo.reason : (!isUserEnrolledInThisCourse ? "Debes inscribirte en este curso para acceder a los módulos." : null);

  return (
    <DashboardLayout>
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
        <div className="my-4 mx-6">
          <Breadcrumbs
            items={[
              { label: "Inicio", href: "/home", icon: <Home size={16} /> },
              { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> },
              { label: course.title },
            ]}
          />
        </div>

        <div className={`bg-dark rounded-3xl relative p-8 mb-8 shadow-3xl border-primary/5 border m-6 ${isCourseLockedByPrerequisite ? 'opacity-60' : ''}`}>
          <div className="absolute rounded-3xl overflow-hidden inset-0 z-10">
            <Waves
              lineColor="rgba(152, 128, 242, 0.4)"
              backgroundColor="#160f30"
              waveSpeedX={0.02}
              waveSpeedY={0.01}
              waveAmpX={70}
              waveAmpY={20}
              friction={0.9}
              tension={0.01}
              maxCursorMove={60}
              xGap={12}
              yGap={36}
            />
          </div>

          <div className="relative z-20">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                  {course.title}
                  {isCourseLockedByPrerequisite && <Lock className="h-8 w-8 text-gray-400" />}
                  {isCourseCompleted && <CheckCircle className="h-8 w-8 text-green-400" />}
                </h2>
                <p className="text-white mb-4 text-lg">{course.description}</p>
              </div>

              {isUserEnrolledInThisCourse && userCourseProgress && (
                <div className="bg-primary/20 rounded-lg p-4 min-w-[200px]">
                  <h3 className="text-white font-semibold mb-2">Tu Progreso</h3>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-300">Completado:</span>
                    <span className="text-white font-bold">{Math.round(userCourseProgress.progress_percentage)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-secondary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${userCourseProgress.progress_percentage}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>

            {isCourseLockedByPrerequisite && (
              <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 text-red-400">
                  <Lock className="h-5 w-5" />
                  <span className="font-semibold">Curso Bloqueado</span>
                </div>
                <p className="text-red-300 mt-1">{courseAccessInfo.reason}</p>
              </div>
            )}

            <div className="flex flex-wrap gap-6 mb-4">
              <div className="flex items-center gap-2 text-white">
                <BookOpen className="w-5 h-5 text-primary" />
                <span>{course.total_modules} módulos</span>
              </div>
              <div className="flex items-center gap-2 text-white">
                <Clock className="w-5 h-5 text-primary" />
                <span>{course.duration_minutes} min</span>
              </div>
              <div className="flex items-center gap-2 text-white">
                <Users className="w-5 h-5 text-primary" />
                <span>{course.students_count} estudiantes</span>
              </div>
              <div className="flex items-center gap-2 text-white">
                <Star className="w-5 h-5 text-[#f2d231]" fill="#f2d231" />
                <span>{course.rating}</span>
              </div>
            </div>

            <div className="flex gap-4 mt-4">
              <Link
                to="/courses"
                className="bg-gray-600 hover:bg-gray-500 text-white font-semibold px-4 py-2 rounded-md transition-colors"
              >
                Volver a Cursos
              </Link>

              {!isCourseLockedByPrerequisite && !isUserEnrolledInThisCourse && (
                <Button
                  onClick={handleEnrollment}
                  disabled={enrolling}
                  className="bg-primary hover:bg-primary/80 text-white font-semibold px-6 py-2"
                >
                  {enrolling ? "Inscribiendo..." : "Inscribirse al Curso"}
                </Button>
              )}

              {isUserEnrolledInThisCourse && !isCourseCompleted && (
                <Link
                  // Link to the first module or last accessed module/lesson if available
                  to={userCourseProgress?.last_accessed_module_id ? `/module/${userCourseProgress.last_accessed_module_id}` : `/courses/${courseId}/modules`}
                  className="bg-secondary hover:bg-secondary/80 text-dark font-semibold px-4 py-2 rounded-md transition-colors"
                >
                  Continuar Aprendiendo
                </Link>
              )}
            </div>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
        <h3 className="text-2xl font-bold text-white mx-6">
          {modulesEffectivelyLocked ? "Contenido del curso (Bloqueado)" : "Módulos disponibles"}
        </h3>
        {modulesEffectivelyLocked && displayLockReason && (
            <p className="text-sm text-gray-400 mx-6 mb-4">{displayLockReason}</p>
        )}
      </FadeContent>

      {modules.length === 0 ? (
        <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
          <div className="flex justify-center p-32 text-gray-400 mx-6 mt-6">
            ¡Oh no!, este curso aún no cuenta con módulos :(
          </div>
        </FadeContent>
      ) : (
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mx-6 items-stretch ${modulesEffectivelyLocked ? 'opacity-50 pointer-events-none' : ''}`}>
          {modules.map((module) => (
            <ModuleCard
              key={module.id}
              module={module}
              // Find specific module progress if available, otherwise pass null
              progress={userCourseProgress?.modules_progress?.find(mp => mp.module_id === module.id) || null}
              isLocked={modulesEffectivelyLocked} // Pass the effective lock status for modules
            >
              {/* Children for ModuleCard, e.g., a button, are handled inside ModuleCard based on its own isLocked prop */}
            </ModuleCard>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
