import { useEffect, useState } from "react";
import { useParams, useNavigate } from "@tanstack/react-router";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getModuleById, getCourseById, getCourseExamExercises } from "@/services/contentService";
import LessonCodeExecutor from "@/components/editor/LessonCodeExecutor";
import { LessonWithCodeRoute, ExamRoute } from "@/router";
import Waves from "@/components/ui/waves";
import AnimatedContent from "@/components/ui/animated-content";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen, ArrowRight, CheckCircle, Loader2, AlertCircle, BookText, ArrowRightCircle } from "lucide-react";
import LessonChatDrawer from "@/components/ai/LessonChatDrawer";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useLessonDetail } from '@/hooks/useLessonDetail';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "react-hot-toast";

export default function LessonWithCodePage() {
  let lessonId, courseId;
  try {
    // Try to get lessonId from the lesson route context
    // eslint-disable-next-line react-hooks/rules-of-hooks
    lessonId = useParams({ from: LessonWithCodeRoute.id }).lessonId;
  } catch {
    lessonId = undefined;
  }
  try {
    // Try to get courseId from the exam route context
    // eslint-disable-next-line react-hooks/rules-of-hooks
    courseId = useParams({ from: ExamRoute.id }).courseId;
  } catch {
    courseId = undefined;
  }
  const navigate = useNavigate();



  // Exam mode if courseId is present and lessonId is not
  const isExamMode = !!courseId && !lessonId;

  // Lesson detail hook (only used if lessonId is present)
  const {
    lesson,
    exercises,
    isLessonCompleted,
    getExerciseProgress,
    loading: lessonDetailLoading,
    error: lessonDetailError,
    submittingExerciseId,
    submitExercise: submitExerciseFromHook,
    nextLessonInfo,
  } = useLessonDetail(lessonId);

  const [module, setModule] = useState(null);
  const [course, setCourse] = useState(null);
  const [breadcrumbLoading, setBreadcrumbLoading] = useState(true);
  const [userStdin, setUserStdin] = useState("");
  const [examExercise, setExamExercise] = useState(null);
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);
  useEffect(() => {
    if (lesson?.module_id) {
      setBreadcrumbLoading(true);
      getModuleById(lesson.module_id)
        .then(moduleData => {
          setModule(moduleData);
          if (moduleData?.course_id) {
            return getCourseById(moduleData.course_id).then(courseData => {
              setCourse(courseData);
            });
          }
        })
        .catch(err => {
          console.error("Error fetching module/course for breadcrumbs:", err);
        })
        .finally(() => setBreadcrumbLoading(false));
    } else if (lesson) {
      setBreadcrumbLoading(false);
    }
  }, [lesson]);

  // Fetch exam exercise if in exam mode
  useEffect(() => {
    if (isExamMode) {
      getCourseExamExercises(courseId).then(setExamExercise);
    }
  }, [isExamMode, courseId]);

  // Determine the current exercise
  let currentExercise = null;
  if (isExamMode && examExercise) {
    currentExercise = examExercise;
  } else if (exercises && exercises.length > 0) {
    currentExercise = exercises[0];
  }
