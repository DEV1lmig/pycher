import { useState } from "react";
import { useParams, Link } from "@tanstack/react-router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { BookOpen, Clock, Users, Star, Home, Lock, CheckCircle, LogOut, PlusCircle } from "lucide-react";
import { ModuleCard } from "@/components/courses/ModuleCard";
import { ExamCard } from "@/components/courses/ExamCard";
import { courseDetailRoute } from "@/router";
import AnimatedContent from '../../components/ui/animated-content';
import FadeContent from "@/components/ui/fade-content";
import Waves from "@/components/ui/waves";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { useCourseAccess } from "@/hooks/useCourseAccess";
import { ConfirmationModal } from "@/components/ui/confirmationModal";
import toast from "react-hot-toast";
import { useCourseDetail, useEnrollmentActions } from "@/hooks/useContentQueries";

export default function CourseDetailPage() {
  const { courseId } = useParams({ from: courseDetailRoute.id });
  const { hasAccessToCourse, loading: courseAccessLoading } = useCourseAccess();

  // First, determine the user's enrollment status from the single source of truth.
  const courseAccessInfo = hasAccessToCourse(parseInt(courseId));
  const isUserEnrolledInThisCourse = courseAccessInfo.isEnrolled;

  // Then, pass that status to the hook that fetches course details.
  const { course, modules, courseProgress, moduleProgresses, examExercise, isLoading, error } = useCourseDetail(courseId, isUserEnrolledInThisCourse);
  const enrollmentMutation = useEnrollmentActions();

  const [modalState, setModalState] = useState({
    isOpen: false,
    actionType: null,
    title: "",
    description: "",
    confirmText: "",
    confirmVariant: "default",
  });

  const examUnlocked = !!courseProgress?.exam_unlocked;

  const handleOpenEnrollModal = () => {
    if (!course) return;
    setModalState({ isOpen: true, actionType: "enroll", title: "Confirmar Inscripción", description: `¿Quieres inscribirte en el curso "${course.title}"?`, confirmText: "Inscribirme", confirmVariant: "default" });
  };

  const handleOpenUnenrollModal = () => {
    if (!course) return;
    setModalState({ isOpen: true, actionType: "unenroll", title: "Confirmar Abandono", description: `¿Estás seguro de que quieres abandonar el curso "${course.title}"? Todo tu progreso se perderá.`, confirmText: "Abandonar Curso", confirmVariant: "destructive" });
  };

  const handleConfirmAction = async () => {
    if (!course || !modalState.actionType) return;
    enrollmentMutation.mutate({ courseId: course.id, action: modalState.actionType });
    handleCloseModal();
  };

  const handleCloseModal = () => {
    if (enrollmentMutation.isPending) return;
    setModalState({ isOpen: false, actionType: null, title: "", description: "" });
  };

  if (isLoading || courseAccessLoading) {
    return (
      <DashboardLayout>
        <div className="my-4 mx-6">
          <div className="h-6 w-48 bg-primary/30 rounded mb-4 animate-pulse" />
        </div>
        <div className="bg-dark rounded-3xl relative p-8 mb-8 shadow-3xl border-primary/5 border m-6">
          <div className="absolute rounded-3xl overflow-hidden inset-0 z-10">
            <Waves lineColor="rgba(152, 128, 242, 0.2)" backgroundColor="#160f30" waveSpeedX={0.02} waveSpeedY={0.01} waveAmpX={70} waveAmpY={20} friction={0.9} tension={0.01} maxCursorMove={60} xGap={12} yGap={36} />
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

  if (error) return <DashboardLayout><div className="p-6 text-center text-red-400">Error al cargar el curso: {error.message}</div></DashboardLayout>;
  if (!course) return <DashboardLayout><div className="p-6 text-center text-gray-400">Curso no encontrado.</div></DashboardLayout>;

  // This logic is now much simpler because the hooks are aligned.
  const isCourseCompleted = courseProgress?.is_completed;
  const isCourseLockedForDisplay = !courseAccessInfo.hasAccess && !isUserEnrolledInThisCourse;
  const overallLockReason = isCourseLockedForDisplay ? courseAccessInfo.reason : (!isUserEnrolledInThisCourse ? "Debes inscribirte en este curso para acceder a los módulos." : null);

  return (
    <DashboardLayout>
      <AnimatedContent distance={40} direction="vertical" reverse={true} config={{ tension: 100, friction: 20 }} initialOpacity={0.2} animateOpacity scale={1} threshold={0.2}>
        <div className="my-4 mx-6">
          <Breadcrumbs items={[{ label: "Inicio", href: "/home", icon: <Home size={16} /> }, { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> }, { label: course.title }]} />
        </div>
        <div className={`bg-dark rounded-3xl relative p-8 mb-8 shadow-3xl border-primary/5 border m-6 ${isCourseLockedForDisplay ? 'opacity-60' : ''}`}>
          <div className="absolute rounded-3xl overflow-hidden inset-0 z-10">
            <Waves lineColor="rgba(152, 128, 242, 0.4)" backgroundColor="#160f30" waveSpeedX={0.02} waveSpeedY={0.01} waveAmpX={70} waveAmpY={20} friction={0.9} tension={0.01} maxCursorMove={60} xGap={12} yGap={36} />
          </div>
          <div className="relative z-20">
            <div className="flex flex-col md:flex-row items-start justify-between mb-4">
              <div className="flex-grow">
                <h2 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                  {course.title}
                  {isCourseLockedForDisplay && <Lock className="h-8 w-8 text-gray-400" />}
                  {isCourseCompleted && <CheckCircle className="h-8 w-8 text-green-400" />}
                </h2>
                <p className="text-white mb-4 text-lg">{course.description}</p>
              </div>
              {isUserEnrolledInThisCourse && courseProgress && (
                <div className="bg-primary/20 rounded-lg p-4 min-w-[200px] md:ml-6 mt-4 md:mt-0">
                  <h3 className="text-white font-semibold mb-2">Tu Progreso</h3>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-300">Completado:</span>
                    <span className="text-white font-bold">{Math.round(courseProgress.progress_percentage ?? 0)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-secondary h-2 rounded-full transition-all duration-300" style={{ width: `${courseProgress.progress_percentage ?? 0}%` }} />
                  </div>
                </div>
              )}
            </div>
            {isCourseLockedForDisplay && (
              <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 text-red-400"><Lock className="h-5 w-5" /> <span className="font-semibold">Curso Bloqueado</span></div>
                <p className="text-red-300 mt-1">{courseAccessInfo.reason}</p>
              </div>
            )}
            <div className="flex flex-wrap gap-x-6 gap-y-2 mb-4">
              <div className="flex items-center gap-2 text-white"><BookOpen className="w-5 h-5 text-primary" /><span>{course.total_modules} módulos</span></div>
              <div className="flex items-center gap-2 text-white"><Clock className="w-5 h-5 text-primary" /><span>{course.duration_minutes} min</span></div>
              <div className="flex items-center gap-2 text-white"><Users className="w-5 h-5 text-primary" /><span>{course.students_count} estudiantes</span></div>
              <div className="flex items-center gap-2 text-white"><Star className="w-5 h-5 text-[#f2d231]" fill="#f2d231" /><span>{course.rating}</span></div>
            </div>
            <div className="flex flex-wrap gap-4 mt-6">
              <Button asChild variant="outline" className="border-gray-500 text-gray-300 hover:bg-gray-700 hover:text-white"><Link to="/courses">Volver a Cursos</Link></Button>
              {!isCourseLockedForDisplay && !isUserEnrolledInThisCourse && (
                <Button onClick={handleOpenEnrollModal} disabled={enrollmentMutation.isPending} className="bg-primary hover:bg-primary/80 text-white font-semibold px-6 py-2">
                  <PlusCircle className="h-5 w-5 mr-2" />
                  {enrollmentMutation.isPending ? "Inscribiendo..." : "Inscribirse al Curso"}
                </Button>
              )}
              {isUserEnrolledInThisCourse && (
                <>
                  {!isCourseCompleted && (<Button asChild variant="secondary" className="text-dark font-semibold px-6 py-2"><Link to={courseProgress?.last_accessed_module_id ? `/module/${courseProgress.last_accessed_module_id}` : (modules.length > 0 ? `/module/${modules[0].id}` : '#')}>Continuar Aprendiendo</Link></Button>)}
                  <Button variant="destructiveOutline" onClick={handleOpenUnenrollModal} disabled={enrollmentMutation.isPending} className="border-destructive bg-default text-destructive hover:bg-destructive/10">
                    <LogOut className="h-5 w-5 mr-2" />
                    {enrollmentMutation.isPending ? "Abandonando..." : "Abandonar Curso"}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </AnimatedContent>
      <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}>
        <h3 className="text-2xl font-bold text-white mx-6">{!isUserEnrolledInThisCourse ? "Contenido del curso (Bloqueado)" : "Módulos disponibles"}</h3>
        {overallLockReason && (<p className="text-sm text-gray-400 mx-6 mb-4">{overallLockReason}</p>)}
      </FadeContent>
      {modules.length === 0 && isUserEnrolledInThisCourse ? (
        <FadeContent blur={true} duration={400} easing="ease-out" initialOpacity={0} delay={100}><div className="flex justify-center p-32 text-gray-400 mx-6 mt-6">¡Oh no!, este curso aún no cuenta con módulos :(</div></FadeContent>
      ) : (
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mx-6 items-stretch ${!isUserEnrolledInThisCourse ? 'opacity-50 pointer-events-none' : ''}`}>
          {modules.map((module) => {
            // The component now simply trusts the `is_locked` property from the hook.
            const progress = moduleProgresses[module.id] || null;
            return (<ModuleCard key={module.id} module={module} progress={progress} isLocked={module.is_locked} />);
          })}
        </div>
      )}
      <ConfirmationModal isOpen={modalState.isOpen} onClose={handleCloseModal} onConfirm={handleConfirmAction} title={modalState.title} description={modalState.description} confirmButtonText={enrollmentMutation.isPending ? "Procesando..." : modalState.confirmText} cancelButtonText="Cancelar" confirmButtonVariant={modalState.confirmVariant} isConfirmDisabled={enrollmentMutation.isPending} />
      {isUserEnrolledInThisCourse && isCourseCompleted && examExercise && examUnlocked && (
        <div className="mx-6 mt-8"><ExamCard exam={examExercise} isLocked={false} /></div>
      )}
    </DashboardLayout>
  );
}
