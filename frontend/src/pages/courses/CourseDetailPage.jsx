import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "@tanstack/react-router"; // Added useNavigate
import { getCourseById, getModulesByCourseId, getCourseExamExercises } from "@/services/contentService";
import { getCourseProgressSummary, getBatchModuleProgress } from "@/services/progressService"; // Importing progress service
import { enrollInCourse, unenrollFromCourse } from "@/services/userService"; // Added unenrollFromCourse
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { BookOpen, Clock, Users, Star, Home, Lock, CheckCircle, LogOut, PlusCircle } from "lucide-react"; // Added LogOut, PlusCircle
import { ModuleCard } from "@/components/courses/ModuleCard";
import { ExamCard } from "@/components/courses/ExamCard";
import { courseDetailRoute } from "@/router";
import AnimatedContent from '../../components/ui/animated-content';
import FadeContent from "@/components/ui/fade-content";
import Waves from "@/components/ui/waves";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { useCourseAccess } from "@/hooks/useCourseAccess";
import { ConfirmationModal } from "@/components/ui/confirmationModal"; // Import the modal
import toast from "react-hot-toast"; // Assuming you use sonner for toasts

export default function CourseDetailPage() {
  const { courseId } = useParams({ from: courseDetailRoute.id });
  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [courseProgress, setCourseProgress] = useState(null);
  const [moduleProgresses, setModuleProgresses] = useState({});
  const [examExercise, setExamExercise] = useState(null);
  // const [enrolling, setEnrolling] = useState(false); // Will be handled by modalState

  const { hasAccessToCourse, getCourseProgress, refreshEnrollments, loading: courseAccessLoading } = useCourseAccess();

  const [modalState, setModalState] = useState({
    isOpen: false,
    actionType: null, // 'enroll' or 'unenroll'
    title: "",
    description: "",
    confirmText: "",
    confirmVariant: "default",
    isLoading: false,
  });

  // DRY: Extract fetch logic
  const fetchModulesAndProgress = useCallback(async () => {
    if (!courseId) return;
    const data = await getModulesByCourseId(courseId);
    let modulesArr = Array.isArray(data) ? data : data ? [data] : [];
    setModules(modulesArr);

    const moduleIds = modulesArr.map(mod => mod.id);
    const progressMap = await getBatchModuleProgress(moduleIds);

    setModuleProgresses(progressMap || {});
  }, [courseId]);

  useEffect(() => {
    getCourseById(courseId).then(setCourse);
  }, [courseId]);

  useEffect(() => {
    fetchModulesAndProgress();
    getCourseProgressSummary(courseId).then(setCourseProgress);
  }, [courseId, fetchModulesAndProgress]);

  useEffect(() => {
    if (course && modules.length > 0) {
      getCourseExamExercises(course.id)
        .then(setExamExercise)
        .catch(() => setExamExercise(null));
    }
  }, [course, modules]);


  const handleOpenEnrollModal = () => {
    if (!course) return;
    setModalState({
      isOpen: true,
      actionType: "enroll",
      title: "Confirmar Inscripción",
      description: `¿Quieres inscribirte en el curso "${course.title}"?`,
      confirmText: "Inscribirme",
      confirmVariant: "default",
      isLoading: false,
    });
  };

  const handleOpenUnenrollModal = () => {
    if (!course) return;
    setModalState({
      isOpen: true,
      actionType: "unenroll",
      title: "Confirmar Abandono",
      description: `¿Estás seguro de que quieres abandonar el curso "${course.title}"? Todo tu progreso en este curso se perderá permanentemente.`,
      confirmText: "Abandonar Curso",
      confirmVariant: "destructive",
      isLoading: false,
    });
  };

  const handleConfirmAction = async () => {
    if (!course || !modalState.actionType) return;
    setModalState(prev => ({ ...prev, isLoading: true }));

    const { actionType } = modalState;

    try {
      if (actionType === "enroll") {
        await enrollInCourse(course.id);
        toast.success(`Te has inscrito en "${course.title}" correctamente.`);
      } else if (actionType === "unenroll") {
        await unenrollFromCourse(course.id);
        toast.success(`Has abandonado el curso "${course.title}".`);
        // Optionally navigate away if they unenroll, e.g., back to courses page
        // navigate({ to: "/courses" });
      }
      await refreshEnrollments(); // Refresh data for both actions
    } catch (error) {
      console.error(`Error during ${actionType}:`, error);
      toast.error(`Error al ${actionType === "enroll" ? "inscribirse" : "abandonar"} el curso. ${error.message || ""}`);
    } finally {
      // Close modal is handled by ConfirmationModal's onConfirm, but reset loading here
      setModalState(prev => ({ ...prev, isLoading: false, isOpen: false }));
    }
  };

  const handleCloseModal = () => {
    if (modalState.isLoading) return; // Prevent closing while an action is in progress
    setModalState({ isOpen: false, actionType: null, title: "", description: "", isLoading: false });
  };


  if (!course || courseAccessLoading) {
    return (
      <DashboardLayout>
        <div className="my-4 mx-6">
          <div className="h-6 w-48 bg-primary/30 rounded mb-4 animate-pulse" />
        </div>
        <div className="bg-dark rounded-3xl relative p-8 mb-8 shadow-3xl border-primary/5 border m-6">
          <div className="absolute rounded-3xl overflow-hidden inset-0 z-10">
            <Waves
              lineColor="rgba(152, 128, 242, 0.2)"
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
            <div className="flex flex-col md:flex-row items-start justify-between mb-4">
              <div className="flex-grow">
                <div className="h-10 w-64 bg-primary/30 rounded mb-4 animate-pulse" />
                <div className="h-5 w-80 bg-primary/20 rounded mb-2 animate-pulse" />
                <div className="h-5 w-56 bg-primary/10 rounded mb-2 animate-pulse" />
              </div>
              <div className="bg-primary/10 rounded-lg p-4 min-w-[200px] md:ml-6 mt-4 md:mt-0">
                <div className="h-4 w-24 bg-primary/20 rounded mb-2 animate-pulse" />
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div className="bg-secondary h-2 rounded-full animate-pulse" style={{ width: `40%` }} />
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-2 mb-4">
              <div className="h-5 w-32 bg-primary/20 rounded animate-pulse" />
              <div className="h-5 w-24 bg-primary/20 rounded animate-pulse" />
              <div className="h-5 w-28 bg-primary/20 rounded animate-pulse" />
              <div className="h-5 w-20 bg-primary/20 rounded animate-pulse" />
            </div>
            <div className="flex gap-4 mt-6">
              <div className="h-10 w-40 bg-primary/20 rounded animate-pulse" />
              <div className="h-10 w-56 bg-primary/20 rounded animate-pulse" />
            </div>
          </div>
        </div>
        <div className="mx-6">
          <div className="h-8 w-64 bg-primary/20 rounded mb-4 animate-pulse" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-dark rounded-xl p-6 shadow-lg animate-pulse h-40" />
            ))}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const courseAccessInfo = hasAccessToCourse(parseInt(courseId));
  const userCourseProgress = getCourseProgress(parseInt(courseId));

  const isCourseLockedByPrerequisite = !courseAccessInfo.hasAccess;
  const isUserEnrolledInThisCourse = !!userCourseProgress;
  const isCourseCompleted = userCourseProgress?.is_completed;

  // Modules are effectively locked if the course has prerequisites not met OR if the user is not enrolled
  const allModulesLockedDueToCourse = isCourseLockedByPrerequisite || !isUserEnrolledInThisCourse;
  const overallLockReason = isCourseLockedByPrerequisite ? courseAccessInfo.reason : (!isUserEnrolledInThisCourse ? "Debes inscribirte en este curso para acceder a los módulos." : null);


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

        <div className={`bg-dark rounded-3xl relative p-8 mb-8 shadow-3xl border-primary/5 border m-6 ${isCourseLockedByPrerequisite && !isUserEnrolledInThisCourse ? 'opacity-60' : ''}`}>
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
            <div className="flex flex-col md:flex-row items-start justify-between mb-4">
              <div className="flex-grow">
                <h2 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                  {course.title}
                  {isCourseLockedByPrerequisite && !isUserEnrolledInThisCourse && <Lock className="h-8 w-8 text-gray-400" />}
                  {isCourseCompleted && <CheckCircle className="h-8 w-8 text-green-400" />}
                </h2>
                <p className="text-white mb-4 text-lg">{course.description}</p>
              </div>

              {isUserEnrolledInThisCourse && courseProgress && (
                <div className="bg-primary/20 rounded-lg p-4 min-w-[200px] md:ml-6 mt-4 md:mt-0">
                  <h3 className="text-white font-semibold mb-2">Tu Progreso</h3>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-300">Completado:</span>
                    <span className="text-white font-bold">{Math.round(courseProgress.progress_percentage)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-secondary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${courseProgress.progress_percentage}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>

            {isCourseLockedByPrerequisite && !isUserEnrolledInThisCourse && (
              <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 text-red-400">
                  <Lock className="h-5 w-5" />
                  <span className="font-semibold">Curso Bloqueado</span>
                </div>
                <p className="text-red-300 mt-1">{courseAccessInfo.reason}</p>
              </div>
            )}

            <div className="flex flex-wrap gap-x-6 gap-y-2 mb-4">
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

            <div className="flex flex-wrap gap-4 mt-6">
              <Button asChild variant="outline" className="border-gray-500 text-gray-300 hover:bg-gray-700 hover:text-white">
                <Link to="/courses">
                  Volver a Cursos
                </Link>
              </Button>

              {!isCourseLockedByPrerequisite && !isUserEnrolledInThisCourse && (
                <Button
                  onClick={handleOpenEnrollModal}
                  disabled={modalState.isLoading && modalState.actionType === 'enroll'}
                  className="bg-primary hover:bg-primary/80 text-white font-semibold px-6 py-2"
                >
                  <PlusCircle className="h-5 w-5 mr-2" />
                  {modalState.isLoading && modalState.actionType === 'enroll' ? "Inscribiendo..." : "Inscribirse al Curso"}
                </Button>
              )}

              {isUserEnrolledInThisCourse && (
                <>
                  {!isCourseCompleted && (
                    <Button asChild variant="secondary" className="text-dark font-semibold px-6 py-2">
                      <Link
                        to={userCourseProgress?.last_accessed_module_id ? `/module/${userCourseProgress.last_accessed_module_id}` : (modules.length > 0 ? `/module/${modules[0].id}` : '#')}
                      >
                        Continuar Aprendiendo
                      </Link>
                    </Button>
                  )}
                  <Button
                    variant="destructiveOutline" // You might need to define this variant or use "outline" and style it
                    onClick={handleOpenUnenrollModal}
                    disabled={modalState.isLoading && modalState.actionType === 'unenroll'}
                    className="border-destructive bg-default text-destructive hover:bg-destructive/10"
                  >
                    <LogOut className="h-5 w-5 mr-2" />
                    {modalState.isLoading && modalState.actionType === 'unenroll' ? "Abandonando..." : "Abandonar Curso"}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
        <h3 className="text-2xl font-bold text-white mx-6">
          {allModulesLockedDueToCourse ? "Contenido del curso (Bloqueado)" : "Módulos disponibles"}
        </h3>
        {allModulesLockedDueToCourse && overallLockReason && (
            <p className="text-sm text-gray-400 mx-6 mb-4">{overallLockReason}</p>
        )}
      </FadeContent>

      {modules.length === 0 && !allModulesLockedDueToCourse ? (
        <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
          <div className="flex justify-center p-32 text-gray-400 mx-6 mt-6">
            ¡Oh no!, este curso aún no cuenta con módulos :(
          </div>
        </FadeContent>
      ) : (
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mx-6 items-stretch ${allModulesLockedDueToCourse ? 'opacity-50 pointer-events-none' : ''}`}>
          {modules.map((module) => {
  // Use is_locked from the module object returned by getModulesByCourseId
  const isLocked = allModulesLockedDueToCourse || module.is_locked;
  const progress = moduleProgresses[module.id] || null;
  return (
      <ModuleCard
      key={module.id}
      module={module}
      progress={progress}
      isLocked={isLocked}
      />
  );
})}
        </div>
      )}
       <ConfirmationModal
        isOpen={modalState.isOpen}
        onClose={handleCloseModal}
        onConfirm={handleConfirmAction}
        title={modalState.title}
        description={modalState.description}
        confirmButtonText={modalState.isLoading ? "Procesando..." : modalState.confirmText}
        cancelButtonText="Cancelar"
        confirmButtonVariant={modalState.confirmVariant}
        isConfirmDisabled={modalState.isLoading}
      />

      {/* After the modules grid */}
      {isUserEnrolledInThisCourse && isCourseCompleted && examExercise && (
        <div className="mx-6 mt-8">
          <ExamCard exam={examExercise} isLocked={false} />
        </div>
      )}
    </DashboardLayout>
  );
}
