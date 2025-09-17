import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, Link } from "@tanstack/react-router";
import { getCourseById, getModulesByCourseId } from "@/services/contentService";
import { enrollInCourse } from "@/services/progressService";
import { unenrollFromCourse } from "@/services/userService";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import {
  BookOpen,
  Clock,
  Users,
  Star,
  Home,
  Lock,
  CheckCircle,
  LogOut,
  PlusCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { ModuleCard } from "@/components/courses/ModuleCard";
import { ExamStatusCard } from "@/components/courses/ExamStatusCard";
import { courseDetailRoute } from "@/router";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { useCourseAccess } from "@/hooks/useCourseAccess";
import { ConfirmationModal } from "@/components/ui/confirmationModal";
import toast from "react-hot-toast";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { getBatchModuleProgress } from "@/services/progressService";
import AnimatedContent from "@/components/ui/animated-content";
import Particles from "@/components/ui/particles";
import BlurText from "@/components/ui/blur-text";


export default function CourseDetailPage() {
  const { courseId } = useParams({ from: courseDetailRoute.id });
  const [course, setCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [moduleProgresses, setModuleProgresses] = useState({});
  const [examModule, setExamModule] = useState(null);
  const [examUnlocked, setExamUnlocked] = useState(false);
  const [isHeaderCollapsed, setIsHeaderCollapsed] = useState(false);

  const { hasAccessToCourse, getCourseProgress, refreshEnrollments, loading: courseAccessLoading } = useCourseAccess();
  const userCourseProgress = getCourseProgress(parseInt(courseId));

  const [modalState, setModalState] = useState({
    isOpen: false,
    actionType: null,
    title: "",
    description: "",
    confirmText: "",
    confirmVariant: "default",
    isLoading: false,
  });

  const fetchModulesAndProgress = useCallback(async () => {
    if (!courseId) return;
    const allCourseModules = await getModulesByCourseId(courseId);
    const exam = allCourseModules.find(mod => mod.is_exam);
    const contentModules = allCourseModules.filter(mod => !mod.is_exam);

    setModules(contentModules);
    setExamModule(exam || null);

    const moduleIds = contentModules.map(mod => mod.id);
    if (moduleIds.length > 0) {
      const progressMap = await getBatchModuleProgress(moduleIds);
      setModuleProgresses(progressMap || {});
    } else {
      setModuleProgresses({});
    }
  }, [courseId]);

  const courseIdNum = parseInt(courseId, 10);
  const courseAccessInfo = useMemo(() => hasAccessToCourse(courseIdNum), [hasAccessToCourse, courseIdNum]);
  const isCourseLockedByPrerequisite = useMemo(() => !courseAccessInfo.hasAccess, [courseAccessInfo]);
  const isUserEnrolledInThisCourse = useMemo(() => !!userCourseProgress && userCourseProgress.is_active_enrollment, [userCourseProgress]);
  const isCourseCompleted = useMemo(() => userCourseProgress?.is_completed, [userCourseProgress]);
  const allModulesLockedDueToCourse = useMemo(() => isCourseLockedByPrerequisite || !isUserEnrolledInThisCourse, [isCourseLockedByPrerequisite, isUserEnrolledInThisCourse]);

  useEffect(() => {
    getCourseById(courseId).then(setCourse);
    fetchModulesAndProgress();
  }, [courseId, fetchModulesAndProgress]);

  useEffect(() => {
    if (userCourseProgress) {
      setExamUnlocked(!!userCourseProgress.exam_unlocked);
    } else {
      setExamUnlocked(false);
    }
  }, [userCourseProgress]);

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
      }
      await refreshEnrollments();
    } catch (error) {
      toast.error(`Error al ${actionType === "enroll" ? "inscribirse" : "abandonar"} el curso. ${error.message || ""}`);
    } finally {
      setModalState(prev => ({ ...prev, isLoading: false, isOpen: false }));
    }
  };

  const handleCloseModal = () => {
    if (modalState.isLoading) return;
    setModalState({ isOpen: false, actionType: null, title: "", description: "", isLoading: false });
  };

  if (!course || courseAccessLoading) {
    return (
        <DashboardLayout>
            <div className="p-4">
                <div className="h-8 w-1/2 bg-dark-light rounded animate-pulse mb-4"></div>
                <div className="h-24 w-full bg-dark-light rounded animate-pulse"></div>
            </div>
        </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="h-screen flex flex-col overflow-hidden bg-dark">
        {/* Animated Header */}
        <div className="flex-shrink-0 p-4">
          <div className="flex items-center justify-between mb-4">
            <Breadcrumbs
              items={[
                { label: "Inicio", href: "/home", icon: <Home size={14} /> },
                { label: "Cursos", href: "/courses", icon: <BookOpen size={14} /> },
                { label: course.title },
              ]}
            />
            <Button variant="ghost" size="sm" onClick={() => setIsHeaderCollapsed(!isHeaderCollapsed)}>
              {isHeaderCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            </Button>
          </div>

          {!isHeaderCollapsed && (
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
              <div className="bg-dark shadow-2xl border-primary/5 border py-8 relative overflow-hidden rounded-lg p-6 cursor-default">
                <div className="absolute inset-0 z-10">
                  <Particles
                    particleColors={["#8363f2", "#f2d231", "#a5a5a5"]}
                    particleCount={200}
                    particleSpread={8}
                    speed={0.2}
                    particleBaseSize={60}
                    moveParticlesOnHover={true}
                    alphaParticles={false}
                    disableRotation={true}
                  />
                </div>

                <div className="relative z-20">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Course Info */}
                    <div className="lg:col-span-2">
                      <div className="flex items-start gap-4">
                        <div className="flex-1">
                          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
                            <BlurText text={course.title} animateBy="words" delay={100} className="inline" />
                            {isCourseLockedByPrerequisite && <Lock className="h-6 w-6 text-gray-400" />}
                            {isCourseCompleted && <CheckCircle className="h-6 w-6 text-green-400" />}
                          </h1>

                          <p className="text-gray-300 mb-4 line-clamp-2">{course.description}</p>

                          <div className="flex flex-wrap gap-3 text-sm">
                            <Badge variant="secondary" className="flex items-center gap-1 bg-primary/20 text-primary border-primary/30 backdrop-blur-sm">
                              <BookOpen className="w-3 h-3" />
                              {course.total_modules} módulos
                            </Badge>
                            <Badge variant="secondary" className="flex items-center gap-1 bg-primary/20 text-primary border-primary/30 backdrop-blur-sm">
                              <Clock className="w-3 h-3" />
                              {course.duration_minutes} min
                            </Badge>
                            <Badge variant="secondary" className="flex items-center gap-1 bg-primary/20 text-primary border-primary/30 backdrop-blur-sm">
                              <Users className="w-3 h-3" />
                              {course.students_count} estudiantes
                            </Badge>
                            <Badge variant="secondary" className="flex items-center gap-1 bg-secondary/20 text-secondary border-secondary/30 backdrop-blur-sm">
                              <Star className="w-3 h-3" fill="currentColor" />
                              {course.rating}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Progress & Actions */}
                    <div className="space-y-4">
                      {isUserEnrolledInThisCourse && userCourseProgress && (
                        <Card className="bg-primary/20 border-primary/30 backdrop-blur-sm">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-sm text-gray-300">Progreso del curso:</span>
                              <span className="text-lg font-bold text-white">
                                {Math.round(userCourseProgress.progress_percentage ?? 0)}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-700/50 rounded-full h-3">
                              <div
                                className="bg-secondary h-3 rounded-full transition-all duration-500"
                                style={{ width: `${userCourseProgress.progress_percentage ?? 0}%` }}
                              />
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      <div className="inline-flex flex-wrap gap-3">
                        <Button asChild variant="outline" size="sm" className="bg-transparent border-primary/30 text-primary hover:bg-primary/10 backdrop-blur-sm">
                           <Link to="/courses">Volver a cursos</Link>
                        </Button>

                        {!isCourseLockedByPrerequisite && !isUserEnrolledInThisCourse && (
                          <Button size="sm" className="bg-primary hover:bg-primary-opaque transition ease-out duration-300 text-white" onClick={handleOpenEnrollModal}>
                            <PlusCircle className="h-4 w-4 mr-2" />
                            Inscribirse al curso
                          </Button>
                        )}

                        {isUserEnrolledInThisCourse && (
                          <>
                            {!isCourseCompleted && (
                               <Button asChild className="bg-secondary text-dark hover:bg-secondary/90 transition ease-out duration-300" size="sm">
                                  <Link to={userCourseProgress?.last_accessed_module_id ? `/module/${userCourseProgress.last_accessed_module_id}` : (modules.length > 0 ? `/module/${modules[0].id}` : '#')}>
                                      Continuar aprendiendo
                                  </Link>
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              className="border-red-500/30 text-red-500 hover:bg-red-500/10 bg-transparent backdrop-blur-sm"
                              onClick={handleOpenUnenrollModal}
                            >
                              <LogOut className="h-4 w-4 mr-2" />
                              Abandonar curso
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </AnimatedContent>
          )}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden">
          <Tabs defaultValue="modules" className="h-full flex flex-col">
            <TabsList className="flex-shrink-0 mx-4 mt-4 bg-dark-light">
              <TabsTrigger value="modules">Módulos ({modules.length})</TabsTrigger>
              {examModule && <TabsTrigger value="exam">Examen Final</TabsTrigger>}
            </TabsList>

            <TabsContent value="modules" className="flex-1 overflow-auto p-4 mt-0">
              <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 ${allModulesLockedDueToCourse ? 'opacity-50 pointer-events-none' : ''}`}>
                {modules.map((module) => {
                  const progress = moduleProgresses[module.id] || null;
                  const isLocked = allModulesLockedDueToCourse || module.is_locked;
                  return <ModuleCard key={module.id} module={module} progress={progress} isLocked={isLocked} />;
                })}
              </div>
            </TabsContent>

            {examModule && (
                <TabsContent value="exam" className="flex-1 overflow-auto p-4 mt-0">
                    <div className="max-w-md">
                        <ExamStatusCard
                            examExercise={examModule}
                            isUnlocked={examUnlocked}
                            isCompleted={isCourseCompleted}
                            courseId={courseId}
                        />
                    </div>
                </TabsContent>
            )}
          </Tabs>
        </div>
      </div>
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
    </DashboardLayout>
  );
}
