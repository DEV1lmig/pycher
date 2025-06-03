import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "@tanstack/react-router"; // Added useNavigate
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { getModuleById, getCourseById } from "@/services/contentService"; // getLessonById and getExercisesByLessonId will come from the hook
import LessonCodeExecutor from "@/components/editor/LessonCodeExecutor";
import { LessonWithCodeRoute } from "@/router";
import Waves from "@/components/ui/waves";
import AnimatedContent from "@/components/ui/animated-content";
import FadeContent from "@/components/ui/fade-content";
import Breadcrumbs from "@/components/ui/breadcrumbs";
import { Home, BookOpen, ArrowRight, CheckCircle, Loader2, AlertCircle, BookText, ArrowRightCircle } from "lucide-react"; // Added ArrowRightCircle
import LessonChatbot from "@/components/ai/LessonChatBot";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useLessonDetail } from '@/hooks/useLessonDetail'; // Import the hook
import { Button } from "@/components/ui/button"; // Import Button
import { Textarea } from "@/components/ui/textarea";
import { toast } from "react-hot-toast";

export default function LessonWithCodePage() {
  const { lessonId: lessonIdParam } = useParams({ from: LessonWithCodeRoute.id });
  const lessonId = parseInt(lessonIdParam);
  const navigate = useNavigate();

  const {
    lesson,
    exercises,
    isLessonCompleted,
    getExerciseProgress,
    loading: lessonDetailLoading,
    error: lessonDetailError,
    submittingExerciseId,
    submitExercise: submitExerciseFromHook,
    nextLessonInfo, // Added nextLessonInfo from the hook
  } = useLessonDetail(lessonId);


  const [module, setModule] = useState(null);
  const [course, setCourse] = useState(null);
  const [breadcrumbLoading, setBreadcrumbLoading] = useState(true);
  const [userStdin, setUserStdin] = useState(""); // This state holds the textarea input

  // Determine the current exercise (assuming one main exercise per page for now)
  const currentExercise = exercises && exercises.length > 0 ? exercises[0] : null;
  const currentExerciseProgress = currentExercise ? getExerciseProgress(currentExercise.id) : null;
  const isCurrentExerciseCorrect = currentExerciseProgress?.is_correct || false;

  // Helper: does this exercise require input?
  const exerciseNeedsInput = !!(
    currentExercise &&
    currentExercise.validation_rules &&
    currentExercise.validation_rules.requires_input_function
  );

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
          // Optionally set an error state for breadcrumbs
        })
        .finally(() => setBreadcrumbLoading(false));
    } else if (lesson) { // Lesson loaded but no module_id
      setBreadcrumbLoading(false);
    }
  }, [lesson]);

  const handleCodeSubmit = async (codeToSubmit) => { // Renamed param for clarity
    if (!currentExercise) {
      toast.error("No hay ejercicio seleccionado para enviar.");
      return;
    }
    try {
      // Pass userStdin to the submission hook
      const submissionResult = await submitExerciseFromHook(currentExercise.id, codeToSubmit, userStdin);
      // The hook should handle success/error toasts and state updates
      return submissionResult;
    } catch (error) {
      // Error toast is likely handled by the hook
      console.error("Failed to submit exercise from page:", error);
      // Optionally, re-throw or handle further if needed
    }
  };

  if (lessonDetailLoading || (lesson && breadcrumbLoading)) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center min-h-[40vh] text-lg text-white">
          <Loader2 className="h-8 w-8 animate-spin mr-3" />
          Cargando lección...
        </div>
      </DashboardLayout>
    );
  }

  if (lessonDetailError) {
    return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-red-400">
          <AlertCircle className="h-12 w-12 mb-4" />
          {lessonDetailError}
        </div>
      </DashboardLayout>
    );
  }

  if (!lesson) {
     return (
      <DashboardLayout>
        <div className="flex flex-col justify-center items-center min-h-[40vh] text-lg text-gray-400">
            <AlertCircle className="h-12 w-12 mb-4" />
            Lección no encontrada o no se pudo cargar.
        </div>
      </DashboardLayout>
    );
  }

  // Determine if the next lesson is in a different module
  const isNextLessonInNewModule = nextLessonInfo && lesson && nextLessonInfo.module_id !== lesson.module_id;

  // ADD THIS CONSOLE LOG
  console.log('LessonWithCodePage State Check:', {
    lessonId,
    isLessonCompleted,
    nextLessonInfo,
    currentLessonModuleId: lesson?.module_id,
    isNextLessonInNewModule,
    lessonTitle: lesson?.title
  });

  return (
    <DashboardLayout>
      <div className="my-4 mx-6">
        <Breadcrumbs
          items={[
            { label: "Inicio", href: "/home", icon: <Home size={16} /> },
            { label: "Cursos", href: "/courses", icon: <BookOpen size={16} /> },
            course && { label: course.title, href: `/courses/${course.id}` },
            module && { label: module.title, href: `/courses/${course?.id}/modules/${module.id}` }, // Updated module link
            lesson && { label: lesson.title },
          ].filter(Boolean)}
        />
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
            <div className="flex justify-between items-start">
                <h1 className="text-3xl font-bold text-white mb-2">{lesson?.title}</h1>
                {isLessonCompleted && (
                    <div className="flex items-center text-green-400 bg-green-900/50 px-3 py-1 rounded-md">
                        <CheckCircle className="h-5 w-5 mr-2" />
                        <span>Lección Completada</span>
                    </div>
                )}
            </div>
            <div className="text-gray-400 mb-4 prose prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{lesson?.description || ""}</ReactMarkdown>
            </div>
          </div>
        </div>
      </AnimatedContent>

      <FadeContent blur={true} duration={300} easing="ease-out" initialOpacity={0} delay={100} >
      <div
        className="grid grid-cols-1 md:grid-cols-2 mx-6 gap-6 custom-scroll"
        style={{ maxHeight: "calc(100vh - 300px)", overflowY: "auto" }} // Adjusted maxHeight
      >
        <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-5 flex flex-col overflow-y-auto custom-scroll">
          <h2 className="font-bold text-lg text-secondary mb-2">{lesson?.title}</h2>
          <hr className="mb-4 border-primary/40" />
          <div className="prose prose-invert max-w-none text-justify flex-grow"> {/* Added flex-grow */}
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{lesson?.content || ""}</ReactMarkdown>
          </div>
          {currentExercise && (
            <div className="mt-6 pt-4 border-t border-primary-opaque/20">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-xl text-secondary mb-1">{currentExercise.title}</h3>
                {isCurrentExerciseCorrect && (
                  <div className="flex items-center text-green-400 text-sm">
                    <CheckCircle className="h-4 w-4 mr-1" /> Completado
                  </div>
                )}
              </div>
              <div className="prose prose-invert max-w-none text-gray-300 mb-3">
                 <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentExercise.description || ""}</ReactMarkdown>
              </div>
              {/* Display Exercise Instructions */}
              {currentExercise.instructions && (
                <div className="mt-3 pt-3 border-t border-primary-opaque/10">
                  <h4 className="font-semibold text-md text-secondary mb-2 flex items-center">
                    <BookText size={18} className="mr-2 text-primary" />
                    Instrucciones del Ejercicio:
                  </h4>
                  <div className="prose prose-sm prose-invert max-w-none text-gray-300">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentExercise.instructions}</ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        <div className="bg-primary-opaque/10 border border-primary-opaque/0 rounded-lg shadow px-6 p-3 flex flex-col gap-4">
          {currentExercise ? (
            <>
              <LessonCodeExecutor
                key={currentExercise.id}
                initialCode={currentExercise.starter_code || ""}
                exerciseId={currentExercise.id}
                onSubmitCode={handleCodeSubmit}
                isSubmitting={submittingExerciseId === currentExercise.id}
                isCorrect={isCurrentExerciseCorrect}
                currentUserStdin={userStdin} // <--- PASS userStdin AS A PROP
              />
              {exerciseNeedsInput && (
                <div className="mt-4">
                  <label htmlFor="user-stdin" className="block text-sm font-medium text-gray-300 mb-1">
                    Entrada estándar (para <code>input()</code>):
                  </label>
                  <Textarea
                    id="user-stdin"
                    value={userStdin}
                    onChange={(e) => setUserStdin(e.target.value)}
                    placeholder="Escribe aquí la entrada que tu código leerá con input()..."
                    className="bg-background/70 border-primary-opaque/30 text-sm"
                    rows={3}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <BookOpen size={48} className="mb-4" />
              <p>Esta lección no tiene un ejercicio interactivo.</p>
            </div>
          )}
        </div>
      </div>
      <div className="mx-6 my-8 flex justify-between items-center">
        <Button variant="outline" onClick={() => navigate({ to: `/courses/${course?.id}/modules/${lesson?.module_id}` })}>
            Volver al Módulo
        </Button>
      </div>

      {/* "Next Lesson" Button Area - This is the preferred and corrected structure */}
      {isLessonCompleted && nextLessonInfo && (
        <div className="mt-8 p-6 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg shadow-md text-center mx-6">
          <h3 className="text-xl font-semibold text-green-700 dark:text-green-300 mb-3">
            ¡Felicidades! Has completado esta lección.
          </h3>
          <Button
            onClick={() => {
              if (nextLessonInfo && nextLessonInfo.id) { // Use nextLessonInfo.id
                navigate({ to: `/lessons/$lessonId`, params: { lessonId: nextLessonInfo.id.toString() } });
              } else {
                console.warn("Next lesson ID is missing, cannot navigate.", nextLessonInfo);
                toast.error("No se pudo determinar la siguiente lección.");
              }
            }}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg text-lg"
            size="lg"
          >
            <ArrowRightCircle className="mr-2 h-5 w-5" />
            Siguiente Lección: {nextLessonInfo.title || "Siguiente"} {/* Use nextLessonInfo.title */}
          </Button>
          {isNextLessonInNewModule && nextLessonInfo.module_title && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              (Continuarás en el módulo: <span className="font-semibold">{nextLessonInfo.module_title}</span>) {/* Use nextLessonInfo.module_title */}
            </p>
          )}
        </div>
      )}
      {isLessonCompleted && !nextLessonInfo && (
        <div className="mt-8 p-6 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg shadow-md text-center mx-6">
          <h3 className="text-xl font-semibold text-blue-700 dark:text-blue-300">
            ¡Has completado todas las lecciones de este curso!
          </h3>
          <Button variant="secondary" onClick={() => navigate({ to: `/courses/${course?.id || lesson?.module?.course_id || ''}` })}>
            Volver al Curso
          </Button>
        </div>
      )}
      {!isLessonCompleted && ( // If lesson is NOT completed
          <div className="mx-6 my-8 flex justify-end items-center">
            {/* This div is to align the button to the right, matching the "Volver al Modulo" button's container */}
            <Button
                disabled={true}
                variant="default" // Or a more subdued variant
                title="Completa la lección actual para continuar"
            >
                Completa la lección para continuar
                {/* Optionally, you could show an arrow if nextLessonInfo is available but lesson not complete,
                    but it might be confusing. Keeping it simple for now. */}
            </Button>
          </div>
      )}

      <LessonChatbot lessonId={lessonId} lessonContent={lesson?.content} exercisePrompt={currentExercise?.description} />
      </FadeContent>
    </DashboardLayout>
  );
}