useEffect(() => {
  setUserStdin("");
}, [currentExercise?.id]);
  const currentExerciseProgress = currentExercise && getExerciseProgress
    ? getExerciseProgress(currentExercise.id)
    : null;
  const isCurrentExerciseCorrect = currentExerciseProgress?.is_correct || false;

  const exerciseNeedsInput = !!(
    currentExercise &&
    currentExercise.validation_rules &&
    currentExercise.validation_rules.requires_input_function
  );

  const handleCodeSubmit = async (codeToSubmit) => {
    if (!currentExercise) {
      toast.error("No hay ejercicio seleccionado para enviar.");
      return;
    }
    try {
      const submissionResult = await submitExerciseFromHook(currentExercise.id, codeToSubmit, userStdin);
      return submissionResult;
    } catch (error) {
      console.error("Failed to submit exercise from page:", error);
    }
  };

  if (!isExamMode && (lessonDetailLoading || (lesson && breadcrumbLoading))) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          <Loader2 className="h-8 w-8 animate-spin mr-3" />
          Cargando lección...
        </div>
      </DashboardLayout>
    );
  }

  if (!isExamMode && lessonDetailError) {
    return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-red-400">
          <AlertCircle className="h-12 w-12 mb-4" />
          {lessonDetailError}
        </div>
      </DashboardLayout>
    );
  }

  if (!isExamMode && !lesson) {
    return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-gray-400">
          <AlertCircle className="h-12 w-12 mb-4" />
          Lección no encontrada o no se pudo cargar.
        </div>
      </DashboardLayout>
    );
  }

  // Breadcrumbs
  const breadcrumbs = [
    { label: "Inicio", href: "/home", icon: <Home size={16} /> },
    { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> },
  ];
  if (isExamMode) {
    breadcrumbs.push({ label: "Examen Final" });
  } else {
    if (course) breadcrumbs.push({ label: course.title, href: `/courses/${course.id}` });
    if (module) breadcrumbs.push({ label: module.title, href: `/module/${module.id}` });
    if (lesson) breadcrumbs.push({ label: lesson.title });
  }

  return (
    <DashboardLayout>
      <div className="my-4 mx-6">
        <Breadcrumbs items={breadcrumbs.filter(Boolean)} />
      </div>
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
        <div className="relative rounded-lg p-8 mx-6 my-6 shadow-2xl border border-primary-opaque/0">
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
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">
                  {isExamMode
                    ? examExercise?.title || "Examen Final"
                    : lesson?.title}
                </h1>
                <div className="text-gray-400 mb-4 prose prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {isExamMode
                      ? examExercise?.description || ""
                      : lesson?.description || ""}
                  </ReactMarkdown>
                </div>
              </div>
              <div className="flex flex-col md:items-end md:justify-end gap-2">
                {!isExamMode && isLessonCompleted && (
                  <div className="flex items-center text-green-400 bg-green-900/50 px-3 py-1 rounded-md mb-1 md:mb-0">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    <span>Lección Completada</span>
                  </div>
                )}
                {/* Move Next Lesson Button to header */}
                {isLessonCompleted && nextLessonInfo && (
                  <Button
                    onClick={() => {
                      if (nextLessonInfo && nextLessonInfo.id) {
                        navigate({ to: `/lessons/$lessonId`, params: { lessonId: nextLessonInfo.id.toString() } });
                      } else {
                        console.warn("Next lesson ID is missing, cannot navigate.", nextLessonInfo);
                        toast.error("No se pudo determinar la siguiente lección.");
                      }
                    }}
                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg text-base mt-2 md:mt-0"
                    size="lg"
                  >
                    <ArrowRightCircle className="mr-2 h-5 w-5" />
                    Siguiente Lección: {nextLessonInfo.title || "Siguiente"}
                  </Button>
                )}
                {/* If all lessons completed, show message here */}
                {isLessonCompleted && !nextLessonInfo && (
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg shadow-md text-center text-blue-700 dark:text-blue-300 mt-2 md:mt-0">
                    ¡Has completado todas las lecciones de este curso!
                    <Button variant="secondary" className="ml-3"
                      onClick={() => navigate({ to: `/courses/${course?.id || lesson?.module?.course_id || ''}` })}>
                      Volver al Curso
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={300} easing="ease-out" initialOpacity={0} delay={100}>
        <div
          className="grid grid-cols-1 md:grid-cols-2 mx-6 gap-6 custom-scroll"
          style={{ height: "calc(100vh - 300px)" }} // Remove overflowY here
        >
          {/* Lesson/Exercise Content Column */}
          <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-5 flex flex-col overflow-y-auto custom-scroll flex-1"
               style={{ maxHeight: "calc(100vh - 300px)" }}>
            <h2 className="font-bold text-lg text-secondary mb-2">
              {isExamMode
                ? examExercise?.title || "Examen Final"
                : lesson?.title}
            </h2>
            <hr className="mb-4 border-primary/40" />
            <div className="prose prose-invert max-w-none text-justify flex-grow">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {isExamMode
                  ? examExercise?.instructions || ""
                  : lesson?.content || ""}
              </ReactMarkdown>
            </div>
            {currentExercise && (
              <div className="mt-6 pt-4 border-t border-primary-opaque/20">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold text-xl text-secondary mb-1">
                    {currentExercise.title}
                  </h3>
                  {isCurrentExerciseCorrect && (
                    <div className="flex items-center text-green-400 text-sm">
                      <CheckCircle className="h-4 w-4 mr-1" /> Completado
                    </div>
                  )}
                </div>
                <div className="prose prose-invert max-w-none text-gray-300 mb-3">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {currentExercise.description || ""}
                  </ReactMarkdown>
                </div>
                {currentExercise.instructions && (
                  <div className="mt-3 pt-3 border-t border-primary-opaque/10">
                    <h4 className="font-semibold text-md text-secondary mb-2 flex items-center">
                      <BookText size={18} className="mr-2 text-primary" />
                      Instrucciones del Ejercicio:
                    </h4>
                    <div className="prose prose-sm prose-invert max-w-none text-gray-300">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {currentExercise.instructions}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          {/* Code Editor/Output Column */}
          <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-3 flex flex-col flex-1 overflow-y-auto custom-scroll"
               style={{ maxHeight: "calc(100vh - 300px)" }}>
            {currentExercise ? (
              <>
                <LessonCodeExecutor
                  key={currentExercise.id}
                  initialCode={currentExercise.starter_code || ""}
                  exerciseId={currentExercise.id}
                  onSubmitCode={handleCodeSubmit}
                  isSubmitting={submittingExerciseId === currentExercise.id}
                  isCorrect={isCurrentExerciseCorrect}
                  currentUserStdin={userStdin}
                />
                {exerciseNeedsInput && (
                  <div className="mt-2"> {/* Changed from mt-4 to mt-2 for less space */}
                    <label htmlFor="user-stdin" className="block text-sm font-medium text-gray-300 mb-1">
                      Entrada estándar (para <code>input()</code>):
                    </label>
                    <Textarea
                      id="user-stdin"
                      value={userStdin}
                      onChange={(e) => setUserStdin(e.target.value)}
                      placeholder="Escribe aquí la entrada que tu código leerá con input()..."
                      className="bg-primary-opaque/70 border-primary-opaque/30 text-sm"
                      rows={3}
                    />
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <BookOpen size={48} className="mb-4" />
                <p>
                  {isExamMode
                    ? "No se encontró el ejercicio de examen para este curso."
                    : "Esta lección no tiene un ejercicio interactivo."}
                </p>
              </div>
            )}
          </div>
        </div>
        <div className="mx-6 my-8 flex justify-between items-center">
          <Button variant="outline" onClick={() => navigate({ to: `/modules/${lesson?.module_id}` })}>
              Volver al Módulo
          </Button>
        </div>

            {/* Floating Chat Button */}
            {!chatDrawerOpen && (
              <button
                className="fixed bottom-6 right-6 z-[10000] bg-primary-700 text-white rounded-full px-5 py-3 shadow-lg hover:bg-primary-800 transition"
                onClick={() => setChatDrawerOpen(true)}
                aria-label="Abrir chat"
                style={{ fontWeight: "bold", fontSize: "1.1rem" }}
              >
                💬 Chat IA
              </button>
            )}

            {chatDrawerOpen && (
              <LessonChatDrawer
                open={chatDrawerOpen}
                onOpenChange={setChatDrawerOpen}
                lessonContent={lesson?.content}
                exercisePrompt={currentExercise?.description}
              />
            )}
        </FadeContent>


    </DashboardLayout>
  );
}
